from web3 import Web3
from datetime import datetime, timedelta
import time
from typing import Dict, List
import json
from curve_get_price import get_curve_prices
from uniswap import get_uniswap_prices
from arb import find_arbitrage_opportunities
from dotenv import load_dotenv
import os

# Load environment variables
load_dotenv()

# Get Alchemy API URL from environment variables
ALCHEMY_API_URL = os.getenv('ALCHEMY_API_URL')
w3 = Web3(Web3.HTTPProvider(ALCHEMY_API_URL))

def get_block_by_timestamp(timestamp: int) -> int:
    """Get the closest block number for a given timestamp"""
    latest = w3.eth.block_number
    earliest = latest - 1_000_000  # Look back ~1M blocks
    
    while earliest <= latest:
        mid = (earliest + latest) // 2
        block = w3.eth.get_block(mid)
        
        if block.timestamp == timestamp:
            return mid
        elif block.timestamp < timestamp:
            earliest = mid + 1
        else:
            latest = mid - 1
            
    return earliest

def get_prices_at_block(block_number: int) -> List[Dict]:
    """Get all pool prices at a specific block"""
    # Set block number for web3 calls
    w3.eth.default_block = block_number
    
    all_pools = []
    
    try:
        # Get Curve prices
        curve_prices = get_curve_prices()
        if curve_prices:
            for pool_address, prices in curve_prices.items():
                prices['name'] = 'Curve'
                prices['block'] = block_number
                all_pools.append(prices)
        
        # Get Uniswap prices
        uniswap_prices = get_uniswap_prices()
        if uniswap_prices:
            for pool_address, prices in uniswap_prices.items():
                prices['block'] = block_number
                all_pools.append(prices)
                
    except Exception as e:
        print(f"Error getting prices for block {block_number}: {str(e)}")
    
    # Reset default block
    w3.eth.default_block = 'latest'
    return all_pools

def analyze_historical_arbitrage(days: int = 3, interval_minutes: int = 30):
    """
    Analyze arbitrage opportunities over the past X days
    Args:
        days: Number of days to look back
        interval_minutes: Minutes between each check
    """
    end_time = int(time.time())
    start_time = end_time - (days * 24 * 60 * 60)
    
    # Store all opportunities
    all_opportunities = []
    
    # Create timestamps for each interval
    current_time = start_time
    while current_time <= end_time:
        try:
            # Get block number for this timestamp
            block = get_block_by_timestamp(current_time)
            
            # Get prices for this block
            prices = get_prices_at_block(block)
            
            # Find arbitrage opportunities
            opportunities = find_arbitrage_opportunities(prices)
            
            if opportunities:
                for opp in opportunities:
                    opp['timestamp'] = current_time
                    opp['block'] = block
                    all_opportunities.append(opp)
                    
                    print(f"\nArbitrage found at block {block} ({datetime.fromtimestamp(current_time)})")
                    print(f"Buy from {opp['buy_pool']} at {opp['buy_price']:.2f} USDC")
                    print(f"Sell to {opp['sell_pool']} at {opp['sell_price']:.2f} USDC")
                    print(f"Profit per ETH: {opp['profit_per_eth']:.2f} USDC ({opp['profit_percentage']:.2f}%)")
            
        except Exception as e:
            print(f"Error processing timestamp {current_time}: {str(e)}")
            
        current_time += interval_minutes * 60
        
    # Save results to file
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"arbitrage_opportunities_{timestamp}.json"
    
    with open(filename, 'w') as f:
        json.dump(all_opportunities, f, indent=2)
        
    print(f"\nAnalysis complete. Found {len(all_opportunities)} opportunities.")
    print(f"Results saved to {filename}")
    
    return all_opportunities

def analyze_results(opportunities: List[Dict]):
    """Analyze and print statistics about the opportunities found"""
    if not opportunities:
        print("No opportunities found to analyze")
        return
        
    total_opps = len(opportunities)
    total_profit = sum(opp['profit_per_eth'] for opp in opportunities)
    avg_profit = total_profit / total_opps
    max_profit = max(opportunities, key=lambda x: x['profit_per_eth'])
    
    print("\n=== Arbitrage Analysis ===")
    print(f"Total opportunities found: {total_opps}")
    print(f"Total potential profit: {total_profit:.2f} USDC")
    print(f"Average profit per trade: {avg_profit:.2f} USDC")
    print("\nBest opportunity:")
    print(f"Block: {max_profit['block']}")
    print(f"Time: {datetime.fromtimestamp(max_profit['timestamp'])}")
    print(f"Buy from: {max_profit['buy_pool']} at {max_profit['buy_price']:.2f} USDC")
    print(f"Sell to: {max_profit['sell_pool']} at {max_profit['sell_price']:.2f} USDC")
    print(f"Profit: {max_profit['profit_per_eth']:.2f} USDC ({max_profit['profit_percentage']:.2f}%)")

if __name__ == "__main__":
    # Run analysis for past 3 days, checking every 30 minutes
    opportunities = analyze_historical_arbitrage(days=1, interval_minutes=0.5)
    
    # Analyze results
    analyze_results(opportunities) 