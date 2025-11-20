from typing import Optional
from azure.core.exceptions import HttpResponseError
import requests


class AzureDashboardUpdater:
    """
    Update Markdown widgets in an Azure Portal dashboard.
    """

    def __init__(
        self,
        credential,
        subscription_id: str,
        resource_group: str,
        dashboard_uuid: str,
    ):
        self.credential = credential
        self.subscription_id = subscription_id
        self.resource_group = resource_group
        self.dashboard_uuid = dashboard_uuid

        self.token = credential.get_token("https://management.azure.com/.default").token
        self.headers = {"Authorization": f"Bearer {self.token}", "Content-Type": "application/json"}

        self.url = (
            f"https://management.azure.com/subscriptions/{self.subscription_id}/"
            f"resourceGroups/{self.resource_group}/providers/Microsoft.Portal/dashboards/{dashboard_uuid}"
            f"?api-version=2022-12-01-preview"
        )

    def get_dashboard(self):
        """
        Retrieve an Azure Portal dashboard as a dict.
        """

        resp = requests.get(self.url, headers=self.headers)
        resp.raise_for_status()
        return resp.json()

    def update_markdown(
        self,
        new_content: str,
        markdown_title: Optional[str] = None,
        subtitle: Optional[str] = "",
        update_all: bool = False,
    ) -> bool:
        """
        Update the Markdown widget(s) within a dashboard.

        :param new_content: Markdown text to insert.
        :param markdown_title: Optional title to match a specific Markdown widget.
        :param update_all: If True, update all Markdown widgets.
        :return: True if any widget was updated.
        """
        dashboard = self.get_dashboard()
        updated = False

        lenses = dashboard.get("properties", {}).get("lenses", {})

        for lens in lenses:
            for part in lens.get("parts", {}):
                metadata = part.get("metadata", {})
                settings = metadata.get("settings", {})
                content = settings.get("content", "")
                widget_type = metadata.get("type", "")

                if "MarkdownPart" in widget_type:
                    title = content.get("title", "")
                    if update_all or (markdown_title and markdown_title.lower() in title.lower()):
                        content["content"] = new_content
                        content["title"] = markdown_title or title
                        content['subtitle'] = subtitle
                        updated = True

        if updated:
            self._save_dashboard(dashboard)

        return updated

    def _save_dashboard(self, dashboard: dict):
        """
        Save the modified dashboard back to Azure.
        """
        try:
            put_resp = requests.put(self.url, headers=self.headers, json=dashboard)
            put_resp.raise_for_status()
            print(f"Dashboard updated successfully.")
        except HttpResponseError as e:
            raise RuntimeError(f"Failed to update dashboard: {e}")