from typing import List, Dict, Optional, Tuple
from concurrent.futures import ThreadPoolExecutor, TimeoutError
from web3 import Web3
import time
import asyncio

class QuoteService:
    def __init__(self, w3: Web3, rate_provider_contract, max_retries: int = 3):
        self.w3 = w3
        self.rate_provider = rate_provider_contract
        self.max_retries = max_retries
        self.max_workers = 20  # Maximum parallel requests
        self.timeout = 2.0     # Seconds to wait for each quote
        
    async def get_quotes(self, token_in: str, token_out: str, amount: int) -> List:
        """Get quotes with retry logic"""
        for attempt in range(self.max_retries):
            try:
                quotes = self.rate_provider.functions.get_quotes(
                    token_in,
                    token_out,
                    amount
                ).call()
                if quotes:  # Only return if we got valid quotes
                    return quotes
                print(f"No quotes found for {token_in} -> {token_out}")
                return []  # Return empty list if no quotes found
            except Exception as e:
                print(f"Failed to get quote (attempt {attempt + 1}): {str(e)}")
                if attempt < self.max_retries - 1:  # Only sleep if we're going to retry
                    await asyncio.sleep(0.5 * (attempt + 1))
        return []  # Return empty list after all retries failed
    
    async def get_quotes_parallel(self, quote_params: List[Tuple[str, str, int]]) -> List[Dict]:
        """Get multiple quotes in parallel"""
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            futures = []
            for token_in, token_out, amount in quote_params:
                futures.append(
                    executor.submit(
                        self.rate_provider.functions.get_quotes(
                            token_in,
                            token_out,
                            amount
                        ).call
                    )
                )
            
            results = []
            for future in futures:
                try:
                    result = future.result(timeout=self.timeout)
                    if result:
                        results.append(result)
                except TimeoutError:
                    print(f"Quote timed out after {self.timeout} seconds")
                except Exception as e:
                    print(f"Quote failed: {str(e)}")
            
            return results
    
    def get_best_quote(self, quotes: List[Dict]) -> Optional[Dict]:
        """Get the best quote from a list of quotes"""
        if not quotes:
            return None
        print("First quote structure:", quotes[0])  # Debug print to see tuple structure
        print("All quotes:", quotes)                # See all quotes
        return max(quotes, key=lambda x: x[3])