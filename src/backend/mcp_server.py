# mcp_healthcheck_server.py

import logging
import os
import re

import mcp

from fastmcp import FastMCP
from azure.identity import DefaultAzureCredential

from concurrent.futures import ThreadPoolExecutor, as_completed
from dotenv import load_dotenv
from urllib.parse import unquote

from tools.adf_client import ADFService
from tools.app_insights_client import AppInsightsFailureChecker
from tools.dashboard_client import AzureDashboardUpdater
from tools.resource_finder import AzureResourceFinder
from tools.excel_handler import ExcelReaderWriter
from tools.logic_apps_client import LogicAppService

load_dotenv()
agent_logger = logging.getLogger("ms_agent")
agent_logger.setLevel(os.getenv("LOG_LEVEL", "INFO"))

# Example log
agent_logger.debug("Initializing agent...")

# Initialize Azure Default Credential
credential = DefaultAzureCredential()

ADF_PROVIDER="microsoft.datafactory"
LOGIC_APP_PROVIDER="microsoft.logic"
APP_INSIGHTS_PROVIDER="microsoft.insights"

# URL patterns for resource extraction
url_patterns = {
    ADF_PROVIDER: re.compile(
    r".*subscriptions/([^/]+)/resourceGroups/([^/]+)/providers/Microsoft\.DataFactory/factories/([^/]+)", re.IGNORECASE
),
    LOGIC_APP_PROVIDER: re.compile(
    r".*subscriptions/([^/]+)/resourceGroups/([^/]+)/providers/Microsoft\.Logic/workflows/([^/?]+)", re.IGNORECASE
),
    APP_INSIGHTS_PROVIDER: re.compile(
    r".*subscriptions/([^/]+)/resourceGroups/([^/]+)/providers/Microsoft\.Insights/components/([^/?]+)", re.IGNORECASE
),
}

mcp = FastMCP(
    "Streamable HTTP: Stateless Server",
    stateless_http=True,
    json_response=True
)

# ---------------- AI Function Tools ----------------
@mcp.tool()
def healthcheck_app_insights_tool(
    url: str
) -> dict:
    """Check the status of an Application Insights resource."""
    app_insights_service = AppInsightsFailureChecker(credential)

    if APP_INSIGHTS_PROVIDER in url.lower():
        subscription_id, resource_group, resource_name = _get_resource_details_from_url(url)
        agent_logger.info(f"Checking Application Insights status of: {resource_name} in rg: {resource_group}")

        status = app_insights_service.get_failures_last_hours(subscription_id, resource_group, resource_name, hours=24, system="")
    else:
        status = {
            "result": {
                "type": "error",
                "status": "Failed",
                "message": "Unsupported URL or Missing Provider"
            }
        }
    return status

@mcp.tool()
def find_resource_by_name_tool(
    resource_name: str,
    resource_group: str = None,
) -> dict:
    """Find an Azure resource by name."""

    agent_logger.info(f"Searching for: {resource_name} in rg: {resource_group}")
    resource_finder = AzureResourceFinder(credential)
    resource_id = resource_finder.find_resource_by_name(resource_name, resource_group)

    agent_logger.info(f"Resource ID found: {resource_id}")

    return {
        "result": {
            "url": resource_id
        }
    }

@mcp.tool()
def healthcheck_adf_tool(url: str) -> dict:
    """Check the status of an ADF pipeline."""
    
    adf_service = ADFService(credential)

    if ADF_PROVIDER in url.lower():
        subscription_id, resource_group, resource_name = _get_resource_details_from_url(url)
        agent_logger.info(f"Checking ADF status of: {resource_name} in rg: {resource_group}")

        status = adf_service.health_check(subscription_id, resource_group, resource_name, url)
        return {"result": status}
    else:
        return {
            "result": {
                "type": "error",
                "status": "Failed",
                "message": "Unsupported URL or Missing Provider"
            }
        }

