"""API server for Azure SRE Agent using FastAPI and assistant-ui integration."""

import os
from pyexpat.errors import messages
import yaml
import logging
import json

from utils import utils
from pathlib import Path
from dotenv import load_dotenv
from agent_framework import Agent

from fastapi.middleware.cors import CORSMiddleware
from ag_ui.encoder import EventEncoder
from fastapi import FastAPI, Request
from fastapi.responses import StreamingResponse

from utils import chat_client_builder
from tools.tools import (
    find_resource_by_name,
    list_resources,
    get_timeseries, 
    healthcheck_adf,
    healthcheck_app_insights,
    healthcheck_logic_app,
    update_dashboard,
    get_metrics,
    raise_jira_ticket,
    perform_healthcheck
)

load_dotenv()

# Read required configuration
endpoint = os.environ.get("AZURE_OPENAI_ENDPOINT")
deployment_name = os.environ.get("AZURE_OPENAI_CHAT_DEPLOYMENT_NAME")

logger = logging.getLogger(__name__)
logger.setLevel(os.getenv("LOG_LEVEL", "INFO"))

# Load YAML configuration
base_dir = Path.cwd() / "config"
config_file = base_dir / Path("resources.yaml").name
with open(config_file, "r", encoding="utf-8") as f:
    agent_config = yaml.safe_load(f)

# Create a custom message store
def create_message_store():
    #TODO: review return ChatMessageStore()
    return None

def get_chat_client():
    chat_builder = chat_client_builder.new_chat_client()

    return Agent(client= chat_builder, name= agent_config.get("name", ""), 
        instructions= agent_config.get("system_message", ""),
        description= agent_config.get("description", ""),
        chat_message_store_factory=create_message_store,
        tools=[ list_resources, 
                raise_jira_ticket, 
                get_metrics, 
                get_timeseries, 
                healthcheck_app_insights, 
                healthcheck_adf, 
                healthcheck_logic_app, 
                find_resource_by_name, 
                update_dashboard,
                perform_healthcheck
        ],
    )

# Create the AI agent
agent = get_chat_client()

# Create FastAPI app
app = FastAPI(title="Azure SRE Agent Server")

origins = [
    'http://localhost:3000',
    'http://127.0.0.1:3000',
    'http://192.168.68.77:3000'
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],  # Alhollow GET, POST, etc.
    allow_headers=["*"],
)

@app.get("/")
async def read_root():
    return {"message": "Hello World with UV and FastAPI!"}


@app.post("/api/chat")
async def agent_endpoint(request: Request):
    """Handle UI agent requests with streaming response."""
    try:
        input_data = await request.json()
        messages = utils.normalize_messages(input_data['messages'])

        async def event_generator():
            encoder = EventEncoder()

            # Use streaming responses
            stream = agent.run(messages, stream=True)
            async for update in stream:
                text = getattr(update, "text", str(update))
                if text:
                    payload = {"content": text}
                    yield f"data: {json.dumps(payload)}\n\n"
            final = await stream.get_final_response()

        return StreamingResponse(
            event_generator(),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "X-Accel-Buffering": "no",
            },
        )

    except Exception as e:
        logger.error(f"Error in agent endpoint: {e}", exc_info=True)
        return {"error": str(e)}

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="127.0.0.1", port=8000)