import logging
from jinja2 import Environment, FileSystemLoader, select_autoescape
from typing import Dict, Any
import os

logger = logging.getLogger(__name__)

class ReportGenerator:
    """A class to generate HTML reports from analysis results."""

    def __init__(self, template_dir: str):
        """
        Initializes the ReportGenerator.

        Args:
            template_dir (str): The directory where the Jinja2 templates are located.
        """
        if not os.path.isdir(template_dir):
            raise FileNotFoundError(f"Template directory not found: {template_dir}")

        self.env = Environment(
            loader=FileSystemLoader(template_dir),
            autoescape=select_autoescape(['html', 'xml'])
        )
        logger.info(f"ReportGenerator initialized with template directory: {template_dir}")

    def generate_html_report(
        self,
        analysis_result: Dict[str, Any],
        template_name: str,
        output_path: str
    ) -> bool:
        """
        Generates an HTML report from the analysis result using a specified template.

        Args:
            analysis_result (Dict[str, Any]): A dictionary containing the data for the report.
            template_name (str): The filename of the template to use (e.g., 'report_template.html').
            output_path (str): The path to save the generated HTML file.

        Returns:
            bool: True if the report was generated successfully, False otherwise.
        """
        try:
            template = self.env.get_template(template_name)
            html_content = template.render(analysis=analysis_result)

            with open(output_path, "w", encoding="utf-8") as f:
                f.write(html_content)

            logger.info(f"Report generated successfully at {output_path}")
            return True
        except Exception as e:
            logger.error(f"Failed to generate HTML report: {e}", exc_info=True)
            return False

# Example Usage (for demonstration purposes):
if __name__ == '__main__':
    # This block will only run when the script is executed directly
    # It serves as a simple test or demonstration of the class functionality.

    # Define a mock analysis result that matches the structure expected by the template
    mock_analysis = {
        "document_name": "Sample Progress Note.docx",
        "analysis_date": "2023-10-27",
        "compliance_score": 88,
        "total_findings": 2,
        "findings": [
            {
                "risk_level": "Medium",
                "problematic_text": "Patient states they are 'feeling okay' but no objective measures were provided.",
                "personalized_tip": "Consider adding specific measurements like a pain scale rating (e.g., '5/10') to objectify the patient's statement.",
                "habit": {
                    "name": "Objectify Subjective Statements",
                    "explanation": "Always back up subjective patient reports with objective data points."
                },
                "low_confidence": False,
                "disputed": False,
                "disputable": True
            },
            {
                "risk_level": "Low",
                "problematic_text": "Plan for next session is to 'continue with exercises'.",
                "personalized_tip": "Specify the exercises planned. For example: 'Plan to continue with 3 sets of 10 squats and 2 sets of 15-second planks.'",
                "habit": {
                    "name": "Be Specific in Planning",
                    "explanation": "Ensure treatment plans are detailed and clearly outline the interventions for the next session."
                },
                "low_confidence": True,
                "disputed": False,
                "disputable": True
            }
        ],
        "limitations_text": "This AI analysis is a tool to assist, not replace, professional judgment. It may not identify all compliance issues.",
        "generation_date": "2023-10-27 15:45:00"
    }

    # Setup the generator
    # Assuming the script is run from the project root, the templates are in 'src/resources'
    template_directory = os.path.join(os.path.dirname(__file__), 'resources')
    report_generator = ReportGenerator(template_dir=template_directory)

    # Generate the report
    success = report_generator.generate_html_report(
        analysis_result=mock_analysis,
        template_name="report_template.html",
        output_path="sample_report.html"
    )

    if success:
        print("Sample report 'sample_report.html' generated successfully.")
        # Try to open the report automatically
        import webbrowser
        webbrowser.open('sample_report.html')
    else:
        print("Failed to generate sample report.")