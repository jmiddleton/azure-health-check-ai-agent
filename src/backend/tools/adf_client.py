from datetime import datetime, time, timedelta, timezone
from pdb import run
from venv import logger
from azure.mgmt.datafactory import DataFactoryManagementClient
from dotenv import load_dotenv
import logging
import os

from utils.json_to_markdown import MarkdownReport

load_dotenv()
logger = logging.getLogger(__name__)
logger.setLevel(os.getenv("LOG_LEVEL", "INFO"))

class ADFService:
    def __init__(self, credential):
        self.credential = credential
        self.markdownReport = MarkdownReport()

    @staticmethod
    def _to_filter_timestamp(dt):
        """Convert datetime to ISO 8601 format used by ADF filters."""
        return dt.strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3] + "Z"

    def health_check(self, subscription_id, resource_group, df_name, url, system="") -> dict:
        """Extract ADF details and return JSON with pipeline and run status."""

        client = DataFactoryManagementClient(self.credential, subscription_id)

        now = datetime.now(timezone.utc)
        yesterday = now - timedelta(days=1)

        filter_params = {
            "lastUpdatedAfter": self._to_filter_timestamp(yesterday),
            "lastUpdatedBefore": self._to_filter_timestamp(now),
            "filters": [{"operand": "LatestOnly", "operator": "Equals", "values": ["true"]}],
            "order_by": [{"order_by": "RunStart", "order": "DESC"}]
        }

        try:
            runs = client.pipeline_runs.query_by_factory(resource_group, df_name, filter_parameters=filter_params)
    
            if not runs.value:
                return {
                    "system": system,
                    "name": df_name,
                    "type": "adf",
                    "rgroup": resource_group,
                    "status": "No Runs"
                }

            status= "Succeeded"
            results = []
            processed = 0
            for run in runs.value:
                processed += 1
                if processed > 50:
                    break  # Limit to 50 recent runs

                run_info = {
                    "name": run.pipeline_name,
                    "status": run.status or "Unknown",
                    "runId": run.run_id,
                    "failures": None
                }

                if run.status == "Failed":
                    status= "Failed"
                    # get details of the activities that failed
                    activity_runs = client.activity_runs.query_by_pipeline_run(
                        resource_group, df_name, run.run_id,
                        filter_parameters={
                            "lastUpdatedAfter": self._to_filter_timestamp(yesterday),
                            "lastUpdatedBefore": self._to_filter_timestamp(now),
                            "filters": [{"operand": "Status", "operator": "Equals", "values": ["Failed"]}]
                        }
                    )

                    failed_activities = [
                        {
                            "name": a.activity_name,
                            "status": a.status,
                            "error": a.error.get("message", "") if a.error else ""
                        }
                        for a in activity_runs.value
                    ]

                    #get first failed activity
                    if failed_activities:
                        run_info["failures"] = failed_activities[0]

                    results.append(run_info)

            logger.debug(f"Status of Data Factory: {df_name},  status: {status}")
            return {
                "system": system,
                "name": df_name,
                "type": "adf",
                "rgroup": resource_group,
                "status": status,
                "results": results if status == "Failed" else [],
                "error": self.markdownReport.build_results_list(results) if status == "Failed" else "-"
            }

        except Exception as e:
            logger.error(f"Error querying ADF runs: {e}")
            return {
                "system": system,
                "name": df_name,
                "type": "adf",
                "rgroup": resource_group,
                "status": "Exception",
                "error": f"Error querying runs: {e}"
            }
