# Copyright (c) Punta Negra PTY. All rights reserved.
# Licensed under the MIT License. See LICENSE in the project root for license information.


import chainlit as cl
from chainlit.data.sql_alchemy import SQLAlchemyDataLayer

import logging
import os
import yaml

from pathlib import Path
from dotenv import load_dotenv
from agent_framework import ChatAgent
from agent_framework.openai import OpenAIChatClient, OpenAIResponsesClient
from agent_framework.azure import AzureOpenAIChatClient
from agent_framework import ChatMessageStore
from chainlit.types import ThreadDict
from utils.charts import PlotlyChartCreator
from utils import chat_client

from tools.tools import (
    find_resource_by_name,
    get_timeseries, 
    healthcheck_adf,
    healthcheck_app_insights,
    healthcheck_logic_app,
    perform_healthcheck,
    update_dashboard,
    get_metrics,
    raise_jira_ticket
)

load_dotenv()

agent_logger = logging.getLogger("ms_agent")
agent_logger.setLevel(os.getenv("LOG_LEVEL", "INFO"))

# Load YAML configuration
config_file = Path("llm_system_prompt_config.yaml")
with open(config_file, "r", encoding="utf-8") as f:
    agent_config = yaml.safe_load(f)

# Create a custom message store
def create_message_store():
    return ChatMessageStore()

chat_client = chat_client.new_chat_client()

agent = ChatAgent(name= agent_config.get("name", ""), chat_client= chat_client,
    instructions= agent_config.get("system_message", ""),
    description= agent_config.get("description", ""),
    chat_message_store_factory=create_message_store,
    tools=[raise_jira_ticket, get_metrics, get_timeseries, healthcheck_app_insights, healthcheck_adf, healthcheck_logic_app, perform_healthcheck, find_resource_by_name, update_dashboard],
)

@cl.data_layer
def get_data_layer():
    """
    Returns an instance of CustomDataLayer.
    """
    return SQLAlchemyDataLayer(
        conninfo=os.getenv("DATABASE_URL", "")
    )   

@cl.set_starters
async def set_starters():
    return [
        cl.Starter(
            label="Perform Azure Health Check",
            message="""Please perform a full health check for entries.""",
            icon="/public/idea.svg",
        ),

        cl.Starter(
            label="Search for Azure Resource by Name",
            message="Can you please check the status of the resource with name \"my-logicapp-au-prd01\"?",
            icon="/public/learn.svg",
        ),
        cl.Starter(
            label="Chart metrics",
            message="Can you draw the metric PipelineSucceededRuns for my-datafactory-syd-prd01?",
            icon="/public/chart.svg",
        )

    ]

USERS=["admin", "jorge"]
PASSWORD="admin"

# AUTHENTICATION
@cl.password_auth_callback
def auth_callback(username: str, password: str):
    if (username in USERS and password == PASSWORD):
        return cl.User(
            identifier=username,
            metadata={},
        )
    else:
        return None

@cl.on_chat_start
async def start_chat():
    app_user = cl.user_session.get("user")
    
    cl.user_session.set("chat_history", [])
    thread = agent.get_new_thread()
    cl.user_session.set(f"{app_user.identifier}_thread", thread)
    
@cl.on_chat_resume
async def on_chat_resume(thread: ThreadDict):
    app_user = cl.user_session.get("user")
    #cl.user_session.set(f"{app_user.identifier}_thread", thread["id"])
    cl.user_session.set("chat_history", [])

    for message in thread["steps"]:
        if message["type"] == "user_message":
            cl.user_session.get("chat_history").append(
                {"role": "user", "content": message["output"]}
            )
        elif message["type"] == "assistant_message":
            cl.user_session.get("chat_history").append(
                {"role": "assistant", "content": message["output"]}
            )

@cl.on_message
async def on_message(message: cl.Message):
    app_user = cl.user_session.get("user")
    chat_history = cl.user_session.get("chat_history", [])
    thread = cl.user_session.get(f"{app_user.identifier}_thread")

    chat_history.append({"role": "user", "content": message.content})

    msg = cl.Message(content="")
    image_displayed = False

    async for part in agent.run_stream(message.content): #TODO: fix me, thread=thread):
        # Stream text tokens first
        if part.text and not image_displayed:
            await msg.stream_token(part.text)

        # Then handle image results if they appear
        elif hasattr(part, "contents") and part.contents:
            result = getattr(part.contents[0], "result", None)
            if result and isinstance(result, dict) and "timeseries" in result:
                try:
                    figure = PlotlyChartCreator.create_plotly(result["name"], "line", result["timeseries"])
                    elements = [cl.Plotly(name=result["name"], figure=figure, display="inline")]

                    await cl.Message(
                        content="Here’s the generated chart:",
                        elements=elements
                    ).send()
                    image_displayed = True
                    break  # Stop streaming once image is sent
                except Exception as e:
                    print("Could not extract image:", e)

    if not image_displayed:
        await msg.send()

    chat_history.append({"role": "assistant", "content": msg.content})
    cl.user_session.set("chat_history", chat_history)
    #cl.user_session.set(f"{app_user.identifier}_thread_serializer", thread.serialize())
    
if __name__ == "__main__":
    from chainlit.cli import run_chainlit
    run_chainlit(__file__)