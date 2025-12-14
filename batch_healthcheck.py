# Copyright (c) Punta Negra PTY. All rights reserved.
# Licensed under the MIT License. See LICENSE in the project root for license information.

from datetime import datetime
import logging
import os
import json
import asyncio

from dotenv import load_dotenv
from azure.identity import DefaultAzureCredential
from tools.dashboard_client import AzureDashboardUpdater
from tools.jira_client import JiraTicketManager
from tools.tools import perform_healthcheck_from_file
from tools.logic_apps_client import LogicAppService
from tools.update_healthcheck_excel import UpdateHealthCheckExcel
from utils.json_to_markdown import MarkdownReport
from utils.advisor import AzureAgentAdvisor, SimpleLlmAdvisor

load_dotenv()

"""
This script runs the health check in batch mode and updates the dashboard.
"""

agent_logger = logging.getLogger("ms_agent")
agent_logger.setLevel(os.getenv("LOG_LEVEL", "DEBUG"))

async def batch_healthcheck() -> None:
    """Run the health check in batch mode and update the dashboard."""
    agent_logger.info("Running health check in batch mode...")

    credential = DefaultAzureCredential()
    advisor = AzureAgentAdvisor()
    report = MarkdownReport()
    jira_manager = JiraTicketManager(url=os.getenv("JIRA_SERVER_URL"), 
                                     user=os.getenv("JIRA_API_USER"), 
                                     token=os.getenv("JIRA_API_TOKEN"))

    results = perform_healthcheck_from_file("./data/Inventory.csv")

    try:
        await advisor.recommend(results)
    except Exception as e:
        agent_logger.error(f"Error during LLM recommendation: {e}")

    try:
        healthcheckWorkbookHandler = UpdateHealthCheckExcel(excel_file=os.getenv("HEALTHCHECK_EXCEL_FILE_PATH"))
        healthcheckWorkbookHandler.update_sheet(results)
    except Exception as e:
        agent_logger.error(f"Error updating health check Excel sheet: {e}")

    # try:
    #     await jira_manager.create_tickets(results)
    # except Exception as e:
    #     agent_logger.error(f"Error during JIRA ticket creation: {e}")

    try:
        markdown_output = await report.to_markdown(results)
        dashboardManager = AzureDashboardUpdater(credential=credential,
            subscription_id=os.getenv("DASHBOARD_SUBSCRIPTION_ID"),
            resource_group=os.getenv("DASHBOARD_RESOURCE_GROUP"),
            dashboard_uuid=os.getenv("DASHBOARD_ID")
        )

        dashboardManager.update_markdown(
            new_content=markdown_output,
            markdown_title=f"Integration Health Check Summary",
            subtitle=f"Last Updated: {datetime.now().strftime('%Y-%m-%d %H:%M UTC')}",
        )
    except Exception as e:
        agent_logger.error(f"Error generating markdown report: {e}")

    agent_logger.info("✅ Health check completed successfully.")

if __name__ == "__main__":
    asyncio.run(batch_healthcheck())    
