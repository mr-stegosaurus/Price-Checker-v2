Starting script to pull prices and calculate arbitrage opportunities. Starting with boilerplate ETH/USDC pools on Uniswap and Curve.

Markets seem efficient so not expecting many arb opportunities. Will try to spread out to more niche pools once boilerplate code is working.

Starting plan::
Trade WBTC/USDC/UDST/ETH on Arbitrum
Get best order quotes from Defi sources at various trade inputs (need to adjust for token decimals and calculate routes)
- Check on chain price against CEXes and find arbitrage opportunities
- GMX Started
- Curve Routing Started Debug
- Uniswap (Update with order routing logic)



To-Do
-Add CEXes (Coinbase started, Kraken next)
-Update curve pricing with more sophsiticated routing [DONE]
-Update uniswap pricing with more sophisticated routing.
-Create backtesting script to find historical arbitrage opportunities. [DONE]
-Create addtl backtesting script that uses TheGraph instead of Alchemy. Should be faster.
-Update Uniswap and Curve pricing to use all pools instead of just the 2 I have hardcoded. [IN PROGRESS]
-Create folders with scripts that run on separate chains (mainnet, base, arbitrum, etc.) [DONE]