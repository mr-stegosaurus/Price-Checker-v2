from web3 import Web3
from typing import Dict, Optional
from dotenv import load_dotenv
import os

# Load environment variables
load_dotenv()

# Get Alchemy API URL from environment variables
ALCHEMY_API_URL = os.getenv('ARB_ALCHEMY_API_URL')
w3 = Web3(Web3.HTTPProvider(ALCHEMY_API_URL))

# Get RateProvider from AddressProvider
address_provider = w3.eth.contract(
    address=Web3.to_checksum_address("0x5ffe7FB82894076ECB99A30D6A32e969e6e35E98"),
    abi=[{"name": "get_address", "outputs": [{"type": "address"}], "inputs": [{"type": "uint256"}], "stateMutability": "view", "type": "function"}]
)
rate_provider_address = address_provider.functions.get_address(18).call()

# Setup RateProvider contract
rate_provider_abi = [{
    "name": "get_quotes",
    "outputs": [{
        "type": "tuple[]",
        "components": [
            {"name": "source_token_index", "type": "uint256"},
            {"name": "dest_token_index", "type": "uint256"},
            {"name": "is_underlying", "type": "bool"},
            {"name": "amount_out", "type": "uint256"},
            {"name": "pool", "type": "address"},
            {"name": "source_token_pool_balance", "type": "uint256"},
            {"name": "dest_token_pool_balance", "type": "uint256"},
            {"name": "pool_type", "type": "uint8"}
        ]
    }],
    "inputs": [
        {"type": "address", "name": "source_token"},
        {"type": "address", "name": "destination_token"},
        {"type": "uint256", "name": "amount_in"}
    ],
    "stateMutability": "view",
    "type": "function"
}]

rate_provider = w3.eth.contract(
    address=rate_provider_address,
    abi=rate_provider_abi
)

# Get quotes for 1 ETH to USDC
amount_in = 1 * 10**18  # 1 ETH in wei

# Common addresses
WETH = Web3.to_checksum_address("0x82aF49447D8a07e3bd95BD0d56f35241523fBab1")  # Wrapped ETH
CRVUSD = Web3.to_checksum_address("0x498bf2b1e120fed3ad3d42ea2165e9b73f99c1e5") #crvUSD
USDC = Web3.to_checksum_address("0xaf88d065e77c8cc2239327c5edb3a432268e5831") #USDC

# Initialize quotes variable
weth_quotes = []

# Add debug prints
print(f"\nDebug Info:")
print(f"Address Provider: {address_provider.address}")
print(f"Rate Provider: {rate_provider_address}")

# Get WETH to crvUSD quotes
try:
    print("\nAttempting WETH -> crvUSD quote...")
    weth_quotes = rate_provider.functions.get_quotes(WETH, CRVUSD, amount_in).call()
    print(f"Success! Found {len(weth_quotes)} WETH routes")
except Exception as e:
    print(f"Error getting WETH quotes: {str(e)}")

# Print token addresses
print("\nToken Addresses Used:")
print(f"WETH: {WETH}")
print(f"crvUSD: {CRVUSD}")

# Check WETH routes
print("\nWETH Quotes:")
for quote in weth_quotes:
    print(f"Amount out: {quote[3] / 10**18} crvUSD")
    print(f"Pool: {quote[4]}")

# Get crvUSD to USDC quotes
try:
    print("\nAttempting crvUSD -> USDC quote...")
    crvusd_quotes = rate_provider.functions.get_quotes(CRVUSD, USDC, weth_quotes[0][3]).call()
    print(f"Success! Found {len(crvusd_quotes)} crvUSD routes")
except Exception as e:
    print(f"Error getting crvUSD quotes: {str(e)}")

# Print token addresses
print("\nToken Addresses Used:")
print(f"crvUSD: {CRVUSD}")
print(f"USDC: {USDC}")

# Check crvUSD routes
print("\ncrvUSD Quotes:")
for quote in crvusd_quotes:
    print(f"Amount out: {quote[3] / 10**6} USDC")  # Note: USDC has 6 decimals
    print(f"Pool: {quote[4]}")
    
# Now calculate reverse route
print("\nCalculating reverse route...")

# USDC -> crvUSD
try:
    print("\nAttempting USDC -> crvUSD quote...")
    usdc_quotes = rate_provider.functions.get_quotes(USDC, CRVUSD, crvusd_quotes[0][3]).call()
    print(f"Success! Found {len(usdc_quotes)} USDC routes")
except Exception as e:
    print(f"Error getting USDC quotes: {str(e)}")

print("\nUSDC -> crvUSD Quotes:")
for quote in usdc_quotes:
    print(f"Amount out: {quote[3] / 10**18} crvUSD")
    print(f"Pool: {quote[4]}")

# crvUSD -> WETH
try:
    print("\nAttempting crvUSD -> WETH quote...")
    final_quotes = rate_provider.functions.get_quotes(CRVUSD, WETH, usdc_quotes[0][3]).call()
    print(f"Success! Found {len(final_quotes)} crvUSD routes")
except Exception as e:
    print(f"Error getting final WETH quotes: {str(e)}")

print("\nFinal crvUSD -> WETH Quotes:")
for quote in final_quotes:
    print(f"Amount out: {quote[3] / 10**18} WETH")
    print(f"Pool: {quote[4]}")
    print(f"Net WETH change: {(quote[3] - amount_in) / 10**18} WETH")

# Add verification
print(f"Using Address Provider: {address_provider.address}")
