from web3 import Web3
from eth_typing import HexAddress
from typing import Dict, List
import time
import logging
from datetime import datetime
import os
import json

# Import existing price fetching functions
from curve_get_price import get_curve_prices
from uniswap import get_uniswap_prices  # Updated import

def setup_logging():
    # Create logs directory if it doesn't exist
    log_dir = 'logs'
    if not os.path.exists(log_dir):
        os.makedirs(log_dir)
    
    # Setup logging to file
    timestamp = datetime.now().strftime('%Y%m%d')
    log_file = f'{log_dir}/arbitrage_{timestamp}.log'
    json_file = f'{log_dir}/opportunities_{timestamp}.json'
    
    class CustomFormatter(logging.Formatter):
        def format(self, record):
            # Only add timestamp for the main header message
            if "=== Checking prices" in record.msg:
                self._style._fmt = '%(asctime)s\n%(message)s\n'
            else:
                self._style._fmt = '%(message)s'
            return super().format(record)
    
    # Create handlers
    file_handler = logging.FileHandler(log_file)
    console_handler = logging.StreamHandler()
    
    # Use the custom formatter for both handlers
    formatter = CustomFormatter()
    file_handler.setFormatter(formatter)
    console_handler.setFormatter(formatter)
    
    # Create logger
    logger = logging.getLogger(__name__)
    logger.setLevel(logging.INFO)
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)
    logger.propagate = False
    
    return logger, json_file

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
    logger, json_file = setup_logging()
    while True:
        logger.info("\n=== Checking prices and arbitrage opportunities ===")
        
        all_pools = []
        
        # Get Curve prices
        curve_prices = get_curve_prices()
        if curve_prices:
            for pool_address, prices in curve_prices.items():
                prices['name'] = 'Curve'
                all_pools.append(prices)
                logger.info(f"\nCurve Pool ({pool_address}):")
                logger.info(f"ETH Sell Price: {prices['eth_sell']:.2f} USDC")
                logger.info(f"ETH Buy Price: {prices['eth_buy']:.2f} USDC")
        
        # Get Uniswap prices
        uniswap_prices = get_uniswap_prices()
        if uniswap_prices:
            for pool_address, prices in uniswap_prices.items():
                all_pools.append(prices)
                logger.info(f"\nUniswap Pool ({pool_address}):")
                logger.info(f"ETH Sell Price: {prices['eth_sell']:.2f} USDC")
                logger.info(f"ETH Buy Price: {prices['eth_buy']:.2f} USDC")
        
        opportunities = find_arbitrage_opportunities(all_pools)
        
        if opportunities:
            logger.info("\n=== Arbitrage Opportunities ===")
            for opp in opportunities:
                logger.info(f"\nBuy from {opp['buy_pool']} at {opp['buy_price']:.2f} USDC")
                logger.info(f"Sell to {opp['sell_pool']} at {opp['sell_price']:.2f} USDC")
                logger.info(f"Profit per ETH: {opp['profit_per_eth']:.2f} USDC")
                logger.info(f"Profit percentage: {opp['profit_percentage']:.2f}%")
        else:
            logger.info("\nNo arbitrage opportunities found")
        
        time.sleep(10) #check every 10 seconds  

if __name__ == "__main__":
    main()
