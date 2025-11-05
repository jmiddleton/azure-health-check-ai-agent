from azure.monitor.query import LogsQueryClient, LogsQueryStatus
from datetime import timedelta
from dotenv import load_dotenv
import logging
import os
import json

from utils.json_to_markdown import MarkdownReport

load_dotenv()
logger = logging.getLogger(__name__)
logger.setLevel(os.getenv("LOG_LEVEL", "INFO"))

thresholds = [
    (48, "3h"),
    (24, "1h"),
    (12, "15m"),
    (0,  "5m"),   # default for anything >= 0
]

class AppInsightsFailureChecker:
    def __init__(self, credential):
        self.credential = credential
        self.logs_client = LogsQueryClient(credential=credential)
        self.markdownReport = MarkdownReport()

    def _query_app_insights(self, app_insights_id: str, query: str, timespan: timedelta = None):
        response = self.logs_client.query_resource(
            app_insights_id,
            query,
            timespan=timespan
        )
        
        if response.status == LogsQueryStatus.PARTIAL:
            return response.partial_data
        elif response.status == LogsQueryStatus.SUCCESS:
            return response.tables[0]
        else:
            return None

    def get_failures_last_hours(self, subscription_id: str, resource_group: str, resource_name: str, hours: int, system: str) -> dict:
        app_insights_id=f"/subscriptions/{subscription_id}/resourceGroups/{resource_group}/providers/microsoft.insights/components/{resource_name}"

        query = """
        requests
        | where timestamp > ago(7d)
        | where success == false
        | summarize FailedCount = count() by bin(timestamp, 1d)
        | order by timestamp asc
        """

        table = self._query_app_insights(app_insights_id= app_insights_id, query=query)

        if table is None:
            logger.error(f"Failed to retrieve logs for Application Insights {resource_name}.")
            return {
                "system": system,
                "name": resource_name,
                "type": "appInsights",
                "rgroup": resource_group,
                "status": "Unknown",
                "results": []
            }

        daily_counts = [row["FailedCount"] for row in table.rows]

        if not daily_counts:
            status = "Succeeded"
            last_day_count = 0
            avg_last_6 = 0
        else:
            last_day_count = daily_counts[-1]
            if len(daily_counts) > 1:
                avg_last_6 = sum(daily_counts[:-1]) / len(daily_counts[:-1])
            else:
                avg_last_6 = 0

            # Compare last day to average of previous 6 days
            if avg_last_6 == 0:
                status = "Failed" if last_day_count > 0 else "Succeeded"
            else:
                status = "Failed" if last_day_count > avg_last_6 * 1.03 else "Succeeded"

        
        failed_request_kql = """
            union
            (
                requests
                | where success == false
                | project timestamp, operationName = operation_Name, FailedCount = 1, problemId = ""
            ),
            (
                exceptions
                | where isnotempty(problemId)
                | project timestamp, operationName = operation_Name, FailedCount = 1, problemId
            )
            | where problemId !in ("")
                and problemId !startswith("ClientConnectionFailure")
                and problemId !startswith("OperationNotFound")
            | summarize FailedCount = sum(FailedCount), exceptions = make_set(problemId) by bin(timestamp, 1d), operationName
            | order by timestamp desc, operationName
            | top 10 by FailedCount
        """

        table = self._query_app_insights(app_insights_id= app_insights_id, query=failed_request_kql, timespan=timedelta(hours=hours))

        results = []
        if table:
            results = [{"name": row["operationName"], "failedCount": row["FailedCount"], "exceptions": json.loads(row["exceptions"])} for row in table.rows]

        response = {
            "system": system,
            "name": resource_name,
            "type": "appInsights",
            "rgroup": resource_group,
            "status": status,
            "results": results,
            "error": f"Today's Failures: {last_day_count}, Avg Previous 6 Days: {avg_last_6:.2f}. <br> {self.markdownReport.build_results_list(results)}",
        }

        logger.info(f"Application Insights {resource_name} status {status}.")
        return response

    def get_timeseries(self, subscription_id: str, resource_group: str, resource_name: str, hours: int, failed_requests: bool) -> dict:
        app_insights_id=f"/subscriptions/{subscription_id}/resourceGroups/{resource_group}/providers/microsoft.insights/components/{resource_name}"
        
        timeGrain = next(val for th, val in thresholds if hours >= th)

        failed_request_kql = f"""
            let timeGrain={timeGrain};
            requests
            | where client_Type != "Browser"
            | summarize totalCount={'sumif(itemCount, success == false)' if failed_requests else 'sum(itemCount)'} by bin(timestamp, timeGrain)
            | order by timestamp
        """

        table = self._query_app_insights(app_insights_id= app_insights_id, query=failed_request_kql, timespan=timedelta(hours=hours))

        series = []
        if table:
            series = [{"timestamp": row["timestamp"], "count": row["totalCount"]} for row in table.rows]

        response = {
            "name": resource_name,
            "type": "appInsights",
            "rgroup": resource_group,
            "timeseries": series,
            "message": f"Time series data.",
        }

        logger.info(f"Retrieved time series for {resource_name}.")
        return response