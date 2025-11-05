from azure.monitor.querymetrics import MetricsClient, MetricAggregationType
from datetime import timedelta
from dotenv import load_dotenv
import logging
import os

load_dotenv()
logger = logging.getLogger(__name__)
logger.setLevel(os.getenv("LOG_LEVEL", "INFO"))

thresholds = [
    (72, timedelta(hours=1)),
    (25, timedelta(minutes=30)),
    (0,  timedelta(minutes=5)), 
]

class AzureMetricsClient:
    def __init__(self, credential):
        self.credential = credential
        self.metrics_client = MetricsClient(endpoint="https://australiaeast.metrics.monitor.azure.com", credential=credential, api_version="2024-02-01" )

    def _get_namespace_by_resource(self, resource_id: str) -> str:
        if "Microsoft.Web/sites" in resource_id:
            return "Microsoft.Web/sites"
        elif "Microsoft.DataFactory/factories" in resource_id:
            return "Microsoft.DataFactory/factories"
        elif "Microsoft.Logic/workflows" in resource_id:
            return "Microsoft.Logic/workflows"
        
        return "Default"

    def get_metrics(self, resource_id, hours: int, metric_name:str = "Http2xx", aggregation: str = "Count") -> dict:
        resource_ids = [resource_id]

        if resource_id is None or "https?://" in resource_id:
            logger.error("Resource ID is required to fetch metrics.")
            return
        
        try:
            timeGrain = next(val for th, val in thresholds if hours >= th)
            metric_ns = self._get_namespace_by_resource(resource_id)

            aggregation = aggregation.capitalize()
            if aggregation == "Sum":
                aggregation = "Total"

            result = self.metrics_client.query_resources(
                resource_ids=resource_ids,
                metric_namespace=metric_ns,
                metric_names=[metric_name],
                timespan=timedelta(hours=hours),
                granularity=timeGrain,
                aggregations=[MetricAggregationType(aggregation)],
            )

            metric_values: list = result[0].metrics[0].timeseries[0].data
            metric_values_as_dict = [vars(mv) for mv in metric_values]
                
            response = {
                "name": f"{aggregation} of {metric_name} over last {hours} hours",
                "type": "azureMonitor",
                "timeseries": metric_values_as_dict,
                "message": f"Metrics data.",
            }

            logger.info(f"Retrieved metrics series for {resource_id}.")
            return response
        except Exception as e:
            logger.error(f"Error retrieving metrics for {resource_id}: {e}")
            return {"error": str(e)}
        
if __name__ == "__main__":
    from azure.identity import DefaultAzureCredential

    credential = DefaultAzureCredential()
    client = AzureMetricsClient(credential=credential)
    resource_id = "/subscriptions/de93eb29-7b3a-415b-9be0-adbf6ddcf73b/resourceGroups/assessmentlearning-dapdataexchange-prod/providers/Microsoft.DataFactory/factories/adf-dap-prd"
    metrics_data = client.get_metrics(resource_id=resource_id, hours=24, metric_name="PipelineSucceededRuns", aggregation="Count")
    print(metrics_data)