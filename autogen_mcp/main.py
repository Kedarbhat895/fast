from fastapi import FastAPI, Form
from twilio.rest import Client
from twilio.twiml.messaging_response import MessagingResponse
from autogen import UserProxyAgent, GroupChat, GroupChatManager
from agents.orchestrator import create_orchestrator_agent
from agents.item_agent import create_item_agent
from agents.cart_agent import create_cart_agent
from agents.order_agent import create_order_agent
from dotenv import load_dotenv
import os

# Load environment variables
load_dotenv(override=True)

# Twilio setup
TWILIO_PHONE = os.getenv("TWILIO_PHONE_NUMBER")
TWILIO_SID = os.getenv("TWILIO_ACCOUNT_SID")
TWILIO_TOKEN = os.getenv("TWILIO_AUTH_TOKEN")
twilio_client = Client(TWILIO_SID, TWILIO_TOKEN)

# OpenAI API Key
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

app = FastAPI()

def send_reply_to_user(reply: str, sender: str = None):
    print("✅ CALLBACK TRIGGERED!")
    print(f"[{sender}] says: {reply}")
    if sender:
        twilio_client.messages.create(
            from_=f"whatsapp:{TWILIO_PHONE}",
            to=sender,
            body=reply
        )

# Create AutoGen agents
user_proxy = UserProxyAgent(
    name="User",
    code_execution_config=False,
    human_input_mode="ALWAYS"
)

orchestrator = create_orchestrator_agent()
item_agent = create_item_agent()
cart_agent = create_cart_agent()
order_agent = create_order_agent()

# Group chat setup
group_chat = GroupChat(
    agents=[user_proxy, orchestrator, item_agent, cart_agent, order_agent],
    messages=[],
    max_round=50
)

manager = GroupChatManager(
    groupchat=group_chat,
    llm_config={
        "config_list": [
            {
                "model": "gpt-3.5-turbo",
                "api_key": OPENAI_API_KEY
            }
        ]
    }
)

@app.post("/whatsapp/webhook")
async def whatsapp_webhook(
    From: str = Form(...),
    Body: str = Form(...)
):
    global user_whatsapp_number
    user_whatsapp_number = From
    print(f"Incoming from {From}: {Body}")

    # Step 1: Send message to User agent
    user_proxy.receive(Body, sender=user_proxy)

    # Step 2: Custom chat loop with step-by-step control
    max_steps = 20  # avoid infinite loop
    for i in range(max_steps):
        step_response = manager.step()  # Runs one message passing step
        if step_response is None:
            print("💤 Conversation ended.")
            break

        role = step_response.get("name")
        content = step_response.get("content", "").strip()

        if role and content:
            print(f"📤 {role}: {content}")
            if role != "User":
                send_reply_to_user(content, sender=user_whatsapp_number)
    print("🗣 Group chat messages so far:")
    for m in group_chat.messages:
        print(f"- {m['name']}: {m['content']}")

    response = MessagingResponse()
    response.message("Received! Let me think... 💬")
    return response.to_xml()


