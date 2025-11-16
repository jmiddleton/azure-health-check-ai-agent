
from azure.mgmt.resourcegraph import ResourceGraphClient
from azure.mgmt.resourcegraph.models import QueryRequest
from typing import Optional
from dotenv import load_dotenv
import logging
import os

load_dotenv()

logger = logging.getLogger(__name__)
logger.setLevel(os.getenv("LOG_LEVEL", "INFO"))

class AzureResourceFinder:
    """
    Search for an Azure resource by name across all subscriptions accessible via your login.
    """

    def __init__(self, credential):
        self.credential = credential
        self.client = ResourceGraphClient(credential)

    def find_resource_by_name(
        self, resource_name: str, resource_group: Optional[str] = None
    ) -> Optional[str]:
        """
        Search for a resource by name across all accessible subscriptions.
        If resource_group is specified, only search within that group.
        Returns the full resource ID (URL) if found, otherwise None.
        """

        if resource_group == "null":
            resource_group = None
            
        query = f"""
        resources
        | where name =~ '{resource_name}'
        {f"| where resourceGroup =~ '{resource_group}'" if resource_group else ""}
        | project name, type, resourceGroup, subscriptionId, location, id
        """

        subscription_ids = os.getenv("AZURE_SUBSCRIPTION_IDS")
        subs = subscription_ids.split(",") if subscription_ids else ["*"]

        request = QueryRequest(subscriptions=subs, query=query)
        response = self.client.resources(request)

        for r in response.data:
            return f"https://portal.azure.com/#@puntanegra.edu.au/resource{r['id']}"  # Return the first matching resource ID
        

    def list_resources_by_type(self, resource_type: str, resource_group: Optional[str] = None) -> list[dict]:

        """
        List all resources of a specific type across all accessible subscriptions.
        If resource_group is specified, only list resources within that group.
        Returns a list of resource details.
        """

        if resource_group == "null":
            resource_group = None

        if resource_type:
            resource_type = resource_type.strip()

        query = f"""
        resources
        | where type contains '{resource_type}'
        {f"| where resourceGroup =~ '{resource_group}'" if resource_group else ""}
        | project name, type, resourceGroup, subscriptionId, location, id
        """

        subscription_ids = os.getenv("AZURE_SUBSCRIPTION_IDS")
        subs = subscription_ids.split(",") if subscription_ids else ["*"]

        request = QueryRequest(subscriptions=subs, query=query)
        response = self.client.resources(request)

        results = []
        for r in response.data:
            results.append({
                "name": r["name"],
                "type": r["type"],
                "resourceGroup": r["resourceGroup"],
                "location": r["location"],
                "id": r["id"]
            })

        return results