import os
from PyQt6.QtWidgets import QFileDialog
from xhtml2pdf import pisa
from jinja2 import Template
import json

def generate_pdf_report(analysis_results_str, parent=None):
    """Generates a PDF report from the analysis results."""
    try:
        analysis_results = json.loads(analysis_results_str)
    except json.JSONDecodeError:
        return False, "Failed to decode analysis results."

    # Define the path for the template
    template_path = os.path.join(os.path.dirname(__file__), '..', 'report_template.html')

    # Read the template file
    try:
        with open(template_path, 'r') as f:
            template_content = f.read()
    except FileNotFoundError:
        return False, f"Report template not found at {template_path}"

    # Create a Jinja2 template object
    template = Template(template_content)

    # Transform the analysis results to match the template's expectations
    findings = []
    for finding in analysis_results.get('findings', []):
        findings.append({
            'title': finding.get('rule_id', 'N/A'),
            'category': finding.get('risk', 'N/A'),
            'justification': finding.get('text', 'N/A'),
            'observation': finding.get('suggestion', 'N/A')
        })

    # Render the template with the analysis results
    html_content = template.render(
        findings=findings,
        guidelines=analysis_results.get('guidelines', [])
    )

    # Prompt the user to select a file path
    file_path, _ = QFileDialog.getSaveFileName(
        parent,
        "Save Report as PDF",
        "",
        "PDF Files (*.pdf)"
    )

    if not file_path:
        return False, "File save cancelled."

    # Generate the PDF
    try:
        with open(file_path, "w+b") as f:
            pisa_status = pisa.CreatePDF(html_content, dest=f)
        if pisa_status.err:
            return False, f"PDF generation failed: {pisa_status.err}"
        return True, file_path
    except Exception as e:
        return False, f"An error occurred while saving the PDF: {e}"
