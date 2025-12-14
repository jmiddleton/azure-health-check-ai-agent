# Copyright (c) Punta Negra. All rights reserved.
# Licensed under the MIT License. See LICENSE in the project root for license information.


import chainlit as cl
from chainlit.data.sql_alchemy import SQLAlchemyDataLayer

import logging
import os
import yaml
from pathlib import Path
from dotenv import load_dotenv
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.schedulers.background import BackgroundScheduler
from agent_framework import ChatAgent
from agent_framework import ChatMessageStore
from chainlit.types import ThreadDict
from utils.charts import PlotlyChartCreator

from batch_healthcheck import batch_healthcheck
from tools.tools import (
    find_resource_by_name,
    list_resources,
    get_timeseries, 
    healthcheck_adf,
    healthcheck_app_insights,
    healthcheck_logic_app,
    perform_healthcheck,
    update_dashboard,
    get_metrics,
    raise_jira_ticket
)

USERS=["admin", "jorge"]
PASSWORD="admin"

load_dotenv()

agent_logger = logging.getLogger("ms_agent")
agent_logger.setLevel(os.getenv("LOG_LEVEL", "INFO"))

# Load YAML configuration
base_dir = Path.cwd() / "config"
config_file = base_dir / Path("resources.yaml").name
with open(config_file, "r", encoding="utf-8") as f:
    agent_config = yaml.safe_load(f)

# Create a custom message store
def create_message_store():
    return ChatMessageStore()

def get_chat_client():

    global _agent_instance
    if _agent_instance is None:
        from utils import chat_client_builder
        chat_client_builder = chat_client_builder.new_chat_client()

        _agent_instance = ChatAgent(name= agent_config.get("name", ""), chat_client= chat_client_builder,
            instructions= agent_config.get("system_message", ""),
            description= agent_config.get("description", ""),
            chat_message_store_factory=create_message_store,
            tools=[list_resources, raise_jira_ticket, 
                   get_metrics, get_timeseries, 
                   healthcheck_app_insights, healthcheck_adf, 
                   healthcheck_logic_app, perform_healthcheck, 
                   find_resource_by_name, update_dashboard
            ],
        )
    return _agent_instance

# scheduler for batch healthcheck
scheduler = AsyncIOScheduler()
_agent_instance = None

@cl.on_app_startup
async def startup():
    """Starts the scheduler to run batch healthcheck every 5 minutes.
    """
    scheduler.add_job(batch_healthcheck, "cron", hour=21, minute=0)  # Runs daily at 9:00 PM UTC
    scheduler.start()

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
            message="Can you please check the status of the resource with name web-puntanegra-dev02",
            icon="/public/learn.svg",
        ),
        cl.Starter(
            label="Detailed incident for Application Insights failures",
            message="Provide a detailed investigation of the recent failures in the Application Insights with name 'web-puntanegra-dev01'.",
            icon="/public/terminal.svg"
        ),
        cl.Starter(
            label="Get Azure monitor metrics",
            message="Can I get the count of Http 5xx errors for the last 168 hours of resource web-puntanegra-dev01?",
            icon="/public/write.svg",
        ),
        cl.Starter(
            label="Chart metrics",
            message="Can you draw the metric PipelineSucceededRuns for web-puntanegra-dev01?",
            icon="/public/chart.svg",
        )
    ]

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
    thread = get_chat_client().get_new_thread()
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

    async for part in get_chat_client().run_stream(message.content): #TODO: fix me, thread=thread):
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