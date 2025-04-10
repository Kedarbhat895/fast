from fastapi import FastAPI, Request, Response
from twilio.twiml.messaging_response import MessagingResponse
from twilio.rest import Client
from autogen import UserProxyAgent, GroupChat, GroupChatManager
import os
from dotenv import load_dotenv
import logging
import sys
import traceback

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

try:
    # Load environment variables
    load_dotenv(override=True)
    logger.info("Environment variables loaded")

    # Initialize Twilio client
    account_sid = os.getenv('TWILIO_ACCOUNT_SID')
    auth_token = os.getenv('TWILIO_AUTH_TOKEN')
    twilio_phone = os.getenv('TWILIO_PHONE_NUMBER')
    twilio_client = Client(account_sid, auth_token)
    logger.info("Twilio client initialized")

    # Import agents
    logger.info("Importing agents...")
    from agents.orchestrator import create_orchestrator_agent
    from agents.item_agent import create_item_agent
    from agents.cart_agent import create_cart_agent
    from agents.order_agent import create_order_agent
    logger.info("Agents imported successfully")

    # Initialize agents
    logger.info("Initializing agents...")
    user_proxy = UserProxyAgent(
        name="User",
        human_input_mode="NEVER",
        code_execution_config=False
    )

    orchestrator = create_orchestrator_agent()
    item_agent = create_item_agent()
    cart_agent = create_cart_agent()
    order_agent = create_order_agent()
    logger.info("Agents initialized successfully")

    # Create group chat with fixed speaker order
    logger.info("Creating group chat...")
    group_chat = GroupChat(
        agents=[user_proxy, orchestrator, item_agent, cart_agent, order_agent],
        messages=[],
        max_round=10,
        speaker_selection_method="round_robin"  # Use round-robin to avoid API calls
    )
    logger.info("Group chat created successfully")

    # Create chat manager with minimal configuration
    manager = GroupChatManager(
        groupchat=group_chat,
        llm_config={
            "config_list": [{
                "model": "gpt-4-0613",
                "api_key": os.getenv("OPENAI_API_KEY")
            }]
        }
    )

except Exception as e:
    logger.error("Error during initialization:")
    logger.error(traceback.format_exc())
    raise e

# Store user sessions
user_sessions = {}

def get_user_session(phone_number: str):
    if phone_number not in user_sessions:
        logger.info(f"Creating new session for user: {phone_number}")
        user_sessions[phone_number] = {
            "messages": [],
            "last_agent": None,
            "manager": manager  # Use the same manager for all users
        }
    return user_sessions[phone_number]

async def process_message(phone_number: str, message: str):
    try:
        logger.info(f"Processing message from {phone_number}: {message}")

        # Get or create user session
        session = get_user_session(phone_number)

        # Start chat directly with orchestrator
        logger.info("Starting chat with orchestrator...")
        chat_response = await session["manager"].initiate_chat(
            user_proxy,
            message=message,
            clear_history=False
        )

        # Get the messages from the group chat
        messages = session["manager"].groupchat.messages
        
        # Log all messages for debugging
        logger.info("--- Full Chat History ---")
        for m in messages:
            logger.info(f"{m['name']}: {m['content']}")
        
        # Find the last message from any agent
        agent_responses = [m for m in reversed(messages) 
                         if m["name"] != "User" 
                         and m["content"]]
        
        if not agent_responses:
            logger.warning("No agent responses found in chat history")
            last_response = "I couldn't process your request. Please try again."
        else:
            last_response = agent_responses[0]["content"]
            logger.info(f"Using response from {agent_responses[0]['name']}: {last_response}")

        # Send response via Twilio
        twilio_client.messages.create(
            from_=f"whatsapp:{twilio_phone}",
            body=last_response,
            to=f"whatsapp:{phone_number}"
        )

        return Response(content="", media_type="text/xml")

    except Exception as e:
        logger.error(f"Error processing message: {str(e)}")
        logger.error(traceback.format_exc())
        return Response(content="", media_type="text/xml")

app = FastAPI()

@app.post("/whatsapp/webhook")
async def whatsapp_webhook(request: Request):
    try:
        logger.info("WhatsApp webhook triggered!")
        form_data = await request.form()
        logger.info(f"Received form data: {form_data}")
        
        incoming_msg = form_data.get('Body', '').strip()
        phone_number = form_data.get('From', '').replace('whatsapp:', '')
        
        logger.info(f"Message from {phone_number}: {incoming_msg}")
        
        # Process the message
        await process_message(phone_number, incoming_msg)
        
        # Return empty 200 OK response
        return Response(status_code=200)
    except Exception as e:
        logger.error(f"Error processing webhook: {str(e)}")
        logger.error(traceback.format_exc())
        return Response(status_code=500) 