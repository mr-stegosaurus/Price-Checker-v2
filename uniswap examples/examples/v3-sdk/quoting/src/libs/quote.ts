import { ethers } from 'ethers'
import { CurrentConfig } from '../config'
import { computePoolAddress } from '@uniswap/v3-sdk'
import Quoter from '@uniswap/v3-periphery/artifacts/contracts/lens/Quoter.sol/Quoter.json'
import IUniswapV3PoolABI from '@uniswap/v3-core/artifacts/contracts/interfaces/IUniswapV3Pool.sol/IUniswapV3Pool.json'
import {
  POOL_FACTORY_CONTRACT_ADDRESS,
  QUOTER_CONTRACT_ADDRESS,
} from '../libs/constants'
import { getProvider } from '../libs/providers'
import { toReadableAmount, fromReadableAmount } from '../libs/conversion'

export async function quote(): Promise<string> {
  const quoterContract = new ethers.Contract(
    QUOTER_CONTRACT_ADDRESS,
    Quoter.abi,
    getProvider()
  )
  const poolConstants = await getPoolConstants()

  const quotedAmountOut = await quoterContract.callStatic.quoteExactInputSingle(
    poolConstants.token0,
    poolConstants.token1,
    poolConstants.fee,
    fromReadableAmount(
      CurrentConfig.tokens.amountIn,
      CurrentConfig.tokens.in.decimals
    ).toString(),
    0
  )

  return toReadableAmount(quotedAmountOut, CurrentConfig.tokens.out.decimals)
}

async function getPoolConstants(): Promise<{
  token0: string
  token1: string
  fee: number
}> {
  console.log('Config:', {
    factoryAddress: POOL_FACTORY_CONTRACT_ADDRESS,
    tokenAAddress: CurrentConfig.tokens.in.address,
    tokenBAddress: CurrentConfig.tokens.out.address,
    fee: CurrentConfig.tokens.poolFee
  });

  const currentPoolAddress = computePoolAddress({
    factoryAddress: POOL_FACTORY_CONTRACT_ADDRESS,
    tokenA: CurrentConfig.tokens.in,
    tokenB: CurrentConfig.tokens.out,
    fee: CurrentConfig.tokens.poolFee,
  })
  
  console.log('Computed Pool Address:', currentPoolAddress)

  const provider = getProvider()
  const network = await provider.getNetwork()
  console.log('Network:', {
    chainId: network.chainId,
    name: network.name
  })

  const code = await provider.getCode(currentPoolAddress)
  console.log('Code at pool address:', code === '0x' ? 'No code (contract not deployed)' : 'Contract exists')

  const poolContract = new ethers.Contract(
    currentPoolAddress,
    IUniswapV3PoolABI.abi,
    getProvider()
  )

  try {
    const [token0, token1, fee] = await Promise.all([
      poolContract.token0(),
      poolContract.token1(),
      poolContract.fee(),
    ])
    
    console.log('Pool tokens:', { token0, token1, fee })
    
    return {
      token0,
      token1,
      fee,
    }
  } catch (error) {
    console.error('Error getting pool constants:', error)
    throw error
  }
}
