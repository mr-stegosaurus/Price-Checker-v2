import pickle
import os
from pathlib import Path
from gmx_python_sdk.scripts.v2.gmx_utils import ConfigManager
from gmx_python_sdk.example_scripts.estimate_swap_output import EstimateSwapOutput
import time

class GMXRouter:
    CACHE_DIR = Path("cache")
    CACHE_FILE = CACHE_DIR / "gmx_cache.pkl"
    
    def __init__(self):
        self.estimator = None
        self.config = None
        self.token_address_cache = {}
        
        if self.load_cache():
            print("Loaded initialized GMX Router from cache")
        else:
            print("Starting GMX Router initialization...")
            start = time.time()
            self.config = ConfigManager("arbitrum")
            self.config.set_config()
            self.initialize_estimator()
            print(f"Initialization took: {time.time() - start:.2f} seconds")
            self.save_cache()
    
    def initialize_estimator(self):
        """Initialize estimator once and cache it"""
        if not self.estimator:
            self.estimator = EstimateSwapOutput(config=self.config)

    def save_cache(self):
        """Save initialized data to cache"""
        try:
            self.CACHE_DIR.mkdir(exist_ok=True)
            with open(self.CACHE_FILE, 'wb') as f:
                pickle.dump({
                    'config': self.config,
                    'estimator': self.estimator,
                    'token_address_cache': self.token_address_cache,
                }, f)
            print("Cached initialization data")
        except Exception as e:
            print(f"Failed to cache data: {e}")

    def load_cache(self) -> bool:
        """Load initialized data from cache if available"""
        try:
            if self.CACHE_FILE.exists():
                with open(self.CACHE_FILE, 'rb') as f:
                    data = pickle.load(f)
                    self.config = data['config']
                    self.estimator = data['estimator']
                    self.token_address_cache = data.get('token_address_cache', {})
                return True
        except Exception as e:
            print(f"Failed to load cache: {e}")
            if self.CACHE_FILE.exists():
                self.CACHE_FILE.unlink()  # Delete corrupted cache
        return False

    def get_token_address(self, token_symbol: str) -> str:
        """Get token address with caching"""
        if token_symbol in self.token_address_cache:
            print(f"Using cached address for {token_symbol}")
            return self.token_address_cache[token_symbol]
            
        print(f"Finding address for {token_symbol}")
        tokens = self.estimator.tokens
        # If not in cache, do the lookup
        for key, value in tokens.items():
            if value.get('symbol') == token_symbol:
                self.token_address_cache[token_symbol] = key
                self.save_cache()
                return key
        raise Exception(f'"{token_symbol}" not a known token for GMX v2!')

    def get_swap_quote(self, token_in: str, token_out: str, amount_in: float) -> dict:
        print(f"\nGetting quote for {amount_in} {token_in} -> {token_out}")
        total_start = time.time()
        
        try:
            print("Starting quote process...")
            step_time = time.time()
            
            # Get cached token addresses
            in_token_address = self.get_token_address(token_in)
            out_token_address = self.get_token_address(token_out)
            
            output = self.estimator.get_swap_output(
                in_token_address=in_token_address,  # Use address instead of symbol
                out_token_address=out_token_address,  # Use address instead of symbol
                token_amount=int(amount_in)
            )
            
            print(f"\nSDK get_swap_output call took: {time.time() - step_time:.2f} seconds")
            print(f"Total quote process took: {time.time() - total_start:.2f} seconds")
            print(f"Output from GMX SDK: {output}")
            
            if output:
                print("\n=== Summary ===")
                print(f"Swapping {amount_in} {token_in}")
                print(f"Receiving {output.get('out_token_actual', 0)} {token_out}")
                print(f"Price Impact: {output.get('price_impact', 0)}%")
            
            return {
                "protocol": "GMX_V2",
                "token_in": token_in,
                "token_out": token_out,
                "amount_in": amount_in,
                "amount_out": output.get('out_token_actual', 0) if output else 0,
                "price_impact": output.get('price_impact', 0) if output else 0
            }

        except Exception as e:
            print(f"\nError getting quote: {str(e)}")
            print(f"Error type: {type(e)}")
            print(f"Error args: {e.args}")
            return None

def main():
    router = GMXRouter()
    
    # Use exact token symbols from the config
    quote = router.get_swap_quote("ETH", "USDC", 1.0)
    
    if quote:
        print("\n=== Summary ===")
        print(f"Swapping {quote['amount_in']} {quote['token_in']}")
        print(f"Receiving {quote['amount_out']} {quote['token_out']}")
        print(f"Price Impact: {quote['price_impact']}%")

if __name__ == "__main__":
    main()