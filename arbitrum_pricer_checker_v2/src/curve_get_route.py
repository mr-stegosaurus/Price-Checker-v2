from web3 import Web3
from typing import Dict, List, Tuple, Set
from dotenv import load_dotenv
import os
from itertools import permutations
from concurrent.futures import ThreadPoolExecutor
import asyncio
from services.cache_service import CurvePoolCache
from services.route_finder import RouteFinder
import time

# Load environment variables
load_dotenv()

class CurveRouter:
    def __init__(self):
        # Initialize Web3
        self.w3 = Web3(Web3.HTTPProvider(os.getenv('ARB_ALCHEMY_API_URL')))
        
        # Initialize address provider
        self.address_provider = self.w3.eth.contract(
            address=Web3.to_checksum_address("0x5ffe7FB82894076ECB99A30D6A32e969e6e35E98"),
            abi=self._get_address_provider_abi()
        )
        
        # Initialize registry
        self.registry_address = self.address_provider.functions.get_address(7).call()
        self.registry = self.w3.eth.contract(
            address=Web3.to_checksum_address(self.registry_address),
            abi=self._get_registry_abi()
        )
        
        # Initialize rate provider
        self.rate_provider_address = self.address_provider.functions.get_address(18).call()
        print(f"\nRate Provider Address: {self.rate_provider_address}")
        self.rate_provider = self.w3.eth.contract(
            address=Web3.to_checksum_address(self.rate_provider_address),
            abi=self._get_rate_provider_abi()
        )
        
        # Initialize cache service
        self.cache = CurvePoolCache(self.w3, self.registry)
        
        # Initialize route finder
        self.route_finder = RouteFinder(self.cache)
        
    def _get_address_provider_abi(self) -> List:
        return [{
            "name": "get_address",
            "outputs": [{"type": "address"}],
            "inputs": [{"type": "uint256"}],
            "stateMutability": "view",
            "type": "function"
        }]

    def _get_registry_abi(self) -> List:
        return [{
            "name": "pool_count",
            "outputs": [{"type": "uint256"}],
            "inputs": [],
            "stateMutability": "view",
            "type": "function"
        },
        {
            "name": "pool_list",
            "outputs": [{"type": "address"}],
            "inputs": [{"type": "uint256"}],
            "stateMutability": "view",
            "type": "function"
        },
        {
            "name": "get_coins",
            "outputs": [{"type": "address[8]"}],
            "inputs": [{"type": "address"}],
            "stateMutability": "view",
            "type": "function"
        },
        {
            "name": "get_underlying_coins",
            "outputs": [{"type": "address[8]"}],
            "inputs": [{"type": "address"}],
            "stateMutability": "view",
            "type": "function"
        }]

    def _get_rate_provider_abi(self) -> List:
        return [{
            "name": "find_pools_for_coins",
            "outputs": [{"type": "address[]", "name": ""}],
            "inputs": [
                {"type": "address", "name": "_from"},
                {"type": "address", "name": "_to"}
            ],
            "stateMutability": "view",
            "type": "function"
        },
        {
            "name": "get_quotes",
            "outputs": [{"type": "tuple[]", "components": [
                {"type": "uint256", "name": "source_token_index"},
                {"type": "uint256", "name": "dest_token_index"},
                {"type": "bool", "name": "is_underlying"},
                {"type": "uint256", "name": "amount_out"},
                {"type": "address", "name": "pool"},
                {"type": "uint256", "name": "source_token_pool_balance"},
                {"type": "uint256", "name": "dest_token_pool_balance"},
                {"type": "uint256", "name": "pool_type"}
            ]}],
            "inputs": [
                {"type": "address", "name": "_from"},
                {"type": "address", "name": "_to"},
                {"type": "uint256", "name": "_amount"}
            ],
            "stateMutability": "view",
            "type": "function"
        }]

    def _get_possible_intermediate_tokens(self, token_in: str, token_out: str) -> Set[str]:
        """Get all tokens that could serve as intermediaries"""
        pools_with_input = self.cache.token_pools.get(token_in, set())
        pools_with_output = self.cache.token_pools.get(token_out, set())
        
        # For intermediate routes
        possible_intermediates = set()
        # Check tokens in pools that have input token
        for pool in pools_with_input:
            possible_intermediates.update(self.cache.pool_tokens[pool])
        # Check tokens in pools that have output token
        for pool in pools_with_output:
            possible_intermediates.update(self.cache.pool_tokens[pool])
        
        # Remove input/output tokens
        possible_intermediates -= {token_in, token_out}
        
        print(f"\nFound {len(possible_intermediates)} possible intermediate tokens")
        return possible_intermediates

    def _get_single_hop_quote(self, token_in: str, token_out: str, amount_in: int) -> List[tuple]:
        """Get quotes for a single hop"""
        try:
            quotes = self.rate_provider.functions.get_quotes(token_in, token_out, amount_in).call()
            if quotes:  # Only print if quotes found
                print(f"\nFound {len(quotes)} quotes for {token_in[:8]}...{token_out[-8:]}")
            return quotes
        except Exception as e:
            print(f"Error getting quote: {str(e)}")
            return []

    def _find_routes(self, token_in: str, token_out: str, max_hops: int = 3) -> List[List[str]]:
        """Find all possible routes up to max_hops"""
        routes = []
        
        # Direct routes (1 hop)
        if self._get_single_hop_quote(token_in, token_out, 1):  # Use small amount to test
            routes.append([token_in, token_out])
        
        # 2 hop routes
        if max_hops >= 2:
            intermediates = self._get_possible_intermediate_tokens(token_in, token_out)
            for mid in intermediates:
                if (self._get_single_hop_quote(token_in, mid, 1) and 
                    self._get_single_hop_quote(mid, token_out, 1)):
                    routes.append([token_in, mid, token_out])
        
        # 3 hop routes
        if max_hops >= 3:
            intermediates = list(self._get_possible_intermediate_tokens(token_in, token_out))
            for mid1, mid2 in permutations(intermediates, 2):
                if (self._get_single_hop_quote(token_in, mid1, 1) and 
                    self._get_single_hop_quote(mid1, mid2, 1) and 
                    self._get_single_hop_quote(mid2, token_out, 1)):
                    routes.append([token_in, mid1, mid2, token_out])
        
        return routes

    async def _simulate_route(self, route: List[str], amount_in: int) -> Dict:
        """Simulate a multi-hop route"""
        current_amount = amount_in
        hops = []
        
        print(f"\nSimulating route: {' -> '.join(route)}")
        
        # Process each hop sequentially
        for i in range(len(route) - 1):
            token_in, token_out = route[i], route[i + 1]
            
            # Get decimals for better logging
            in_decimals = self._get_token_decimals(token_in)
            out_decimals = self._get_token_decimals(token_out)
            
            print(f"\nHop {i+1}: {token_in} -> {token_out}")
            print(f"Input amount: {current_amount / 10**in_decimals} ({current_amount} raw)")
            
            quotes = self._get_single_hop_quote(token_in, token_out, current_amount)
            
            if not quotes:
                print(f"No quotes found for hop {i+1}")
                return None
            
            best_quote = max(quotes, key=lambda x: x[3])  # x[3] is amount_out
            if not best_quote:
                print(f"No valid quote found for hop {i+1}")
                return None
            
            current_amount = best_quote[3]  # Update amount for next hop
            print(f"Output amount: {current_amount / 10**out_decimals} ({current_amount} raw)")
            
            hops.append({
                "token_in": route[i],
                "token_out": route[i + 1],
                "amount_in": amount_in if i == 0 else hops[i-1]["amount_out"],
                "amount_out": best_quote[3],
                "pool": best_quote[4]  # pool address is at index 4
            })
        
        return {
            "protocol": "Curve",
            "path": route,
            "hops": hops,
            "input_amount": amount_in,
            "output_amount": current_amount
        }

    async def find_best_route(self, token_in: str, token_out: str, amount_in: int):
        # Convert addresses to checksum format
        token_in = Web3.to_checksum_address(token_in)
        token_out = Web3.to_checksum_address(token_out)
        
        print(f"\nSearching for routes between {token_in} and {token_out}")
        possible_routes = self.route_finder.find_possible_routes(token_in, token_out)
        
        if not possible_routes:
            print("\nDebug: Route finding failed")
            print(f"Input token pools: {self.cache.token_pools.get(token_in, set())}")
            print(f"Output token pools: {self.cache.token_pools.get(token_out, set())}")
            print(f"Direct path possible: {self._get_single_hop_quote(token_in, token_out, 1)}")
            return None
        
        print(f"\nFound {len(possible_routes)} possible routes:")
        for route in possible_routes:
            print(f"Route: {' -> '.join(route.path)}")
        
        # Simulate each route to find the best one
        best_route = None
        best_amount = 0
        all_routes = []
        
        for route in possible_routes:
            print(f"Trying route: {' -> '.join(route.path)}")
            result = await self._simulate_route(route.path, amount_in)
            if result and result['output_amount'] > best_amount:
                best_route = result
                best_amount = result['output_amount']
            if result:
                all_routes.append(result)
        
        if not all_routes:
            print("No valid routes found")
            return None
        
        return {
            'best_route': best_route,
            'all_routes': all_routes
        }

    def _get_token_decimals(self, token_address: str) -> int:
        """Get token decimals from contract"""
        try:
            abi = [{"inputs":[],"name":"decimals","outputs":[{"internalType":"uint8","type":"uint8"}],"stateMutability":"view","type":"function"}]
            token_contract = self.w3.eth.contract(address=Web3.to_checksum_address(token_address), abi=abi)
            return token_contract.functions.decimals().call()
        except Exception as e:
            print(f"Error getting decimals for {token_address}: {e}")
            return 18  # Default to 18 if unable to get decimals

