from web3 import Web3
from dotenv import load_dotenv
import os

# Load environment variables
load_dotenv()

# Get Alchemy API URL from environment variables
ALCHEMY_API_URL = os.getenv('ALCHEMY_API_URL')
w3 = Web3(Web3.HTTPProvider(ALCHEMY_API_URL))

# MetaRegistry contract address
registry_address = Web3.to_checksum_address('0xF98B45FA17DE75FB1aD0e7aFD971b0ca00e379fC')

# ABI for the find_pools_for_coins function
abi = [{
    "stateMutability": "view",
    "type": "function",
    "name": "find_pools_for_coins",
    "inputs": [
        {"name": "_from", "type": "address"},
        {"name": "_to", "type": "address"}
    ],
    "outputs": [{"name": "", "type": "address[]"}]
}]

# Create contract instance
registry = w3.eth.contract(address=registry_address, abi=abi)

# Call the function with checksum addresses
usdc = Web3.to_checksum_address("0xa0b86991c6218b36c1d19d4a2e9eb0ce3606eb48")
eth = Web3.to_checksum_address("0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2")
pools = registry.functions.find_pools_for_coins(usdc, eth).call()

print("Found pools:", pools)