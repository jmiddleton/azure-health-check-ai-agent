# AI Agent for Daily Azure Health Checks

This project implements an **AI agent** designed to monitor, analyze, and report the operational health of Azure resources.
It connects to observability data (Azure Monitor, Application Insights, and Logic Apps), automates diagnostics, and streamlines incident management. Automate repetitive tasks and improve incident response using the Integration’s knowledge base. 
It uses AI-assisted analysis to identify issues, summarize failures, and recommend actionable fixes across Azure services.

---

## Overview

The **AI Agent** monitors Azure resources, detects anomalies, and uses AI to suggest recommendations to fix the issues. It supports natural language commands and interoperates with tools like Azure SDK and Azure Management API.

It uses the **Microsoft Agent Framework** and **OpenAI (or Ollama)** for status analysis and report generation.

### Key Responsibilities

  - Automated Health Checks: Periodically verifies the operational status of Azure Data Factory pipelines, Logic Apps, App Insights and API integrations. Configurable via scheduler.
  - Intelligent Error Analysis: Uses LLM to summarize failure messages, filter known/expected issues, and suggest resolutions.
  - Batch File Processing: Reads health check definitions from CSV, or Excel files to perform health check of multiple resources.
  - Adaptive Filtering: Automatically ignores pre-defined false/positive issues.
  - MCP Server Support: Exposes tools and monitoring functions through an MCP (Model Context Protocol) interface, enabling LLM-assisted orchestration.
  - Integration with Jira: Automatically raise Jira tickets when an issue is detected on one of the Integration services. Alternatively, the user can ask to raise a ticket on a failure service.
  - Report Summary: Publish report summary to Azure Dashboard
  - Metrics Visualization: Integration with Azure Monitor Metrics to query for metrics using plain language e.g. 


---

## Architecture

  - LLM: Runs locally on Ollama with model gpt-oss:20b, but can also use OpenAI or other models.
  - Language & Frameworks: Python with FastAPI, FastMCP, and Azure SDKs (azure-identity, azure-mgmt-*).
  - AI Agent Platform: Microsoft Agent Framework for building, orchestrating, and deploying AI agents.
  - Chat UI: Chainlit provides the web-based chat interface.

---

## Running the Agent

### Install Dependencies

`uv sync`

### Authenticate with Azure

`az login`

### Run the Agent

1. Chatbot
  - `uv run chat_server.py -w`

2. Batch Mode
  - `uv run .\batch_healthcheck.py`

3. MCP Server
  - `fastmcp run mcp_server.py:mcp --transport http --port 9000 --host 0.0.0.0`

To use MCP Inspector, in a command windows execute the following command: `npx @modelcontextprotocol/inspector`

## Prompt examples

```
Hi, what can you help me with?

Please perform a full health check for entries.

Which Azure resource is unhealthy?

Can I get the metrics of PipelineSucceededRuns for my-logicapp-au-prod01?

Can I get the count of HTTP 5xx errors for the last 7 days for function app myfunction-app-au-prod01?

Can I get the chart for pipeline failed runs metrics for my-logicapp-au-prod01 for the last 7 days?
```
