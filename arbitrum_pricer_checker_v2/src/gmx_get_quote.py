from web3 import Web3
from typing import Dict
import requests
import os
from dotenv import load_dotenv

class GMXRouter:
    def __init__(self):
        load_dotenv()
        
        # Initialize Web3 connection (Arbitrum)
        self.w3 = Web3(Web3.HTTPProvider(os.getenv('ARB_ALCHEMY_API_URL')))
        
        # GMX API endpoints
        self.api_url = "https://api.gmx.io/api"
        
        # Common token addresses
        self.TOKENS = {
            "WETH": "0x82aF49447D8a07e3bd95BD0d56f35241523fBab1",
            "WBTC": "0x2f2a2543B76A4166549F7aaB2e75Bef0aefC5B0f",
            "USDC": "0xFF970A61A04b1cA14834A43f5dE4533eBDDB5CC8",
            "USDT": "0xFd086bC7CD5C481DCC9C85ebE478A1C0b69FCbb9",
            "DAI": "0xDA10009cBd5D07dd0CeCc66161FC93D7c9000da1",
            "GMX": "0xfc5A1A6EB076a2C7aD06eD22C90d7E710E35ad0a"
        }

    def get_token_decimals(self, token_address: str) -> int:
        """Get token decimals"""
        try:
            token_abi = [{"inputs":[],"name":"decimals","outputs":[{"internalType":"uint8","type":"uint8"}],"stateMutability":"view","type":"function"}]
            token_contract = self.w3.eth.contract(address=Web3.to_checksum_address(token_address), abi=token_abi)
            return token_contract.functions.decimals().call()
        except Exception as e:
            print(f"Error getting decimals: {str(e)}")
            return 18  # default to 18 decimals

    def get_swap_quote(self, token_in: str, token_out: str, amount_in: int) -> Dict:
        """
        Get swap quote from GMX
        token_in: token address or symbol
        token_out: token address or symbol
        amount_in: amount in token decimals
        """
        try:
            # Convert token symbols to addresses if needed
            token_in_address = self.TOKENS.get(token_in, token_in)
            token_out_address = self.TOKENS.get(token_out, token_out)
            
            # Ensure addresses are checksum
            token_in_address = Web3.to_checksum_address(token_in_address)
            token_out_address = Web3.to_checksum_address(token_out_address)
            
            # Get token decimals
            token_in_decimals = self.get_token_decimals(token_in_address)
            token_out_decimals = self.get_token_decimals(token_out_address)
            
            print(f"\n=== Getting GMX Quote ===")
            print(f"Token In: {token_in_address}")
            print(f"Token Out: {token_out_address}")
            print(f"Amount In: {amount_in / 10**token_in_decimals}")
            
            # Construct API endpoint
            endpoint = f"{self.api_url}/swap/quote"
            params = {
                "tokenIn": token_in_address,
                "tokenOut": token_out_address,
                "amountIn": str(amount_in),
                "isWrap": False
            }
            
            # Get quote from API
            response = requests.get(endpoint, params=params)
            if response.status_code != 200:
                raise Exception(f"API request failed: {response.text}")
            
            quote_data = response.json()
            
            # Format response
            result = {
                "protocol": "GMX",
                "token_in": token_in_address,
                "token_out": token_out_address,
                "amount_in": amount_in,
                "amount_out": int(quote_data.get("amountOut", 0)),
                "price_impact": quote_data.get("priceImpact", 0),
                "fees": quote_data.get("fees", 0)
            }
            
            print("\n=== Quote Results ===")
            print(f"Amount Out: {result['amount_out'] / 10**token_out_decimals}")
            print(f"Price Impact: {result['price_impact']}%")
            print(f"Fees: {result['fees']}")
            
            return result
            
        except Exception as e:
            print(f"Error getting quote: {str(e)}")
            return None

def main():
    router = GMXRouter()
    
    # Example: Swap 1 WETH for USDC
    amount_in = 1 * 10**18  # 1 WETH
    quote = router.get_swap_quote("WETH", "USDC", amount_in)
    
    if quote:
        print("\n=== Summary ===")
        print(f"Swapping {amount_in / 10**18} WETH")
        print(f"Receiving {quote['amount_out'] / 10**6} USDC")  # USDC has 6 decimals

if __name__ == "__main__":
    main()