from web3 import Web3

# Connect to network
w3 = Web3(Web3.HTTPProvider('https://eth-mainnet.g.alchemy.com/v2/1vrOjbMXRF6L4M_AgL-7W3jCvuVXKlRt'))

# More complete pool ABI for Curve pools
pool_abi = [{
    "name": "get_dy",
    "outputs": [{"type": "uint256", "name": ""}],
    "inputs": [
        {"type": "int128", "name": "i"},
        {"type": "int128", "name": "j"},
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
}, {
    "name": "get_virtual_price",
    "outputs": [{"type": "uint256", "name": ""}],
    "inputs": [],
    "stateMutability": "view",
    "type": "function"
}]

# First find the pool using MetaRegistry
registry_address = Web3.to_checksum_address('0xF98B45FA17DE75FB1aD0e7aFD971b0ca00e379fC')
registry_abi = [{
    "stateMutability": "view",
    "type": "function",
    "name": "find_pools_for_coins",
    "inputs": [
        {"name": "_from", "type": "address"},
        {"name": "_to", "type": "address"}
    ],
    "outputs": [{"name": "", "type": "address[]"}]
}]

registry = w3.eth.contract(address=registry_address, abi=registry_abi)

# Get pools for USDC/WETH
usdc = Web3.to_checksum_address("0xa0b86991c6218b36c1d19d4a2e9eb0ce3606eb48")
weth = Web3.to_checksum_address("0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2")
pools = registry.functions.find_pools_for_coins(usdc, weth).call()

print(f"Found pools: {pools}")

if pools:
    for pool_address in pools:
        print(f"\nChecking pool: {pool_address}")
        pool = w3.eth.contract(address=pool_address, abi=pool_abi)
        
        try:
            # Get coins to verify order
            coin0 = pool.functions.coins(0).call()
            coin1 = pool.functions.coins(1).call()
            print(f"coin0: {coin0}")
            print(f"coin1: {coin1}")
            
            # Try to get oracle price first
            try:
                price_oracle = pool.functions.price_oracle(0).call()
                print(f"Oracle price: {price_oracle / 10**18}")
            except Exception as e:
                print(f"No oracle price available: {str(e)}")
            
            # Amount in (1 USDC = 1e6)
            amount_in = 1000000  # 1 USDC
            
            # Determine correct order based on coin addresses
            if coin0.lower() == usdc.lower():
                print("Testing USDC -> WETH")
                dy = pool.functions.get_dy(0, 1, amount_in).call()
                price = dy / (10**18)
                print(f"1 USDC = {price} WETH")
            else:
                print("Testing WETH -> USDC")
                dy = pool.functions.get_dy(1, 0, amount_in).call()
                price = dy / (10**6)
                print(f"1 WETH = {price} USDC")
                
        except Exception as e:
            print(f"Error with pool {pool_address}: {str(e)}")
            continue