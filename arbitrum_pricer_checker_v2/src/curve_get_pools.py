from web3 import Web3
from typing import Dict, Optional
from dotenv import load_dotenv
import os

# Load environment variables
load_dotenv()

# Get Alchemy API URL from environment variables
ALCHEMY_API_URL = os.getenv('ARB_ALCHEMY_API_URL')
w3 = Web3(Web3.HTTPProvider(ALCHEMY_API_URL))

# Common addresses for ETH and WETH on Arbitrum
WETH = "0x82aF49447D8a07e3bd95BD0d56f35241523fBab1"  # Wrapped ETH
CRVUSD = Web3.to_checksum_address("0x498bf2b1e120fed3ad3d42ea2165e9b73f99c1e5") #crvUSD

# Add MetaRegistry ABI
meta_registry_abi = [{
    "name": "find_pools_for_coins",
    "outputs": [{"type": "address[]", "name": ""}],
    "inputs": [
        {"type": "address", "name": "_from"},
        {"type": "address", "name": "_to"}
    ],
    "stateMutability": "view",
    "type": "function"
}]

# Get RateProvider from AddressProvider
address_provider = w3.eth.contract(
    address=Web3.to_checksum_address("0x5ffe7FB82894076ECB99A30D6A32e969e6e35E98"),
    abi=[{"name": "get_address", "outputs": [{"type": "address"}], "inputs": [{"type": "uint256"}], "stateMutability": "view", "type": "function"}]
)
rate_provider_address = address_provider.functions.get_address(7).call()
print(rate_provider_address)

# Create contract instance for the rate provider
rate_provider = w3.eth.contract(
    address=Web3.to_checksum_address(rate_provider_address),
    abi=meta_registry_abi  # Using the same ABI since it's the same interface
)

# Find pools containing ETH and crvUSD
eth_crvusd_pools = rate_provider.functions.find_pools_for_coins(
    WETH,  # Using WETH address since pools use wrapped ETH
    CRVUSD
).call()

print(f"Found {len(eth_crvusd_pools)} pools containing ETH and crvUSD:")
for pool in eth_crvusd_pools:
    print(f"Pool address: {pool}")
