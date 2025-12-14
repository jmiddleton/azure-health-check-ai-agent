import os, time
from azure.identity import DefaultAzureCredential
from azure.ai.projects import AIProjectClient
from azure.ai.agents.models import FunctionTool
import json
import datetime
from typing import Any, Callable, Set, Dict, List, Optional
from dotenv import load_dotenv

load_dotenv()
    
# Start by defining a function for your agent to call. 
# When you create a function for an agent to call, you describe its structure 
# with any required parameters in a docstring.


def fetch_weather(location: str) -> str:
    """
    Fetches the weather information for the specified location.

    :param location: The location to fetch weather for.
    :return: Weather information as a JSON string.
    """
    # Mock weather data for demonstration purposes
    mock_weather_data = {"New York": "Sunny, 25°C", "London": "Cloudy, 18°C", "Tokyo": "Rainy, 22°C"}
    weather = mock_weather_data.get(location, "Weather data not available for this location.")
    return json.dumps({"weather": weather})

# Define user functions
user_functions = {fetch_weather}

# Retrieve the project endpoint from environment variables
project_endpoint = os.environ["AZURE_PROJECT_ENDPOINT"]
model_name = os.environ["AZURE_OPENAI_CHAT_DEPLOYMENT_NAME"]
# Initialize the AIProjectClient
project_client = AIProjectClient(
    endpoint=project_endpoint,
    credential=DefaultAzureCredential()
)

# Initialize the FunctionTool with user-defined functions
functions = FunctionTool(functions=user_functions)

with project_client:
    # Create an agent with custom functions
    agent = project_client.agents.get_agent(
        agent_id="asst_qj2okXz6T2JNRtTrHlQWkw5v"
    )

    # Create a thread for communication
    thread = project_client.agents.threads.create()
    print(f"Created thread, ID: {thread.id}")

    # Send a message to the thread
    message = project_client.agents.messages.create(
        thread_id=thread.id,
        role="user",
        content="""Could you provide a short grounded recommendation based on the knowledge base for the following failure.
                Try to keep the recommendation under 100 words.
                Try to find the relevant information based on the system or resource name.
                Enumerate all the information you find in the section `Recommended Action`.
                The failure occurred in resource ADF `adf-dap-prd` 
                Error: - pl_results_sync_managmnt: Failed
                - cp_astra_child_graded_cands_map_multiple_jsonstocsv: ErrorCode=UserErrorSourceBlobNotExist,
                'Type=Microsoft.DataTransfer.Common.Shared.HybridDeliveryException,Message=The required Blob is missing.
                Folder path: dap/resuls/InpseraAllResults/f22a784c-6d39-4430-b59a-20ff04b0991c/testTrans/.,
                Source=Microsoft.DataTransfer.ClientLibrary,'""",
    )
    print(f"Created message, ID: {message['id']}")

    # Create and process a run for the agent to handle the message
    run = project_client.agents.runs.create(thread_id=thread.id, agent_id=agent.id)
    print(f"Created run, ID: {run.id}")

    # Poll the run status until it is completed or requires action
    while run.status in ["queued", "in_progress", "requires_action"]:
        time.sleep(1)
        run = project_client.agents.runs.get(thread_id=thread.id, run_id=run.id)

    print(f"Run completed with status: {run.status}")

    # Fetch and log all messages from the thread
    messages = project_client.agents.messages.list(thread_id=thread.id)
    for message in messages:
        if message['role'] == 'assistant':
            response = message['content'][0]
            print(f"Role: {message['role']}, Content: {response.text.value}")
        
        # for citation in message.get('file_citation_annotations', []):
        #     print(f"Citation: {citation}")

    print("All messages in the thread have been logged.")