from web3 import Web3
from typing import Dict, List, Tuple, Set
from dotenv import load_dotenv
import os
from itertools import permutations

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
        self.registry_address = self.address_provider.functions.get_address(0).call()
        self.registry = self.w3.eth.contract(
            address=Web3.to_checksum_address(self.registry_address),
            abi=self._get_registry_abi()
        )
        
        # Initialize rate provider
        self.rate_provider_address = self.address_provider.functions.get_address(7).call()
        self.rate_provider = self.w3.eth.contract(
            address=Web3.to_checksum_address(self.rate_provider_address),
            abi=self._get_rate_provider_abi()
        )
        
        # Cache for pools and tokens
        self.pool_tokens: Dict[str, Set[str]] = {}  # pool -> tokens
        self.token_pools: Dict[str, Set[str]] = {}  # token -> pools
        self.all_tokens: Set[str] = set()
        
        # Build initial cache
        self._build_pool_cache()
        
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

    def _build_pool_cache(self):
        """Build cache of all pools and their tokens"""
        try:
            pool_count = self.registry.functions.pool_count().call()
            print(f"\n=== Registry Scan ===")
            print(f"Found {pool_count} pools in registry")

            for i in range(pool_count):
                try:
                    pool_address = self.registry.functions.pool_list(i).call()
                    pool_address = Web3.to_checksum_address(pool_address)
                    print(f"\nProcessing pool {i+1}/{pool_count}: {pool_address}")
                    
                    # Get both regular and underlying coins
                    coins = self.registry.functions.get_coins(pool_address).call()
                    underlying = self.registry.functions.get_underlying_coins(pool_address).call()
                    
                    # Filter out null addresses and combine coins
                    pool_tokens = set()
                    print("Tokens found in pool:")
                    for coin in coins + underlying:
                        if coin and coin != "0x0000000000000000000000000000000000000000":
                            coin = Web3.to_checksum_address(coin)
                            pool_tokens.add(coin)
                            print(f"  - {coin}")
                            
                            # Update token -> pools mapping
                            if coin not in self.token_pools:
                                self.token_pools[coin] = set()
                            self.token_pools[coin].add(pool_address)
                    
                    # Update pool -> tokens mapping
                    self.pool_tokens[pool_address] = pool_tokens
                    
                    # Update all_tokens set
                    self.all_tokens.update(pool_tokens)
                    
                except Exception as e:
                    print(f"Error processing pool {i}: {str(e)}")
                    continue
                
            print(f"\n=== Cache Summary ===")
            print(f"Cached {len(self.all_tokens)} unique tokens across {len(self.pool_tokens)} pools")
            
        except Exception as e:
            print(f"Error building pool cache: {str(e)}")

    def _get_possible_intermediate_tokens(self, token_in: str, token_out: str) -> Set[str]:
        """Get all tokens that could serve as intermediaries"""
        print(f"\n=== Finding Intermediate Tokens ===")
        print(f"Input Token: {token_in}")
        print(f"Output Token: {token_out}")
        
        # Get pools that contain token_in
        pools_with_input = self.token_pools.get(token_in, set())
        print(f"Found {len(pools_with_input)} pools containing input token")
        
        # Get all tokens from these pools
        possible_intermediates = set()
        for pool in pools_with_input:
            possible_intermediates.update(self.pool_tokens[pool])
        
        print(f"Initial possible intermediates: {len(possible_intermediates)}")
        
        # Remove input and output tokens
        possible_intermediates -= {token_in, token_out}
        
        # Filter to only tokens that can also reach the output token
        valid_intermediates = {token for token in possible_intermediates 
                             if self.token_pools.get(token, set()) & self.token_pools.get(token_out, set())}
        
        print(f"Final valid intermediates: {len(valid_intermediates)}")
        print("Valid intermediate tokens:")
        for token in valid_intermediates:
            print(f"  - {token}")
            
        return valid_intermediates

    def _get_single_hop_quote(self, token_in: str, token_out: str, amount_in: int) -> List[tuple]:
        """Get quotes for a single hop"""
        try:
            print(f"\nGetting quote for {token_in} -> {token_out}")
            quotes = self.rate_provider.functions.get_quotes(token_in, token_out, amount_in).call()
            print(f"Found {len(quotes)} quotes")
            for quote in quotes:
                print(f"  Pool: {quote[4]}")
                print(f"  Amount Out: {quote[3]}")
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

    def _simulate_route(self, route: List[str], amount_in: int) -> Dict:
        """Simulate a multi-hop route and return the result"""
        current_amount = amount_in
        hops = []
        
        for i in range(len(route) - 1):
            token_in, token_out = route[i], route[i + 1]
            quotes = self._get_single_hop_quote(token_in, token_out, current_amount)
            
            if not quotes:
                return None
                
            best_quote = max(quotes, key=lambda x: x[3])
            current_amount = best_quote[3]
            
            hops.append({
                "token_in": token_in,
                "token_out": token_out,
                "amount_in": current_amount,
                "amount_out": best_quote[3],
                "pool": best_quote[4]
            })
            
        return {
            "protocol": "Curve",
            "path": route,
            "hops": hops,
            "input_amount": amount_in,
            "output_amount": current_amount
        }

    def find_best_route(self, token_in: str, token_out: str, amount_in: int) -> Dict:
        """Find the best route between two tokens using up to 3 hops"""
        token_in = Web3.to_checksum_address(token_in)
        token_out = Web3.to_checksum_address(token_out)
        
        # Find all possible routes
        possible_routes = self._find_routes(token_in, token_out)
        print(f"Found {len(possible_routes)} possible routes")
        
        # Simulate each route
        valid_routes = []
        for route in possible_routes:
            result = self._simulate_route(route, amount_in)
            if result:
                valid_routes.append(result)
        
        if not valid_routes:
            return None
            
        # Find best route by output amount
        best_route = max(valid_routes, key=lambda x: x['output_amount'])
        
        return {
            "best_route": best_route,
            "all_routes": valid_routes
        }

def main():
    router = CurveRouter()
    
    # Example tokens
    USDC = "0xFF970A61A04b1cA14834A43f5dE4533eBDDB5CC8"
    USDT = "0xFd086bC7CD5C481DCC9C85ebE478A1C0b69FCbb9"
    
    # Amount in (1000 USDC)
    amount_in = 1000 * 10**6
    
    result = router.find_best_route(USDC, USDT, amount_in)
    
    if result:
        best_route = result['best_route']
        print("\nBest Route Found:")
        print(f"Path: {' -> '.join(best_route['path'])}")
        print(f"Input Amount: {amount_in / 10**6} USDC")
        print(f"Output Amount: {best_route['output_amount'] / 10**6} USDT")
        
        print("\nHop Details:")
        for hop in best_route['hops']:
            print(f"Pool: {hop['pool']}")
            print(f"Amount In: {hop['amount_in'] / 10**6}")
            print(f"Amount Out: {hop['amount_out'] / 10**6}")
            print("---")
        
        print("\nAll Routes Found:", len(result['all_routes']))

if __name__ == "__main__":
    main() 