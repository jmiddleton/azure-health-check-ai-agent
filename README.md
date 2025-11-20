# AI Agent for Daily Azure Health Checks

This project implements an **AI agent** that performs **daily health checks** across key Azure integration resources — including **Azure Data Factory (ADF)** pipelines and **Logic Apps**.  

It is designed to automatically detect issues, summarize system health, and provide actionable insights or recommendations for remediation.

---

## Overview

The **AI Agent** monitors Azure resources, detects anomalies, and uses AI to suggest recommendations to fix the issues. It supports natural language commands and interoperates with tools like Azure SDK and Azure Management API.

It uses the **Microsoft Agent Framework** and **OpenAI (or Ollama)** for status analysis and report generation.

### Key Responsibilities
| **Capability** | **Description** |
|-----------------|-----------------|
| **Automated Health Checks** | Periodically verifies the operational status of Azure Data Factory pipelines, Logic Apps, App Insights, and API integrations. Configurable via scheduler. |
| **Intelligent Error Analysis** | Uses LLM to summarize failure messages, filter known/expected issues, and suggest resolutions. |
| **Batch File Processing** | Reads health check definitions from CSV or Excel files to perform health checks on multiple resources. |
| **Adaptive Filtering** | Automatically ignores pre-defined false/positive issues. |
| **MCP Server Support** | Exposes tools and monitoring functions through an MCP (Model Context Protocol) interface, enabling LLM-assisted orchestration. |
| **Automated Incident Response (Planned)** | Automatically respond to Azure Monitor alerts. |
| **Integration with Jira** | Automatically raises Jira tickets when an issue is detected on one of the Integration services. Alternatively, the user can ask to raise a ticket for a failed service. |
| **Spreadsheet Update** | Updates the shared Excel file daily with success or failure. |
| **Report Summary** | Publishes report summary to Azure Dashboard. |
| **Metrics Visualization** | Integration with Azure Monitor Metrics to query for metrics using plain language|
| **Chatbot** | Provides a chatbot to allow users to ask plain-language questions about Azure resources and health. |
| **Authentication** | Authentication is required to access the chatbot. |
| **Chat History** | Allows storage and retrieval of previous conversations. |

---

## Architecture

This solution deploys a web-based chat application with an AI agent running in Azure Container App.

The agent leverages the Azure AI Agent service with knowledge about issues and recommendations, enabling it to generate responses with citations. The solution also includes built-in monitoring capabilities with tracing to ensure easier troubleshooting and optimized performance.

This solution creates an Azure AI Foundry project.

![Architecture diagram showing that user input is provided to the Azure Container App, which contains the chat UI. With user identity and resource access through managed identity, the input is used to form a response. The input and the Azure monitor are able to use the Azure resources deployed in the solution: Application Insights, Azure AI Foundry Project, Azure AI Services, Storage account, Azure Container App, and Log Analytics Workspace.](/images/architecture.png)

The app code runs in Azure Container App to process the user input and generate a response to the user. It leverages Azure AI projects and Azure AI services, including the model and agent.

| **Category** | **Description** |
|---------------|-----------------|
| **Azure AI Foundry** | Provides a workspace for AI development with access to models e.g.: `gpt-4o-mini`, data, and compute resources |
| **Azure Storage Account** | Provides blob storage for application data and file uploads |
| **Azure Container App** | Hosts and scales the web application with serverless containers |
| **Log analytics** | Collects and analyzes telemetry data for monitoring and troubleshooting |
| **Application Insights** | Provides application performance monitoring, logging, and telemetry for debugging and optimization |
| **Language & Frameworks** | Python with FastAPI, FastMCP, and Azure SDKs (`azure-identity`, `azure-mgmt-*`). |
| **AI Agent Platform** | Microsoft Agent Framework for building, orchestrating, and deploying AI agents. |
| **Chat UI** | Chainlit provides the web-based chat interface. |


### Security

The Azure Health Check Agent uses a flexible model for managing roles and access management based on Azure RBAC.

#### Agent permissions
The Azure Health Check Agent has its own user assigned managed identity that gives the agent the required credentials to act on your behalf as it manages assigned resource groups. You have full control over the roles and permissions applied to this managed identity.

The agent's managed identity is preconfigured with the following role assignments for a managed resource group:
  - Log Analytics Reader
  - Monitoring Reader

The Agent uses the following security mechanisms:

| **Category** | **Description** |
|---------------|-----------------|
| **Authentication** | Uses Microsoft Entra ID via `az login` or Managed Identity for secure API access. |
| **Token Management** | Session-scoped tokens. |
| **Local LLM (Ollama)** | Runs `gpt-oss` locally, keeping data private and compliant. |
| **RBAC Enforcement** | Access limited to resources authorized under the user’s Azure role. |
| **Read-only Access** | Tools only read data (no modification of resources). |
| **Thread Context Control** | Conversation context is limited to per-thread sessions. |
| **Subscription Scope** | Access restricted to specific Azure subscriptions. |
| **No PII Information** | No personally identifiable information is processed or stored. |
| **Chat UI Authentication** | The chat interface requires user authentication before access. |

---

## Running the Agent

### Install Dependencies

Go to the source folder `cd src/backend`

`uv sync --prerelease=allow`
`source ./.venv/bin/activate`

### Authenticate with Azure

`az login`

### Run the Agent

1. Chatbot
  - Production: `./.venv/bin/chainlit run chat_server.py` or `uv run chat_server.py`

2. Batch Mode
  - `uv run .\batch_healthcheck.py`

3. MCP Server
  - `fastmcp run mcp_server.py:mcp --transport http --port 9000 --host 0.0.0.0`

To use MCP Inspector, in a command windows execute the following command: `npx @modelcontextprotocol/inspector`

### Deployment

  - Login into Azure `azd auth login`
  - Run the following commands in the terminal: `azd up`
  - Follow the prompts to select your Azure subscription and region
  - Wait for deployment to complete (5-20 minutes) - you'll get a web app URL when finished

## Prompt examples

Hi, what can you help me with?

Please perform a full health check for entries.

Which Azure resource is unhealthy?

Can I get the metrics of PipelineSucceededRuns for adf-puntanegra-dev?

Can I get the count of HTTP 5xx errors for the last 7 days for function app fn-puntanegra-dev?

Could you check the health of adf-puntanegra-dev, and if the status is failed, create a Jira ticket?

Could you check the health of adf-puntanegra-dev?

Can you provide the health check for all the Azure Data Factory we have in the configuration file DailyHealthCheck.csv?

Why is web-puntanegra-dev not working?

Can you check the health of web-puntanegra-dev?

Can I get the chart for pipeline failed runs metrics for web-puntanegra-dev for the last 7 days?