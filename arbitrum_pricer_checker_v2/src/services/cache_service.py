from web3 import Web3
import json
import time
from typing import Dict, Set

class CurvePoolCache:
    def __init__(self, w3: Web3, registry_contract):
        self.w3 = w3
        self.registry = registry_contract
        self.cache_file = "curve_pool_cache.json"
        self.cache_expiry = 3600  # 1 hour in seconds
        
        # Cache structures
        self.pool_tokens: Dict[str, Set[str]] = {}  # pool -> tokens
        self.token_pools: Dict[str, Set[str]] = {}  # token -> pools
        self.all_tokens: Set[str] = set()
        self.last_update = 0
        
        # Load or build cache
        self.load_cache()
    
    def load_cache(self):
        """Load cache from file or build if expired/missing"""
        try:
            with open(self.cache_file, 'r') as f:
                data = json.load(f)
                if time.time() - data['timestamp'] < self.cache_expiry:
                    self.pool_tokens = {k: set(v) for k, v in data['pool_tokens'].items()}
                    self.token_pools = {k: set(v) for k, v in data['token_pools'].items()}
                    self.all_tokens = set(data['all_tokens'])
                    self.last_update = data['timestamp']
                    return
        except FileNotFoundError:
            pass
        
        self.build_cache()
    
    def build_cache(self):
        """Build cache from chain data"""
        print("Building pool cache...")
        
        # Get total number of pools
        pool_count = self.registry.functions.pool_count().call()
        print(f"Found {pool_count} pools")
        
        # Iterate through all pools
        for i in range(pool_count):
            try:
                # Get pool address
                pool_address = self.registry.functions.pool_list(i).call()
                pool_address = self.w3.to_checksum_address(pool_address)
                
                # Get coins (regular and underlying)
                coins = self.registry.functions.get_coins(pool_address).call()
                underlying_coins = self.registry.functions.get_underlying_coins(pool_address).call()
                
                # Filter out null addresses
                coins = [self.w3.to_checksum_address(coin) for coin in coins if coin != '0x0000000000000000000000000000000000000000']
                underlying_coins = [self.w3.to_checksum_address(coin) for coin in underlying_coins if coin != '0x0000000000000000000000000000000000000000']
                
                # Combine all tokens for this pool
                pool_tokens = set(coins + underlying_coins)
                
                # Update mappings
                self.pool_tokens[pool_address] = pool_tokens
                self.all_tokens.update(pool_tokens)
                
                # Update token -> pools mapping
                for token in pool_tokens:
                    if token not in self.token_pools:
                        self.token_pools[token] = set()
                    self.token_pools[token].add(pool_address)
                
                if i % 10 == 0:  # Progress update every 10 pools
                    print(f"Processed {i}/{pool_count} pools")
                    
            except Exception as e:
                print(f"Error processing pool {i}: {str(e)}")
                continue
        
        print(f"Cache built successfully. Found {len(self.all_tokens)} unique tokens across {len(self.pool_tokens)} pools.")
        self.save_cache()
    
    def save_cache(self):
        """Save cache to file"""
        cache_data = {
            'timestamp': time.time(),
            'pool_tokens': {k: list(v) for k, v in self.pool_tokens.items()},
            'token_pools': {k: list(v) for k, v in self.token_pools.items()},
            'all_tokens': list(self.all_tokens)
        }
        
        with open(self.cache_file, 'w') as f:
            json.dump(cache_data, f) 