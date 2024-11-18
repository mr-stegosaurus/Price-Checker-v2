from coinbase.rest import Client
from typing import Dict, Optional
from dotenv import load_dotenv
import os

# Load environment variables
load_dotenv()

# Get API credentials from environment variables
API_KEY = os.getenv('COINBASE_API_KEY')
API_SECRET = os.getenv('COINBASE_API_SECRET')

def get_coinbase_prices() -> Optional[Dict]:
    """
    Get ETH-USDC prices from Coinbase Advanced Trade
    """
    try:
        # Initialize client
        client = Client(API_KEY, API_SECRET)
        
        # Get ticker data for ETH-USDC
        ticker = client.get_product_ticker('ETH-USDC')
        
        # Structure the response similar to other DEX responses
        prices = {
            'name': 'Coinbase',
            'eth_buy': float(ticker['ask']),  # Price to buy ETH
            'eth_sell': float(ticker['bid']),  # Price to sell ETH
            'pool_address': 'coinbase'  # Using 'coinbase' as identifier
        }
        
        return prices
        
    except Exception as e:
        print(f"Error fetching Coinbase prices: {str(e)}")
        return None

if __name__ == "__main__":
    # Test the function
    prices = get_coinbase_prices()
    if prices:
        print(f"ETH Buy Price: {prices['eth_buy']:.2f} USDC")
        print(f"ETH Sell Price: {prices['eth_sell']:.2f} USDC")