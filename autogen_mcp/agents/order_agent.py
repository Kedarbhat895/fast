from autogen import AssistantAgent
import requests
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv(override=True)

def confirm_order(user_id: str):
    print(f"[DEBUG] Calling backend: /order/confirm for user {user_id}")
    try:
        response = requests.post("http://localhost:8000/order/confirm", json={"user_id": user_id})
        data = response.json()
        items = [f"{item['name']}: {item['quantity']} units" for item in data["items"]]
        return (
            f"Order confirmed!\n"
            f"Total amount: ${data['total_amount']:.2f}\n"
            f"Items ordered:\n" + "\n".join(f"- {item}" for item in items)
        )
    except:
        print("[DEBUG] Error connecting to backend")
        return "Failed to confirm order. Please try again."

def create_order_agent():
    agent = AssistantAgent(
        name="OrderAgent",
        system_message=(
            "You are the OrderAgent. Your role is to help users confirm their orders.\n\n"
            "Use the confirm_order(user_id) function when:\n"
            "- The user wants to place/confirm their order\n"
            "- The user wants to checkout\n"
            "- The user is done shopping\n\n"
            "The function will process the order and return the order details.\n"
            "NEVER make up responses. ALWAYS use the function provided."
        ),
        llm_config={
            "config_list": [{"model": "gpt-4-0613", "api_key": os.getenv("OPENAI_API_KEY")}],
            "functions": [
                {
                    "name": "confirm_order",
                    "description": "Confirm the user's order and process checkout",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "user_id": {
                                "type": "string",
                                "description": "The ID of the user"
                            }
                        },
                        "required": ["user_id"]
                    }
                }
            ]
        }
    )
    
    # Register the functions
    agent.register_function(
        function_map={
            "confirm_order": confirm_order
        }
    )
    
    return agent
