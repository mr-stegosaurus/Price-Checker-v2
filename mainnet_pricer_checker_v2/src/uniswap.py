from web3 import Web3
from eth_typing import HexAddress
from typing import Dict
from dotenv import load_dotenv
import os

# Load environment variables
load_dotenv()

# Get Alchemy API URL from environment variables
ALCHEMY_API_URL = os.getenv('ALCHEMY_API_URL')
w3 = Web3(Web3.HTTPProvider(ALCHEMY_API_URL))

# Constants
QUOTER_ADDRESS = "0xb27308f9F90D607463bb33eA1BeBb41C27CE5AB6"
USDC = Web3.to_checksum_address("0xa0b86991c6218b36c1d19d4a2e9eb0ce3606eb48")
WETH = Web3.to_checksum_address("0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2")

# ABIs remain the same as in original file
QUOTER_ABI = [{
    "inputs": [
        {"type": "address", "name": "tokenIn"},
        {"type": "address", "name": "tokenOut"},
        {"type": "uint24", "name": "fee"},
        {"type": "uint256", "name": "amountIn"},
        {"type": "uint160", "name": "sqrtPriceLimitX96"},
    ],
    "name": "quoteExactInputSingle",
    "outputs": [{"type": "uint256", "name": "amountOut"}],
    "stateMutability": "nonpayable",
    "type": "function"
}]

POOL_ABI = [
    {
        "inputs": [],
        "name": "token0",
        "outputs": [{"type": "address", "name": ""}],
        "stateMutability": "view",
        "type": "function"
    },
    {
        "inputs": [],
        "name": "token1",
        "outputs": [{"type": "address", "name": ""}],
        "stateMutability": "view",
        "type": "function"
    },
    {
        "inputs": [],
        "name": "fee",
        "outputs": [{"type": "uint24", "name": ""}],
        "stateMutability": "view",
        "type": "function"
    }
]

def get_uniswap_prices() -> Dict[str, Dict[str, float]]:
    """
    Get prices from Uniswap pools and return a dictionary of pool prices
    Returns:
        Dict with pool addresses as keys and price info as values
    """
    pools = {
        Web3.to_checksum_address("0x8ad599c3A0ff1De082011EFDDc58f1908eb6e6D8"): "0.3% fee pool",
        Web3.to_checksum_address("0x88e6A0c2dDD26FEEb64F039a2c41296FcB3f5640"): "0.05% fee pool"
    }
    
    quoter_contract = w3.eth.contract(address=QUOTER_ADDRESS, abi=QUOTER_ABI)
    pool_prices = {}

    for pool_address in pools.keys():
        try:
            token0, token1, fee = get_pool_info(pool_address)
            
            # Determine token ordering
            is_usdc_token0 = token0.lower() == USDC.lower()
            usdc_token = token0 if is_usdc_token0 else token1
            weth_token = token1 if is_usdc_token0 else token0
            
            # Get ETH sell price (ETH -> USDC)
            eth_input = 1 * 10**18  # 1 ETH
            usdc_amount = quoter_contract.functions.quoteExactInputSingle(
                weth_token,
                usdc_token,
                fee,
                eth_input,
                0
            ).call()
            eth_sell_price = usdc_amount / (10**6)
            
            # Get ETH buy price (USDC -> ETH)
            usdc_input = 3000 * 10**6  # 1000 USDC
            eth_amount = quoter_contract.functions.quoteExactInputSingle(
                usdc_token,
                weth_token,
                fee,
                usdc_input,
                0
            ).call()
            eth_buy_price = (3000 / (eth_amount / 10**18))
            
            pool_prices[pool_address] = {
                'eth_buy': eth_buy_price,
                'eth_sell': eth_sell_price,
                'name': 'Uniswap'
            }

        except Exception as e:
            print(f"Error with pool {pool_address}: {str(e)}")
            continue
            
    return pool_prices

def get_pool_info(pool_address: HexAddress):
    """Get token addresses and fee from pool contract"""
    pool_contract = w3.eth.contract(address=pool_address, abi=POOL_ABI)
    token0 = pool_contract.functions.token0().call()
    token1 = pool_contract.functions.token1().call()
    fee = pool_contract.functions.fee().call()
    return token0, token1, fee

if __name__ == "__main__":
    prices = get_uniswap_prices()
    print(prices)
