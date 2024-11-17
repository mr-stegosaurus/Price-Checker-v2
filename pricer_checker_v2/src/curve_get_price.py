from web3 import Web3
from typing import Dict, Optional
from dotenv import load_dotenv
import os

# Load environment variables
load_dotenv()

# Get Alchemy API URL from environment variables
ALCHEMY_API_URL = os.getenv('ALCHEMY_API_URL')
w3 = Web3(Web3.HTTPProvider(ALCHEMY_API_URL))

# Token addresses for verification
USDC = Web3.to_checksum_address("0xa0b86991c6218b36c1d19d4a2e9eb0ce3606eb48")
WBTC = Web3.to_checksum_address("0x2260FAC5E5542a773Aa44fBCfeDf7C193bc2C599")
ETH = Web3.to_checksum_address("0xEeeeeEeeeEeEeeEeEeEeeEEEeeeeEeeeeeeeEEeE")

# Pool ABI for get_dy function
pool_abi = [{
    "name": "get_dy",
    "outputs": [{"type": "uint256", "name": ""}],
    "inputs": [
        {"type": "uint256", "name": "i"},
        {"type": "uint256", "name": "j"},
        {"type": "uint256", "name": "dx"}
    ],
    "stateMutability": "view",
    "type": "function"
}, {
    "name": "coins",
    "outputs": [{"type": "address", "name": ""}],
    "inputs": [{"type": "uint256", "name": "arg0"}],
    "stateMutability": "view",
    "type": "function"
}]

def get_curve_prices() -> Dict[str, Dict[str, float]]:
    """
    Get prices from Curve pools and return a dictionary of pool prices
    Returns:
        Dict with pool addresses as keys and price info as values
    """
    # Pool addresses and their coin indices
    pools = {
        Web3.to_checksum_address('0x7f86bf177dd4f3494b841a37e810a34dd56c829b'): {
            'USDC': 0,
            'WBTC': 1, 
            'ETH': 2
        },
        Web3.to_checksum_address('0xd51a44d3fae010294c616388b506acda1bfaae46'): {
            'USDT': 0,
            'WBTC': 1,
            'ETH': 2
        }
    }

    # Create contract instances for each pool
    pool_contracts = {
        addr: w3.eth.contract(address=addr, abi=pool_abi)
        for addr in pools.keys()
    }

    pool_prices = {}

    for pool_address, pool_contract in pool_contracts.items():
        try:
            # Get coin addresses from pool and verify
            coin0 = pool_contract.functions.coins(0).call()
            coin1 = pool_contract.functions.coins(1).call()
            coin2 = pool_contract.functions.coins(2).call()

            # ETH prices
            eth_input = 1 * 10**18  # 1 ETH
            usdc_amount = pool_contract.functions.get_dy(2, 0, eth_input).call()
            eth_sell_price = usdc_amount / (10**6)

            usdc_amount = 3000 * 10**6  # 3000 USDC
            eth_amount = pool_contract.functions.get_dy(0, 2, usdc_amount).call()
            eth_buy_price = (3000 / (eth_amount / 10**18))

            # WBTC prices
            wbtc_input = int(0.05 * 10**8)  # 0.05 WBTC
            usdc_amount = pool_contract.functions.get_dy(1, 0, wbtc_input).call()
            wbtc_sell_price = (0.05 / (usdc_amount / (10**6)))

            usdc_amount = 3000 * 10**6  # 3000 USDC
            wbtc_amount = pool_contract.functions.get_dy(0, 1, usdc_amount).call()
            wbtc_buy_price = (3000 / (wbtc_amount / 10**8))

            pool_prices[pool_address] = {
                'eth_buy': eth_buy_price,
                'eth_sell': eth_sell_price,
                'wbtc_buy': wbtc_buy_price,
                'wbtc_sell': wbtc_sell_price
            }

        except Exception as e:
            print(f"Error with pool {pool_address}: {str(e)}")
            continue

    return pool_prices

def check_arbitrage(pool_prices: Dict[str, Dict[str, float]]) -> None:
    """Check for arbitrage opportunities between pools"""
    for pool_address, prices in pool_prices.items():
        for other_pool, other_prices in pool_prices.items():
            if other_pool == pool_address:
                continue
                
            # Check ETH arbitrage between pools
            eth_profit = other_prices['eth_sell'] - prices['eth_buy']
            eth_profit_pct = (eth_profit / prices['eth_buy']) * 100
            
            if eth_profit_pct > 0:
                print(f"\nETH Arbitrage Opportunity between pools:")
                print(f"Buy from {pool_address} at {prices['eth_buy']:.2f} USDC")
                print(f"Sell to {other_pool} at {other_prices['eth_sell']:.2f} USDC")
                print(f"Profit per ETH: {eth_profit:.2f} USDC ({eth_profit_pct:.2f}%)")

            # Check WBTC arbitrage between pools
            wbtc_profit = other_prices['wbtc_sell'] - prices['wbtc_buy']
            wbtc_profit_pct = (wbtc_profit / prices['wbtc_buy']) * 100
            
            if wbtc_profit_pct > 0:
                print(f"\nWBTC Arbitrage Opportunity between pools:")
                print(f"Buy from {pool_address} at {prices['wbtc_buy']:.2f} USDC")
                print(f"Sell to {other_pool} at {other_prices['wbtc_sell']:.2f} USDC")
                print(f"Profit per WBTC: {wbtc_profit:.2f} USDC ({wbtc_profit_pct:.2f}%)")

if __name__ == "__main__":
    prices = get_curve_prices()
    check_arbitrage(prices)
