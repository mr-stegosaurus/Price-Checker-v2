Starting script to pull prices and calculate arbitrage opportunities. Starting with boilerplate ETH/USDC pools on Uniswap and Curve.

Markets seem efficient so not expecting many arb opportunities. Will try to spread out to more niche pools once boilerplate code is working.

To-Do
-Add CEXes
-Update curve pricing with more sophsiticated routing.
-Update uniswap pricing with more sophisticated routing.
-Create backtesting script to find historical arbitrage opportunities. [DONE]
-Create addtl backtesting script that uses TheGraph instead of Alchemy. Should be faster.
-Update Uniswap and Curve pricing to use all pools instead of just the 2 I have hardcoded.
-Create folders with scripts that run on separate chains (mainnet, base, arbitrum, etc.)