from gmx_python_sdk.scripts.v2.gmx_utils import ConfigManager
from gmx_python_sdk.example_scripts.estimate_swap_output import EstimateSwapOutput

class GMXRouter:
    def __init__(self):
        # Initialize config for Arbitrum
        self.config = ConfigManager("arbitrum")
        self.config.set_config()

    def get_swap_quote(self, token_in: str, token_out: str, amount_in: float) -> dict:
        """Get swap quote using GMX SDK
        
        Args:
            token_in: Token symbol (e.g., "WETH")
            token_out: Token symbol (e.g., "USDC")
            amount_in: Amount of input token (in human readable format)
        """
        try:
            output = EstimateSwapOutput(config=self.config).get_swap_output(
                in_token_symbol=token_in,
                out_token_symbol=token_out,
                token_amount=amount_in
            )
            
            return {
                "protocol": "GMX_V2",
                "token_in": token_in,
                "token_out": token_out,
                "amount_in": amount_in,
                "amount_out": output["output_amount"],
                "price_impact": output["price_impact"]
            }

        except Exception as e:
            print(f"Error getting quote: {str(e)}")
            return None

def main():
    router = GMXRouter()
    
    # Example: Swap 1 WETH for USDC
    quote = router.get_swap_quote("WETH", "USDC", 1.0)
    
    if quote:
        print("\n=== Summary ===")
        print(f"Swapping {quote['amount_in']} {quote['token_in']}")
        print(f"Receiving {quote['amount_out']} {quote['token_out']}")
        print(f"Price Impact: {quote['price_impact']}%")

if __name__ == "__main__":
    main()