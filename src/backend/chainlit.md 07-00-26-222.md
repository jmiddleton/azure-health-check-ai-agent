# Integration Health Check Agent

The Integration Health Check Agent provides automated monitoring, health checking, and reporting for critical Punta Negra integration services. Automate repetitive tasks and improve incident response using the Integration’s knowledge base. 
It uses AI-assisted analysis to identify issues, summarize failures, and recommend actionable fixes across Azure services.

The LLM model used currently is gpt-oss:20b running on Ollama.
---

## Overview

The **AI Agent** monitors Azure resources, detects anomalies, and uses AI to suggest recommendations to fix the issues. It supports natural language commands and interoperates with tools like Azure SDK and Azure Management API.

It uses the **Microsoft Agent Framework** and **OpenAI (or Ollama)** for status analysis and report generation.

### Key Responsibilities
- Read integration inventory from an Excel or CSV file (e.g., `DailyHealthCheck.csv`).
- Filter entries by responsible engineer or all (e.g., `Peter`).
- Perform health checks for each resource:
  - Azure Data Factory (ADF)
  - Azure Logic Apps
  - App Insights
  - Azure Monitor
- Summarize status results and identify failed components.
- Extract and interpret error details from failed Logic App runs.
