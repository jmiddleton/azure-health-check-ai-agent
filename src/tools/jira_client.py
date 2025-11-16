
from dotenv import load_dotenv
import logging
import os

from jira import JIRA

load_dotenv()

logger = logging.getLogger(__name__)
logger.setLevel(os.getenv("LOG_LEVEL", "INFO"))

class JiraTicketManager:
    """
    Raise Jira issues for the Integration team.
    """

    def __init__(self, url: str, user: str, token: str):
        self.client = JIRA(
            server= url,
            basic_auth=(user, token)
        )

    def _create_issue_table(self, summary, diagnosis, error, recommendation, severity, service_impact):
        return f"""
            || *Triage Field* || *Details* ||
            | *Issue Summary* | {summary} |
            | *Issue Occur* |  |
            | *Severity* | {severity} |
            | *Impact Level* |  |
            | *Impacted Systems/Services* | {service_impact} |
            | *Initial Diagnosis* | {diagnosis} |
            | *Logs / Screenshots / Metrics* | {error} |
            | *Mitigation / Workaround* |  |
            | *Next Steps / Action Items* | {recommendation.replace("<br>", "\n")} |
            | *Contact Information* | *AI Agent Health Check* |
            """

    async def create_tickets(self, data: list[dict]) -> str:
        """
        Create a Jira ticket.
        """

        response=[]

        try:
            for item in data:
                status = item.get("status", "").lower()
                if "failed" in status:
                    name = item.get("name", "No Name")
                    recommendation = item.get("recommendation", "No Recommendation Provided")
                    summary = f"[Prod Issue] {name} - Health Check Failed"
                    
                    logger.info(f"Creating Jira ticket for failed item: {name}")

                    # if there is already a ticket for this item, skip creating a new one, to avoid duplicates
                    jql = f'project = "{os.getenv("JIRA_PROJECT_KEY")}" AND summary ~ "{summary}" AND status != "Done"'
                    existing_issues = self.client.search_issues(jql)
                    if existing_issues:
                        existing_issues[0].update(description= self._create_issue_table(summary="Health Check Failed", diagnosis="", error=item.get("error", ""), recommendation=recommendation, severity="Severity 3", service_impact=name))
                        
                        item['jira_ticket'] = existing_issues[0].key
                        logger.info(f"Jira ticket for {name} already exists. Updated existing ticket: {existing_issues[0].key}")

                        response.append({
                            "jira_ticket": existing_issues[0].key,
                            "message": f"Jira ticket {existing_issues[0].key} updated."
                        })
                        continue

                    new_issue = self.client.create_issue(
                        project=os.getenv("JIRA_PROJECT_KEY"),
                        summary=summary,
                        description= self._create_issue_table(summary="Health Check Failed", diagnosis="", error=item.get("error", ""), recommendation=recommendation, severity="Severity 3", service_impact=name),
                        issuetype={"name": "Bug"}
                    )

                    item['jira_ticket'] = new_issue.key
                    logger.info(f"Created Jira ticket: {new_issue.key}")

                    response.append({
                        "jira_ticket": new_issue.key,
                        "message": f"Jira ticket {new_issue.key} created successfully for {name}."
                    })

            return {
                "message": "Jira ticket created",
                "tickets": response
            }
        except Exception as e:
            logger.error(f"Error creating Jira ticket: {e}")
            return {
                "message": f"Error creating Jira ticket: {e}. Please try again later.",
                "tickets": [],
            }