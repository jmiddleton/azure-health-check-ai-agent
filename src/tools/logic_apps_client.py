from datetime import datetime, timedelta, timezone
from azure.mgmt.logic import LogicManagementClient
from dotenv import load_dotenv
import logging
import os

from utils.json_to_markdown import MarkdownReport

load_dotenv()
logger = logging.getLogger(__name__)
logger.setLevel(os.getenv("LOG_LEVEL", "INFO"))

class LogicAppService:
    def __init__(self, credential):
        self.credential = credential
        self.markdownReport = MarkdownReport()

    @staticmethod
    def _to_filter_timestamp(dt):
        """Format datetime to Logic App filter-compatible ISO string."""
        return dt.strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3] + "Z"

    def health_check(self, subscription_id, resource_group, logic_app_name, url="", system="") -> dict:
        """Check all Logic App runs for the day and summarize status."""

        client = LogicManagementClient(self.credential, subscription_id, api_version="2016-06-01")

        now = datetime.now(timezone.utc)
        yesterday = now - timedelta(days=1)

        try:
            runs_paged = client.workflow_runs.list(
                resource_group_name=resource_group,
                workflow_name=logic_app_name
            )

            if not runs_paged:
                return {
                    "system": system,
                    "name": logic_app_name,
                    "type": "logicApp",
                    "rgroup": resource_group,
                    "status": "No Runs",
                    "error": "-"
                }

            status= "Succeeded"
            results = []
            processed = 0
            for run in runs_paged:
                processed += 1
                if processed > 40 or (run.start_time and run.start_time < yesterday):
                    break   # Limit to recent 40 runs or those within the last day

                run_info = {
                    "name": run.name,
                    "status": run.status or "Unknown",
                    "runId": run.name,
                    "failures": None
                }

                # get details of the activities that failed
                activity_runs = client.workflow_run_actions.list(
                    resource_group_name=resource_group,
                    workflow_name=logic_app_name,
                    run_name=run.name,
                    filter="status eq 'Failed'"
                )

                failed_activities = [
                    {
                        "name": a.name,
                        "status": a.status,
                        "error": a.error.get("message", "") if a.error else ""
                    }
                    for a in activity_runs
                ]

                #get first failed activity
                if failed_activities:
                    run_info["failures"] = failed_activities

                results.append(run_info)

                # return on first failed run
                if run.status == "Failed" or run_info["failures"] is not None:
                    status= "Failed"
                    break

            logger.info(f"Logic App {logic_app_name} status: {status}")
            failed_result = [r for r in results if r.get("status") == "Failed"]
            return {
                "system": system,
                "name": logic_app_name,
                "type": "logicApp",
                "rgroup": resource_group,
                "status": status,
                "results": failed_result,
                "error": self.markdownReport.build_results_list(failed_result)
            }

        except Exception as e:
            logger.error(f"Error fetching Logic App runs: {e}")
            return {
                "system": system,
                "name": logic_app_name,
                "type": "logicApp",
                "rgroup": resource_group,
                "status": "Exception",
                "error": f"Error fetching Logic App runs: {e}"
            }