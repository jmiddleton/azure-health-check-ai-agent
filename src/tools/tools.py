# Copyright (c) Punta Negra. All rights reserved.
# Licensed under the MIT License. See LICENSE in the project root for license information.

import os
import re
import json
import logging

from typing import Annotated, Optional, Union
from pydantic import Field
from urllib.parse import unquote
from time import time
from tools.adf_client import ADFService
from tools.app_insights_client import AppInsightsFailureChecker
from tools.dashboard_client import AzureDashboardUpdater
from tools.resource_finder import AzureResourceFinder
from tools.excel_handler import ExcelReaderWriter
from tools.logic_apps_client import LogicAppService
from tools.metrics_client import AzureMetricsClient
from tools.jira_client import JiraTicketManager
from utils.advisor import AzureAgentAdvisor
from concurrent.futures import ThreadPoolExecutor, as_completed
from azure.identity import DefaultAzureCredential

logger = logging.getLogger("tools_agent")
logger.setLevel(os.getenv("LOG_LEVEL", "INFO"))

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

# Initialize Azure Default Credential
credential = DefaultAzureCredential()
resource_finder = AzureResourceFinder(credential)
advisor = AzureAgentAdvisor()
jira_client = JiraTicketManager(url=os.getenv("JIRA_SERVER_URL"), 
                                     user=os.getenv("JIRA_API_USER"), 
                                     token=os.getenv("JIRA_API_TOKEN"))

# Initialize tools
# ---------------- AI Function Tools ----------------
def raise_jira_ticket(
    health_check_result: Annotated[Union[dict, str], Field(description="The health check result of a resource.")]
) -> dict:
    """
    Raises a JIRA ticket when a failure is detected.
    Takes a structured health_check_result dictionary describing the resource health status,
    including fields such as 'system', 'name', 'type', 'status', 'error', and 'results'.
    """

    if isinstance(health_check_result, str):
        try:
            health_check_result = json.loads(health_check_result)
        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON string provided for health_check_result. {e}")
            health_check_result = {"raw_text": health_check_result}
            
    return jira_client.create_tickets([health_check_result])

def get_metrics(
    resource_name: Annotated[str, Field(description="The resource name.")],
    hours: Annotated[Optional[int], Field(description="The number of hours to filter metrics.")] = 24,
    metric_name: Annotated[Optional[str], Field(description="The name of the metric to retrieve.")] = "Http2xx",
    aggregation: Annotated[Optional[str], Field(description="The aggregation type for the metric.")] = "Count"
) -> dict:
    """Retrieve metrics from Azure Monitor."""

    if resource_name:
        resource_id = resource_finder.find_resource_by_name(resource_name, None)
        logger.info(f"Resource ID found: {resource_id}")

        if resource_id:
            resource_id = resource_id.replace("https://portal.azure.com/#@puntanegra.edu.au/resource", "")
            metrics_client = AzureMetricsClient(credential)
            return metrics_client.get_metrics(resource_id, hours=hours, metric_name=metric_name, aggregation=aggregation)

    return {"error": "Resource not found."}

def healthcheck_app_insights(
    url: Annotated[str, Field(description="The URL of the Application Insights resource to check.")],
) -> str:
    """Check the status of an Application Insights resource."""
    app_insights_service = AppInsightsFailureChecker(credential)

    if APP_INSIGHTS_PROVIDER in url.lower():
        subscription_id, resource_group, resource_name = _get_resource_details_from_url(url)
        logger.info(f"Checking Application Insights status of: {resource_name}")

        status = app_insights_service.get_failures_last_hours(subscription_id, resource_group, resource_name, hours=24, system="")
    else:
        status = "Unsupported URL or Missing Provider"
    return status

def get_timeseries(
    url: Annotated[str, Field(description="The URL of the Application Insights resource to check.")],
    failed_requests: Annotated[Optional[bool], Field(description="Whether to retrieve failed requests or not.")] = True,
    hours: Annotated[Optional[int], Field(description="The number of hours to retrieve the time series for.")] = 24
) -> dict:
    """Retrieve time series from Application Insights."""
    app_insights_service = AppInsightsFailureChecker(credential)

    if APP_INSIGHTS_PROVIDER in url.lower():
        subscription_id, resource_group, resource_name = _get_resource_details_from_url(url)
        logger.info(f"Retrieving requests time series for: {resource_name}")

        status = app_insights_service.get_timeseries(subscription_id, resource_group, resource_name, hours=hours, failed_requests=failed_requests)
    else:
        status = {"error": "Unsupported URL or Missing Provider"}
    return status

def find_resource_by_name(
    resource_name: Annotated[str, Field(description="The name of the resource to find.")],
    resource_group: Annotated[Optional[str], Field(description="The resource group to search within (optional).", default=None)] = None,
) -> str:
    """Finds an Azure resource by name and resource group (optional)."""

    logger.info(f"Searching for: {resource_name} in rg: {resource_group}")
    resource_id = resource_finder.find_resource_by_name(resource_name, resource_group)

    logger.info(f"Resource ID found: {resource_id}")
    if resource_id:
        return {"url": resource_id}
    return {"url": None}

