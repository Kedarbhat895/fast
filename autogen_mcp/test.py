from autogen import UserProxyAgent, GroupChat, GroupChatManager
from agents.item_agent import create_item_agent

user_proxy = UserProxyAgent("user", human_input_mode="NEVER")
item_agent = create_item_agent()

groupchat = GroupChat(agents=[user_proxy, item_agent], messages=[], max_round=3)
chat_manager = GroupChatManager(groupchat=groupchat)

user_proxy.initiate_chat(chat_manager, message="Can you list all the categories?")