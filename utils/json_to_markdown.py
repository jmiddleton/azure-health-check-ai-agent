
import logging
import os
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger("ms_agent")
logger.format = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
logger.setLevel(os.getenv("LOG_LEVEL", "INFO"))

class MarkdownReport:
    def __init__(self):
        pass

    def _evaluate_results_status(self, status) -> str:
        status=status.lower()

        if status == "succeeded":
            return "✅Succeeded"
        elif "partial" in status:
            return "⚠️Partially Failed"
        elif status == "failed":
            return "❌Failed"
        elif status == "exception":
            return "⚡Exception"
        else:
            return "Unknown"

    def build_results_list(self, results: list[dict]) -> str:
        """Create a Markdown list showing pipeline run results."""
        if not results:
            return "-"

        lines = []
        for r in results:
            p_name = r.get("name", "-")
            status = r.get("status", "")
            failures = r.get("failures", {})

            # Header line for the pipeline
            exceptions = ""
            if r.get("failedCount", -1) > 0:
                status = r.get("failedCount", 0)
                exceptions = " Exceptions: " + ", ".join(r.get("exceptions", []))

            lines.append(f"- **{p_name}**: {status}{exceptions}")

            if failures and type(failures) is dict:
                error_msg = failures.get("error", "-").replace("\n", " ").replace("\r", "").strip()
                lines.append(f" - `{failures.get('name', '-')}`: {error_msg}")
            elif failures and type(failures) is list:
                for fail in failures:
                    error_msg = fail.get("error", "-").replace("\n", " ").replace("\r", "").strip()
                    lines.append(f" - `{fail.get('name', '-')}`: {error_msg}")

        return "<br>".join(lines)
    
    async def to_markdown(self, data: list[dict]) -> str:
        """Convert JSON data to a markdown table."""
        header = "| System | Name | Status | Result | Recommendation |\n"
        divider = "|--------|------|---------|--------|----------------|\n"
        rows = ""

        sorted_data = sorted(data, key=lambda x: int(x.get("idx", 0)))
        for item in sorted_data:
            system = item.get("system", "")
            name = item.get("name", "") or "-"
            error = item.get("error", "")
            recommendation = item.get("recommendation", "-")

            status = self._evaluate_results_status(item.get("status", "Unknown"))

            # Use <br> to preserve formatting in Markdown viewers - {inner_table.replace(chr(10), '<br>')}
            rows += f"| {system} | {name} | {status} | {error.replace(chr(10), '<br>')} | {recommendation} |\n"

        return header + divider + rows
