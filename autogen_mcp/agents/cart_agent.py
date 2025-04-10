from autogen import AssistantAgent
import requests
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv(override=True)

def add_to_cart(user_id: str, item_id: int, quantity: float):
    payload = {"user_id": user_id, "item_id": item_id, "quantity": quantity}
    print("[DEBUG] Calling backend: /cart/add")
    try:
        response = requests.post("http://localhost:8000/cart/add", json=payload)
        data = response.json()
        return f"Added {quantity} units of item {item_id} to cart"
    except:
        print("[DEBUG] Error connecting to backend")
        return "Failed to add item to cart. Please try again."

def remove_from_cart(user_id: str, item_id: int):
    payload = {"user_id": user_id, "item_id": item_id}
    print("[DEBUG] Calling backend: /cart/remove")
    try:
        response = requests.post("http://localhost:8000/cart/remove", json=payload)
        data = response.json()
        return f"Removed item {item_id} from cart"
    except:
        print("[DEBUG] Error connecting to backend")
        return "Failed to remove item from cart. Please try again."

def view_cart(user_id: str):
    try:
        response = requests.get(f"http://localhost:8000/cart", params={"user_id": user_id})
        data = response.json()
        if not data["cart"]:
            return "Your cart is empty"
        items = []
        for item in data["cart"]:
            items.append(f"{item['name']}: {item['quantity']} {item.get('unit', 'units')}")
        return "Your cart contains:\n" + "\n".join(items)
    except:
        print("[DEBUG] Error connecting to backend")
        return "Failed to view cart. Please try again."

def create_cart_agent():
    agent = AssistantAgent(
        name="CartAgent",
        system_message=(
            "You are the CartAgent. Your role is to help users manage their shopping cart. "
            "Use these functions:\n"
            "1. add_to_cart(user_id, item_id, quantity) - When a user wants to buy items\n"
            "2. remove_from_cart(user_id, item_id) - When a user wants to remove items\n"
            "3. view_cart(user_id) - When a user wants to see what's in their cart\n"
            "\nNEVER make up responses. ALWAYS use the functions provided."
        ),
        llm_config={
            "config_list": [{"model": "gpt-4-0613", "api_key": os.getenv("OPENAI_API_KEY")}],
            "functions": [
                {
                    "name": "add_to_cart",
                    "description": "Add an item to the user's cart",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "user_id": {
                                "type": "string",
                                "description": "The ID of the user"
                            },
                            "item_id": {
                                "type": "integer",
                                "description": "The ID of the item to add"
                            },
                            "quantity": {
                                "type": "number",
                                "description": "The quantity to add"
                            }
                        },
                        "required": ["user_id", "item_id", "quantity"]
                    }
                },
                {
                    "name": "remove_from_cart",
                    "description": "Remove an item from the user's cart",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "user_id": {
                                "type": "string",
                                "description": "The ID of the user"
                            },
                            "item_id": {
                                "type": "integer",
                                "description": "The ID of the item to remove"
                            }
                        },
                        "required": ["user_id", "item_id"]
                    }
                },
                {
                    "name": "view_cart",
                    "description": "View the contents of the user's cart",
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
            "add_to_cart": add_to_cart,
            "remove_from_cart": remove_from_cart,
            "view_cart": view_cart
        }
    )
    
    return agent
