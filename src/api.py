from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.responses import HTMLResponse
import shutil
import os
import re
import sqlite3
import tempfile

from src.database import initialize_database, DATABASE_PATH
from src.rubric_service import RubricService
from src.parsing import parse_document_content
from src.guideline_service import GuidelineService
from src.compliance_analyzer import ComplianceAnalyzer
# Mode: "offline" or "backend"
analysis_mode = "backend"  # or set to "offline" as needed

if analysis_mode == "offline":
    from src.document_classifier import DocumentClassifier, DocumentType
    # Set up classifier usage (example)
    classifier = DocumentClassifier()
else:
    from src import rubric_router
    initialize_database()  # Make sure rubric/database is ready for API


app = FastAPI()

app.include_router(rubric_router.router)

# Instantiate and load guidelines at startup
guideline_service = GuidelineService()
guideline_sources = [
    "_default_medicare_benefit_policy_manual.txt",
    "_default_medicare_part.txt"
]
guideline_service.load_and_index_guidelines(sources=guideline_sources)

# Instantiate the main compliance analyzer at startup
analyzer = ComplianceAnalyzer()

def scrub_phi(text: str) -> str:
    if not isinstance(text, str):
        return text
    patterns = [
        (r'[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}', '[EMAIL]'),
        (r'(\+?\d{1,2}[\s\-.]?)?(\(?\d{3}\)?[ \-.]?\d{3}[\-.]?\d{4})', '[PHONE]'),
        (r'\b\d{3}-\d{2}-\d{4}\b', '[SSN]'),
        (r'\bMRN[:\s]*[A-Za-z0-9\-]{4,}\b', '[MRN]'),
        (r'\b(19|20)\d{2}-/ (0?[1-9]|1[0-2])-/ (0?[1-g]|[12]\d|3[01])\b', '[DATE]'),
        (r'\b(Name|Patient|DOB|Address)[:\s]+[^\n]+', r'\1: [REDACTED]'),
    ]
    out = text
    for pat, repl in patterns:
        out = re.sub(pat, repl, out)
    return out

@app.get("/")
def read_root():
    return {"message": "Backend for Therapy Compliance Analyzer"}

@app.post("/analyze", response_class=HTMLResponse)
async def analyze_document(
    file: UploadFile = File(...), 
    discipline: str = Form("All"), 
    rubric_id: int = Form(None)
):
    if rubric_id is not None:
        # Run rubric-based analysis
        result = run_rubric_analysis(file, rubric_id)
    else:
        # Run discipline-based analysis (default if rubric_id is not given)
        result = run_discipline_analysis(file, discipline)
    return result

def run_rubric_analysis(file, rubric_id):
    # Save the uploaded file temporarily
    temp_file_path = f"temp_{file.filename}"
    with open(temp_file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    temp_rubric_path = None
    try:
        # 1. Parse document content
        document_chunks = parse_document_content(temp_file_path)
        document_text = " ".join([chunk[0] for chunk in document_chunks])
        scrubbed_text = scrub_phi(document_text)

        # 2. Load the selected rubric from the database
        try:
            with sqlite3.connect(DATABASE_PATH) as conn:
                cur = conn.cursor()
                cur.execute("SELECT content FROM rubrics WHERE id = ?", (rubric_id,))
                result = cur.fetchone()
            if not result:
                raise HTTPException(status_code=404, detail="Selected rubric not found.")
            rubric_content = result[0]
        except sqlite3.Error as e:
            raise HTTPException(status_code=500, detail=f"Database error: {e}")

        # 3. Use RubricService with the specific rubric content
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix=".ttl") as temp_rubric_file:
            temp_rubric_file.write(rubric_content)
            temp_rubric_path = temp_rubric_file.name

        rubric_service = RubricService(ontology_path=temp_rubric_path)
        rules = rubric_service.get_rules()

        # 4. Perform keyword-based analysis
        findings = []
        for rule in rules:
            # Simple keyword matching (can be expanded)
            for keyword in rule.positive_keywords:
                if keyword.lower() in scrubbed_text.lower():
                    findings.append(rule)
                    break

        # 5. Generate the HTML report
        with open("src/report_template.html", "r") as f:
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
            findings_html = "<p>No specific findings based on the selected rubric.</p>"

        report_html = template_str.replace("<!-- Placeholder for findings -->", findings_html)
        # For rubric analysis, we leave the guidelines section blank unless specified otherwise
        report_html = report_html.replace("<!-- Placeholder for Medicare guidelines -->", "<p>Guideline correlation not performed for this rubric analysis.</p>")

    finally:
        # Clean up the temporary files
        os.remove(temp_file_path)
        if temp_rubric_path and os.path.exists(temp_rubric_path):
            os.remove(temp_rubric_path)

    return HTMLResponse(content=report_html)

def run_discipline_analysis(file, discipline):
    # Save the uploaded file temporarily
    temp_file_path = f"temp_{file.filename}"
    with open(temp_file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    try:
        # 1. Parse the document content
        document_chunks = parse_document_content(temp_file_path)
        document_text = " ".join([chunk[0] for chunk in document_chunks])

        # 2. Perform analysis using the ComplianceAnalyzer
        result = analyzer.analyze_document(document_text)
        analysis_html = f"<div>{result['analysis']}</div>"

        # 3. Format the sources
        sources_html = "<ul>"
        for source in result['sources']:
            sources_html += f"<li>{source}</li>"
        sources_html += "</ul>"

        # 4. Generate the HTML report
        with open("src/report_template.html", "r") as f:
            template_str = f.read()

        report_html = template_str.replace("<!-- Placeholder for findings -->", analysis_html)
        report_html = report_html.replace("<!-- Placeholder for Medicare guidelines -->", sources_html)

    finally:
        # Clean up the temporary file
        os.remove(temp_file_path)

    return HTMLResponse(content=report_html)
