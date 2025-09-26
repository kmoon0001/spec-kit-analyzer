import logging
from jinja2 import Environment, FileSystemLoader
from typing import Dict, Any

logger = logging.getLogger(__name__)


class ReportGenerator:
    """A class to generate HTML reports from analysis results."""

    def __init__(self, template_path: str):
        """Initializes the ReportGenerator with the path to the template directory."""
        self.env = Environment(loader=FileSystemLoader(template_path))

    def generate_html_report(self, analysis_result: Dict[str, Any], output_path: str):
        """Generates an HTML report from the analysis result."""
        try:
            template = self.env.get_template("report_template.html")
            html_content = template.render(analysis=analysis_result)

            with open(output_path, "w") as f:
                f.write(html_content)

            logger.info(f"Report generated successfully at {output_path}")
            return True
        except Exception as e:
            logger.error(f"Failed to generate HTML report: {e}")
            return False
