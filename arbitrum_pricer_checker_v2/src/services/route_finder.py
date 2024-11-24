from typing import List, Set, Dict, Tuple
from dataclasses import dataclass
import json
import time

@dataclass
class Route:
    path: List[str]
    hops: int

class RouteFinder:
    def __init__(self, cache_service):
        self.cache = cache_service
        self.max_hops = 3
        self.route_cache: Dict[Tuple[str, str], List[Route]] = {}
        self.route_cache_file = "curve_route_cache.json"
        self.cache_expiry = 3600  # 1 hour
        self.load_route_cache()
    
    def find_possible_routes(self, token_in: str, token_out: str) -> List[Route]:
        """Find routes, using cache if available"""
        cache_key = (token_in, token_out)
        
        # Check cache first
        if cache_key in self.route_cache:
            return self.route_cache[cache_key]
        
        # Find routes if not cached
        routes = self._find_routes(token_in, token_out)
        
        # Cache the result
        self.route_cache[cache_key] = routes
        self.save_route_cache()
        
        return routes
    
    def _find_routes(self, token_in: str, token_out: str) -> List[Route]:
        """Find routes with maximum 2 hops"""
        routes = []
        
        # Direct routes (1 hop)
        if self._tokens_have_common_pool(token_in, token_out):
            routes.append(Route(
                path=[token_in, token_out],
                hops=1
            ))
        
        # 2 hop routes
        intermediates = self._get_possible_intermediate_tokens(token_in, token_out)
        for mid in intermediates:
            if (self._tokens_have_common_pool(token_in, mid) and 
                self._tokens_have_common_pool(mid, token_out)):
                routes.append(Route(
                    path=[token_in, mid, token_out],
                    hops=2
                ))
        
        return routes
    
    def _tokens_have_common_pool(self, token1: str, token2: str) -> bool:
        """Check if two tokens share any pools"""
        pools1 = self.cache.token_pools.get(token1, set())
        pools2 = self.cache.token_pools.get(token2, set())
        return bool(pools1 & pools2)  # intersection
    
    def _get_possible_intermediate_tokens(self, token_in: str, token_out: str) -> Set[str]:
        """Get all tokens that could serve as intermediaries"""
        pools_with_input = self.cache.token_pools.get(token_in, set())
        pools_with_output = self.cache.token_pools.get(token_out, set())
        
        possible_intermediates = set()
        for pool in pools_with_input:
            possible_intermediates.update(self.cache.pool_tokens[pool])
        for pool in pools_with_output:
            possible_intermediates.update(self.cache.pool_tokens[pool])
        
        # Remove input/output tokens
        possible_intermediates -= {token_in, token_out}
        
        return possible_intermediates
    
    def load_route_cache(self):
        """Load cached routes from file"""
        try:
            with open(self.route_cache_file, 'r') as f:
                data = json.load(f)
                if time.time() - data['timestamp'] < self.cache_expiry:
                    # Convert string tuples back to actual tuples for keys
                    self.route_cache = {
                        tuple(k.split('|')): [Route(**r) for r in routes]
                        for k, routes in data['routes'].items()
                    }
        except FileNotFoundError:
            self.route_cache = {}
    
    def save_route_cache(self):
        """Save routes to cache file"""
        cache_data = {
            'timestamp': time.time(),
            'routes': {
                f"{k[0]}|{k[1]}": [{'path': r.path, 'hops': r.hops} for r in routes]
                for k, routes in self.route_cache.items()
            }
        }
        with open(self.route_cache_file, 'w') as f:
            json.dump(cache_data, f)