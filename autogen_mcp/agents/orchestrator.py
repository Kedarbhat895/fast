from autogen import AssistantAgent
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv(override=True)


def create_orchestrator_agent():
    return AssistantAgent(
        name="Orchestrator",
        llm_config={"config_list": [{"model": "gpt-4-0613", "api_key": os.getenv("OPENAI_API_KEY")}]},
        system_message=(
            "You are the Orchestrator agent. Your role is to coordinate between different agents to help users shop:\n\n"
            "1. When users want to know about products or categories:\n"
            "   - Direct these queries to the ItemAgent\n"
            "   - The ItemAgent will list categories and provide item details\n\n"
            "2. When users want to buy items or manage their cart:\n"
            "   - Direct these queries to the CartAgent\n"
            "   - Help identify item IDs and quantities from user messages\n"
            "   - The CartAgent will handle adding items and viewing cart\n\n"
            "3. When users want to place orders:\n"
            "   - Direct these queries to the OrderAgent\n"
            "   - The OrderAgent will handle order confirmation\n\n"
            "IMPORTANT: Always let the specialized agents handle their specific tasks. Your job is to:\n"
            "- Understand user intent\n"
            "- Direct queries to the right agent\n"
            "- Help extract relevant information (like quantities and item IDs)\n"
            "- Ensure a smooth conversation flow"
        )
    )
