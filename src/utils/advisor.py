
import logging
import json
import os
from dotenv import load_dotenv
import yaml

from abc import abstractmethod
from pathlib import Path
from agent_framework import ChatAgent
from azure.identity.aio import AzureCliCredential
from azure.ai.projects.aio import AIProjectClient
from utils import chat_client_builder

load_dotenv()

logger = logging.getLogger("ms_agent")
logger.setLevel(os.getenv("LOG_LEVEL", "DEBUG"))

base_dir = Path.cwd() / "config"

class Advisor():
    def __init__(self):
        pass

    @abstractmethod
    async def get_recommendation(self, entry: dict) -> str:
        """Use an LLM to generate a short recommendation based on status or error."""
        pass

    async def recommend(self, data: list[dict]) -> None:
        """Add recommendations to each entry in the data list."""
        sorted_data = sorted(data, key=lambda x: int(x.get("idx", 0)))
        for item in sorted_data:
            status = item.get("status", "").lower()

            if "failed" in status:
                item["recommendation"] = await self.get_recommendation(item)
            else:
                item["recommendation"] = " - "


class SimpleLlmAdvisor(Advisor):
    """Class that provide Azure recommendations and health check functionalities."""
    def __init__(self):
        super().__init__()
        chat_client = chat_client_builder.new_chat_client()

        config_file = base_dir / Path("resources.yaml").name
        with open(config_file, "r", encoding="utf-8") as f:
            agent_config = yaml.safe_load(f)
            
        self.agent = ChatAgent(name= agent_config.get("name", ""), chat_client= chat_client,
            instructions= agent_config.get("recommendation_message", ""),
            description= agent_config.get("description", ""),
            tools=[],
        )
    
    async def get_recommendation(self, entry: dict) -> str:
        """Use an LLM to generate a short recommendation based on status or error."""
        
        logger.info(f"Generating recommendation for failed entry {entry.get('name')} using LLM...")
        response = await self.agent.run(f"Could you please provide a recommendation for the following entry: {json.dumps(entry)}")

        logger.info(f"LLM response for failed entry {entry.get('name')} generated.")
        return response.text.replace("\n", "<br>")

class AzureAgentAdvisor(Advisor):
    """Class that provides Azure-specific recommendations and health check functionalities."""
    def __init__(self):
        super().__init__()
        self.project_endpoint = os.environ["AZURE_PROJECT_ENDPOINT"]
        self.model_name = os.environ["AZURE_OPENAI_CHAT_DEPLOYMENT_NAME"]
        self.agent_id = os.environ["AZURE_EXISTING_AGENT_ID"]

        config_file = base_dir / Path("resources.yaml").name
        with open(config_file, "r", encoding="utf-8") as f:
            self.agent_config = yaml.safe_load(f)

    async def get_recommendation(self, entry: dict) -> str:
        """Use an Azure-specific LLM to generate a short recommendation based on status or error."""
        logger.info(f"Generating recommendation for entry {entry.get('name')} using LLM...")

        # Create the client
        async with (
            AzureCliCredential() as credential,
            AIProjectClient(endpoint=self.project_endpoint, credential=credential) as project_client,
        ):

            # Create an agent with custom functions
            azure_ai_agent = await project_client.agents.get_agent(
                agent_id=self.agent_id
            )

            chat_client = chat_client_builder.get_chat_client(project_client=project_client, agent_id=azure_ai_agent.id,
                            project_endpoint=self.project_endpoint, async_credential=credential)

            try:
                async with ChatAgent(
                    chat_client=chat_client,
                    instructions= self.agent_config.get("recommendation_message", ""),
                ) as agent:
                    response = await agent.run(f"Could you please provide a recommendation for the following entry: {json.dumps(entry)}")

                    logger.info(f"LLM response for entry {entry.get('name')} generated.")
                    return response.text.replace(chr(10), "<br>")
            except Exception as e:
                logger.error(f"Error during chat with Azure AI Projects agent: {e}")
                response = None

        return response if response else "No recommendation available."