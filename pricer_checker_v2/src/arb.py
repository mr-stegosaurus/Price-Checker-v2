from web3 import Web3
from eth_typing import HexAddress
from typing import Dict, List
import time

# Import existing price fetching functions
from curve_get_price import get_curve_prices
from uniswap import get_uniswap_prices  # Updated import

def find_arbitrage_opportunities(pools: List[Dict]) -> List[Dict]:
    """Find arbitrage opportunities between pools"""
    opportunities = []
    
    for i, pool1 in enumerate(pools):
        if not pool1:
            continue
            
        for j, pool2 in enumerate(pools[i+1:], i+1):
            if not pool2:
                continue
                
            # Buy low, sell high opportunities
            profit1 = pool2['eth_sell'] - pool1['eth_buy']  # Updated to match new price format
            profit2 = pool1['eth_sell'] - pool2['eth_buy']  # Updated to match new price format
            
            if profit1 > 0:
                opportunities.append({
                    'buy_pool': pool1['name'],
                    'sell_pool': pool2['name'],
                    'buy_price': pool1['eth_buy'],
                    'sell_price': pool2['eth_sell'],
                    'profit_per_eth': profit1,
                    'profit_percentage': (profit1 / pool1['eth_buy']) * 100
                })
                
            if profit2 > 0:
                opportunities.append({
                    'buy_pool': pool2['name'],
                    'sell_pool': pool1['name'],
                    'buy_price': pool2['eth_buy'],
                    'sell_price': pool1['eth_sell'],
                    'profit_per_eth': profit2,
                    'profit_percentage': (profit2 / pool2['eth_buy']) * 100
                })
    
    return opportunities

def main():
    while True:
        print("\n=== Checking prices and arbitrage opportunities ===")
        print(f"Timestamp: {time.strftime('%Y-%m-%d %H:%M:%S')}")
        
        all_pools = []
        
        # Get Curve prices
        curve_prices = get_curve_prices()
        if curve_prices:
            for pool_address, prices in curve_prices.items():
                prices['name'] = 'Curve'
                all_pools.append(prices)
                print(f"\nCurve Pool ({pool_address}):")
                print(f"ETH Sell Price: {prices['eth_sell']:.2f} USDC")
                print(f"ETH Buy Price: {prices['eth_buy']:.2f} USDC")
        
        # Get Uniswap prices
        uniswap_prices = get_uniswap_prices()
        if uniswap_prices:
            for pool_address, prices in uniswap_prices.items():
                all_pools.append(prices)
                print(f"\nUniswap Pool ({pool_address}):")
                print(f"ETH Sell Price: {prices['eth_sell']:.2f} USDC")
                print(f"ETH Buy Price: {prices['eth_buy']:.2f} USDC")
        
        # Find arbitrage opportunities
        opportunities = find_arbitrage_opportunities(all_pools)
        
        if opportunities:
            print("\n=== Arbitrage Opportunities ===")
            for opp in opportunities:
                print(f"\nBuy from {opp['buy_pool']} at {opp['buy_price']:.2f} USDC")
                print(f"Sell to {opp['sell_pool']} at {opp['sell_price']:.2f} USDC")
                print(f"Profit per ETH: {opp['profit_per_eth']:.2f} USDC")
                print(f"Profit percentage: {opp['profit_percentage']:.2f}%")
        else:
            print("\nNo arbitrage opportunities found")
        
        time.sleep(10)  # Check every 10 seconds

if __name__ == "__main__":
    main()