@mcp.tool()
def update_dashboard(result_summary: str) -> dict:
    """Update an Azure Dashboard with the Report Summary."""
    dashboardManager = AzureDashboardUpdater(
            credential= credential,
            subscription_id=os.getenv("DASHBOARD_SUBSCRIPTION_ID"),
            resource_group=os.getenv("DASHBOARD_RESOURCE_GROUP"),
            dashboard_uuid=os.getenv("DASHBOARD_ID"),
        )

    dashboardManager.update_markdown(
        new_content=result_summary,
        markdown_title="Integration Health Check Summary",
    )
    return{
            "result": {
                "type": "error",
                "status": "Success",
                "message": "Dashboard updated successfully"
            }
        }

@mcp.tool()
def healthcheck_logic_app_tool(url: str) -> dict:

    """Check the status of an Azure Logic App."""
    logic_app_service = LogicAppService(credential)

    if LOGIC_APP_PROVIDER in url.lower():
        subscription_id, resource_group, resource_name = _get_resource_details_from_url(url)
        agent_logger.info(f"Checking LogicApp status of: {resource_name} in rg: {resource_group}")

        status = logic_app_service.health_check(subscription_id, resource_group, resource_name, url)
    else:
        status = {
                "type": "error",
                "status": "Failed",
                "message": "Unsupported URL or Missing Provider"
            }
    return status

@mcp.tool()
def perform_healthcheck_from_file_tool(
    file_path: str,
    responsible: str = None
) -> dict:
    """Performs a health check on all entries (or only those assigned to the given responsible) and returns a summary."""
    agent_logger.info(f"Initializing health check for {responsible}'s entries...")
    excel_handler = ExcelReaderWriter(file_path)
    entries = excel_handler.read_sheet()

    results = []
    with ThreadPoolExecutor(max_workers=10) as executor:
        future_to_row = {
            executor.submit(_process_row, row): row
            for _, row in entries.iterrows()
            if responsible is None or responsible.strip().lower() == row["Responsible"].lower()
        }

        for future in as_completed(future_to_row):
            res = future.result()
            if res:
                results.append(res)

    agent_logger.info(f"Health check completed with {len(results)} results.")

    return results

# Helper function to extract resource details from URL
# returns (subscription_id, resource_group, resource_name)
def _get_resource_details_from_url(url: str):
    match = None
    if not url or not url.startswith("http"):
        return None, None, None
    
    cleaned_url = unquote(url).strip()
    url_lower = url.lower()

    for key, pattern in url_patterns.items():
        if key in url_lower:
            match = pattern.match(cleaned_url)
            break
    else:
        return None, None, None
    
    return match.groups()

# Helper function to process each row
def _process_row(row):
    url = str(row.get("URL", "")).strip()
    system = str(row.get("System", "")).strip()
    subscription_id, resource_group, resource_name = _get_resource_details_from_url(url)
    agent_logger.info(f"Checking status of: {resource_name} in rg: {resource_group}")

    if not subscription_id or not resource_group or not resource_name:
        return {
            "system": system,
            "name": resource_name,
            "type": "unknown",
            "rgroup": resource_group,
            "status": "Invalid URL",
            "error": f"Invalid or missing URL: {str(row.get('System', ''))}"
        }

    # Call health check
    if ADF_PROVIDER in url.lower():
        adf_service = ADFService(credential)
        return adf_service.health_check(subscription_id, resource_group, resource_name, url, system)
    elif LOGIC_APP_PROVIDER in url.lower():
        logic_app_service = LogicAppService(credential)
        return logic_app_service.health_check(subscription_id, resource_group, resource_name, url, system)
    elif APP_INSIGHTS_PROVIDER in url.lower():
        app_insights_service = AppInsightsFailureChecker(credential)
        return app_insights_service.get_failures_last_hours(subscription_id, resource_group, resource_name, hours=24, system=system)
    else:
        return {
            "system": system,
            "name": resource_name,
            "rgroup": resource_group,
            "type": "unknown",
            "status": "Unsupported URL",
            "error": None
        }

if __name__ == "__main__":
    mcp.run(transport="streamable-http", host="0.0.0.0", port=9000)