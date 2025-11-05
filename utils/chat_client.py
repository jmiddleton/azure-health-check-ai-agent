
import os
import logging
from dotenv import load_dotenv
from dotenv import load_dotenv
from agent_framework.openai import OpenAIChatClient, OpenAIResponsesClient
from agent_framework import ChatAgent
from agent_framework.azure import AzureOpenAIChatClient

load_dotenv()

logger = logging.getLogger("ms_agent")
logger.setLevel(os.getenv("LOG_LEVEL", "DEBUG"))

def new_chat_client() -> ChatAgent:
    """Create a new ChatAgent instance based on environment configuration."""
    chat_client = None
    if os.getenv("OPENAI_API_KEY") == "ollama":
        logger.info("Using Ollama as the backend for the agent.")
        chat_client = OpenAIChatClient(
                api_key="ollama",
                base_url=os.getenv("OLLAMA_ENDPOINT"),
                model_id=os.getenv("OLLAMA_CHAT_MODEL_ID"),
            )
    elif os.getenv("OPENAI_API_KEY") == "azureopenai":
        logger.info("Using Azure OpenAI as the backend for the agent.")
        chat_client = AzureOpenAIChatClient(
            endpoint=os.getenv("AZURE_OPENAI_ENDPOINT"),
            api_version=os.getenv("AZURE_OPENAI_API_VERSION"),
            api_key=os.getenv("AZURE_OPENAI_SUBSCRIPTION_KEY"),
            deployment_name=os.getenv("AZURE_OPENAI_CHAT_DEPLOYMENT_NAME"),
        )
    else:
        logger.info("Using OpenAI as the backend for the agent.")
        chat_client = OpenAIResponsesClient(
                api_key=os.getenv("OPENAI_API_KEY"),
                model_id=os.getenv("OPENAI_CHAT_MODEL_ID"),
            )

    return chat_client