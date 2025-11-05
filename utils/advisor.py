
import logging
import json
from pyexpat.errors import messages
import os, time
import yaml
from abc import abstractmethod
from dotenv import load_dotenv
from pathlib import Path
from dotenv import load_dotenv
from agent_framework import ChatAgent
from azure.identity import DefaultAzureCredential
from azure.ai.projects import AIProjectClient

load_dotenv()

logger = logging.getLogger("ms_agent")
logger.setLevel(os.getenv("LOG_LEVEL", "DEBUG"))

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
        chat_client = chat_client.new_chat_client()

        config_file = Path("llm_system_prompt_config.yaml")
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

    async def get_recommendation(self, entry: dict) -> str:
        """Use an Azure-specific LLM to generate a short recommendation based on status or error."""
        logger.info(f"Generating recommendation for failed entry {entry.get('name')} using LLM...")

        # Initialize the AIProjectClient
        project_client = AIProjectClient(
            endpoint= self.project_endpoint,
            credential=DefaultAzureCredential()
        )

        with project_client:
            # Create an agent with custom functions
            agent = project_client.agents.get_agent(
                agent_id="asst_qj2okXz6T2JNRtTrHlQWkw5v"
            )

            # Create a thread for communication
            thread = project_client.agents.threads.create()
            message = project_client.agents.messages.create(
                thread_id=thread.id,
                role="user",
                content=f"""
                Could you provide a short grounded recommendation based on the knowledge base for 
                the following failure.
                Try to keep the recommendation under 100 words.
                Try to find the relevant information based on the system or resource name.
                Enumerate all the information you find in the section `Recommended Action`.
                Entry details:{json.dumps(entry)}
                """
            )

            # Create and process a run for the agent to handle the message
            run = project_client.agents.runs.create(thread_id=thread.id, agent_id=agent.id)

            # Poll the run status until it is completed or requires action
            while run.status not in ["completed"]:
                time.sleep(1)
                run = project_client.agents.runs.get(thread_id=thread.id, run_id=run.id)
 
            # Fetch and log all messages from the thread
            messages = project_client.agents.messages.list(thread_id=thread.id)
            for message in messages:
                logger.debug(f"Role: {message['role']}, Content: {message['content']}")
                if message['role'] == 'assistant':
                    response = message['content'][0]
                    break

        logger.info(f"LLM response for failed entry {entry.get('name')} generated.")
        if response and response.text and response.text.value:
            return response.text.value.replace("\n", "<br>")