from autogen import AssistantAgent
import requests
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def get_categories():
    print("[DEBUG] Calling backend: /getAllCategories")
    # For testing, you can mock the response
    try:
        response = requests.get("http://localhost:8000/getAllCategories")
        data = response.json()
        return "Available categories: " + ", ".join(data["categories"])
    except:
        print("[DEBUG] Error connecting to backend, returning mock data")
        return "Available categories: Electronics, Clothing, Home, Books"

def get_category_items(category: str):
    print(f"[DEBUG] Calling backend: /getAllItems/{category}")
    try:
        response = requests.get(f"http://localhost:8000/getAllItems/{category}")
        data = response.json()
        items = []
        for item in data["items"]:
            items.append(f"{item['name']}: ${item['price']} per {item['unit']}")
        return f"Items in {category}:\n" + "\n".join(items)
    except:
        print("[DEBUG] Error connecting to backend")
        return f"Failed to get items in {category}. Please try again."

def get_item_info(item_id: int):
    print(f"[DEBUG] Calling backend: /getItemInfo/{item_id}")
    try:
        response = requests.get(f"http://localhost:8000/getItemInfo/{item_id}")
        data = response.json()["item"]
        return f"Item {item_id}: {data['name']}, Price: ${data['price']}, Unit: {data['unit']}"
    except:
        print("[DEBUG] Error connecting to backend, returning mock data")
        return f"Item {item_id}: Sample Item, Price: $99.99"

# Define function schema for the LLM to understand how to call the functions
function_map = {
    "get_categories": get_categories,
    "get_category_items": get_category_items,
    "get_item_info": get_item_info
}

def create_item_agent():
    agent = AssistantAgent(
        name="ItemAgent",
        system_message=(
            "You are the ItemAgent. Your role is to help users find products. "
            "Use these functions:\n"
            "1. get_categories() - List all available product categories\n"
            "2. get_category_items(category) - List all items in a category\n"
            "3. get_item_info(item_id) - Get details about a specific item\n"
            "\nNEVER make up responses. ALWAYS use the functions provided."
        ),
        llm_config={
            "config_list": [{"model": "gpt-4-0613", "api_key": os.getenv("OPENAI_API_KEY")}],
            "functions": [
                {
                    "name": "get_categories",
                    "description": "Get all available product categories",
                    "parameters": {
                        "type": "object",
                        "properties": {},
                        "required": []
                    }
                },
                {
                    "name": "get_category_items",
                    "description": "Get all items in a category",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "category": {
                                "type": "string",
                                "description": "The category to get items from"
                            }
                        },
                        "required": ["category"]
                    }
                },
                {
                    "name": "get_item_info",
                    "description": "Get information about a specific item",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "item_id": {
                                "type": "integer",
                                "description": "The ID of the item to get information about"
                            }
                        },
                        "required": ["item_id"]
                    }
                }
            ]
        }
    )
    
    # Register the functions
    agent.register_function(
        function_map={
            "get_categories": get_categories,
            "get_category_items": get_category_items,
            "get_item_info": get_item_info
        }
    )
    
    return agent