async def main():
    router = CurveRouter()
    
    # Example tokens
    token_in = "0x912CE59144191C1204E64559FE8253a0e49E6548"  # arb
    token_out = "0xFF970A61A04b1cA14834A43f5dE4533eBDDB5CC8"  # usdc.e
    
    # Get decimals for both tokens
    in_decimals = router._get_token_decimals(token_in)
    out_decimals = router._get_token_decimals(token_out)
    
    print(f"Input token decimals: {in_decimals}")
    print(f"Output token decimals: {out_decimals}")
    
    # Amount in (44.906 token_in)
    amount_in = int(44.906 * 10**in_decimals)  # Convert to integer explicitly
    
    result = await router.find_best_route(token_in, token_out, amount_in)
    
    if result:
        best_route = result['best_route']
        print("\nBest Route Found:")
        print(f"Path: {' -> '.join(best_route['path'])}")
        print(f"Input Amount: {amount_in / 10**in_decimals} {token_in}")
        print(f"Output Amount: {best_route['output_amount'] / 10**out_decimals} {token_out}")
        
        print("\nHop Details:")
        for hop in best_route['hops']:
            # Get decimals for each hop
            hop_in_decimals = router._get_token_decimals(hop['token_in'])
            hop_out_decimals = router._get_token_decimals(hop['token_out'])
            
            print(f"Pool: {hop['pool']}")
            print(f"Amount In: {hop['amount_in'] / 10**hop_in_decimals}")
            print(f"Amount Out: {hop['amount_out'] / 10**hop_out_decimals}")
            print("---")
        
        print("\nAll Routes Found:", len(result['all_routes']))

if __name__ == "__main__":
    asyncio.run(main()) 