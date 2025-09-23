from fastapi import FastAPI, UploadFile, File, Query
from fastapi.responses import HTMLResponse
import shutil
import os
import tempfile

from rubric_service import RubricService, ComplianceRule
from parsing import parse_document_content

# --- Path Setup ---
# Build paths inside the project like this: os.path.join(BASE_DIR, 'relative/path/to/file')
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
TEMPLATE_PATH = os.path.join(BASE_DIR, "templates", "report_template.html")


app = FastAPI()

@app.get("/")
def read_root():
    return {"message": "Backend for Therapy Compliance Analyzer"}

@app.post("/analyze", response_class=HTMLResponse)
async def analyze_document(file: UploadFile = File(...), rubric: str = Query("pt", enum=["pt", "ot", "slp"])):
    # Use a temporary directory for uploaded files for security and cleanliness
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_file_path = os.path.join(temp_dir, file.filename)
        with open(temp_file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        # 1. Parse the document content
        document_chunks = parse_document_content(temp_file_path)
        document_text = " ".join([chunk[0] for chunk in document_chunks])

        # 2. Load the rubric based on the query parameter
        rubric_filename = f"{rubric}_compliance_rubric.ttl"
        rubric_path = os.path.join(BASE_DIR, rubric_filename)

        if not os.path.exists(rubric_path):
            return HTMLResponse(content=f"<h1>Error</h1><p>Rubric file '{rubric_filename}' not found.</p>", status_code=404)

        rubric_service = RubricService(ontology_path=rubric_path)
        rules = rubric_service.get_rules()

        # 3. Perform analysis (simple keyword matching)
        findings = []
        for rule in rules:
            for keyword in rule.positive_keywords:
                if keyword.lower() in document_text.lower():
                    findings.append(rule)
                    break # Move to the next rule once a keyword is found

    # 4. Generate the HTML report
    with open(TEMPLATE_PATH, "r") as f:
        template_str = f.read()

    findings_html = ""
    if findings:
        for finding in findings:
            findings_html += f"""
            <div class="finding">
                <h3>{finding.issue_title}</h3>
                <p><strong>Severity:</strong> {finding.severity}</p>
                <p><strong>Category:</strong> {finding.issue_category}</p>
                <p>{finding.issue_detail}</p>
            </div>
            """
    else:
        findings_html = "<p>No specific findings based on the rubric.</p>"

    report_html = template_str.replace("<!-- Placeholder for findings -->", findings_html)

    # Clean up the temporary file
    os.remove(temp_file_path)

    return HTMLResponse(content=report_html)