def list_resources(
    resource_type: Annotated[str, Field(description="The type of resources to list (e.g., 'ApiManagement', 'Web', 'Logic', 'Function', 'ServiceBus', 'DataFactory').")],
    resource_group: Annotated[Optional[str], Field(description="The resource group to filter by (optional).", default=None)] = None,
) -> list[dict]:
    """Lists Azure resources of a specific type, optionally filtered by resource group.
    
        The resource_type parameter should correspond to Azure resource providers, such as:
        Microsoft.Compute → Virtual Machines 
        Microsoft.Storage → Storage 
        Microsoft.Network → Application Gateway, Virtual Network, etc. 
        Microsoft.KeyVault → Key Vault 
        Microsoft.Sql → Azure SQL Database 
        Microsoft.CosmosDB (listed as Microsoft.DocumentDB) → Azure Cosmos DB 
        Microsoft.EventHub → Event Hubs 
        Microsoft.ServiceBus → Service Bus 
        Microsoft.ApiManagement → API Management 
        Microsoft.DevOpsInfrastructure → Managed DevOps Pools 
        Microsoft.AzureArcData → Azure Arc-enabled data services 
        Microsoft.MachineLearningServices → Azure Machine Learning 
        Microsoft.DataFactory → Data Factory 
        Microsoft.StorageSync → Storage Sync 
        Microsoft.Web → App Service
    """

    logger.info(f"Listing resources of type: {resource_type} in rg: {resource_group}")
    resources = resource_finder.list_resources_by_type(resource_type, resource_group)

    logger.info(f"Number of resources found: {len(resources)}")
    return resources

def healthcheck_adf(
    url: Annotated[str, Field(description="The URL of the ADF pipeline to check.")],
) -> str:
    """Checks the status of an Azure Data Factory pipeline."""
    
    adf_service = ADFService(credential)

    if ADF_PROVIDER in url.lower():
        subscription_id, resource_group, resource_name = _get_resource_details_from_url(url)
        logger.info(f"Checking ADF status of: {resource_name}")

        status = adf_service.health_check(subscription_id, resource_group, resource_name, url)
    else:
        status = "Unsupported URL or Missing Provider"
    return status


def update_dashboard(result_summary: Annotated[str, Field(description="The summary of health check results to post to the dashboard. The summary is in Markdown format.")]) -> None:
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
    return "Dashboard updated successfully."

def healthcheck_logic_app(
    url: Annotated[str, Field(description="The URL of the Logic App to check.")],
) -> str:

    """Check the status of an Azure Logic App."""
    logic_app_service = LogicAppService(credential)

    if LOGIC_APP_PROVIDER in url.lower():
        subscription_id, resource_group, resource_name = _get_resource_details_from_url(url)
        logger.info(f"Checking LogicApp status of: {resource_name}")

        status = logic_app_service.health_check(subscription_id, resource_group, resource_name, url)
    else:
        status = "Unsupported URL or Missing Provider"
    return status

# Main health check function
def perform_healthcheck_from_file(
    file_path: Annotated[str, Field(description="Path to the CSV file to check.")],
    responsible: Annotated[Optional[str], Field(description="The name of the responsible person (optional).", default=None)] = None,
) -> list[dict]:
    """Performs a full platform health check using the specified CSV file."""
     
    logger.info(f"Initializing health check for {responsible}'s entries...")
    
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
            try:
                res = future.result()
                if res:
                    results.append(res)
            except Exception as e:
                logger.error(f"Error processing row: {e}")

    logger.info(f"Health check completed with {len(results)} results.")

    # Sort results by idx and save to file for debugging
    sorted_results = sorted(results, key=lambda x: int(x.get("idx", 0)))
    with open(f"output{time()}.json", "w") as f:
        json.dump(sorted_results, f, indent=2)

    return sorted_results

async def perform_healthcheck() -> list[dict]:
    """Performs a full health of the integration platform."""
    results= perform_healthcheck_from_file("DailyHealthCheck.csv")
    
    try:
        await advisor.recommend(results)
    except Exception as e:
        logger.error(f"Error during LLM recommendation: {e}")

    return results

# ---------------- END AI Function Tools ----------------
    
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
    idx = str(row.name)  # Get the index of the row
    system = str(row.get("System", "")).strip()
    subscription_id, resource_group, resource_name = _get_resource_details_from_url(url)

    result = {
            "system": system,
            "idx": idx,
            "name": resource_name,
            "rgroup": resource_group,
            "type": "unknown",
            "status": "Unsupported URL",
            "error": None
        }
    
    logger.info(f"Checking status of: {resource_name}")

    if not subscription_id or not resource_group or not resource_name:
        result["status"] = "Invalid URL"
        result["error"] = f"Invalid or missing URL: {str(row.get('System', ''))}"
        return result

    # Call health check
    if ADF_PROVIDER in url.lower():
        adf_service = ADFService(credential)
        result = adf_service.health_check(subscription_id, resource_group, resource_name, url, system)
    elif LOGIC_APP_PROVIDER in url.lower():
        logic_app_service = LogicAppService(credential)
        result = logic_app_service.health_check(subscription_id, resource_group, resource_name, url, system)
    elif APP_INSIGHTS_PROVIDER in url.lower():
        app_insights_service = AppInsightsFailureChecker(credential)
        result = app_insights_service.get_failures_last_hours(subscription_id, resource_group, resource_name, hours=24, system=system)

    if result:
        result["idx"] = idx

    logger.info(f"Status checked of: {resource_name} is {result.get('status', 'Unknown')}")
        
    return result
