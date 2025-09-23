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

# Import the new analyzer
from src.compliance_analyzer import ComplianceAnalyzer

# Instantiate the new ComplianceAnalyzer at startup.
# This is a heavyweight object that loads multiple ML models,
# so we follow a singleton pattern by creating it once.
print("Loading Compliance Analyzer at startup...")
analyzer = ComplianceAnalyzer()
print("Compliance Analyzer loaded successfully.")

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
import tempfile
import os
import shutil

@app.post("/analyze", response_class=HTMLResponse)
async def analyze_document(
    file: UploadFile = File(...),
    discipline: str = Form("All"),
    rubric_id: int = Form(None)
):
    # Use a temporary directory for robust cleanup of the uploaded file.
    temp_dir = tempfile.mkdtemp()
    temp_file_path = os.path.join(temp_dir, file.filename)
    try:
        with open(temp_file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        
        # 1. Parse the document content and scrub PHI
        document_chunks = parse_document_content(temp_file_path)
        if not document_chunks or not document_chunks[0][0]:
            raise HTTPException(status_code=400, detail="Could not extract text from document.")
        document_text = " ".join([chunk[0] for chunk in document_chunks if chunk[0]])
        scrubbed_text = scrub_phi(document_text)
        if not scrubbed_text.strip():
            raise HTTPException(status_code=400, detail="Document is empty or contains no parsable text.")
        
        # 2. Load the selected rubric from the database and run analysis
        if rubric_id is not None:
            result = run_rubric_analysis(scrubbed_text, rubric_id)
        else:
            result = run_discipline_analysis(scrubbed_text, discipline)
        return result
    finally:
        shutil.rmtree(temp_dir)

def run_rubric_analysis(file, rubric_id):
    # Save the uploaded file temporarily
    temp_file_path = f"temp_{file.filename}"
    with open(temp_file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    temp_rubric_path = None
    try:
        # 1. Parse document content and scrub for PHI
        document_chunks = parse_document_content(temp_file_path)
        document_text = " ".join([chunk[0] for chunk in document_chunks if chunk[0]])
        scrubbed_text = scrub_phi(document_text)

        # Handle empty text
        if not scrubbed_text.strip():
            raise HTTPException(status_code=400, detail="Document is empty or contains no parsable text.")

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

        # 3. Analyze using RubricService (original feature logic still works)
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix=".ttl") as temp_rubric_file:
            temp_rubric_file.write(rubric_content)
            temp_rubric_path = temp_rubric_file.name

        rubric_service = RubricService(ontology_path=temp_rubric_path)
        rules = rubric_service.get_rules()

        # Keyword-based findings for backward compatibility
        findings = []
        for rule in rules:
            for keyword in rule.positive_keywords:
                if keyword.lower() in scrubbed_text.lower():
                    findings.append(rule)
                    break

        # NEW: Analysis results using ComplianceAnalyzer if available
        analysis_results = None
        if 'analyzer' in globals():  # If you have ComplianceAnalyzer configured
            analysis_results = analyzer.analyze_document(scrubbed_text)

        # 4. Generate the HTML report, combine results
        with open("src/report_template.html", "r") as f:
            template_str = f.read()

        findings_html = ''
        if analysis_results:
            for section, analysis in analysis_results.items():
                findings_html += f"<div><strong>{section}</strong>: {analysis.replace('\\n', ' ')}</div>"
        elif findings:
            findings_html += "<ul>" + "".join(f"<li>{rule}</li>" for rule in findings) + "</ul>"
        else:
            findings_html = "No specific findings based on the selected rubric."

        report_html = template_str.replace("{{findings}}", findings_html)
        report_html = report_html.replace("{{guidelines}}", "\n\nGuideline correlation not performed for this rubric analysis.\n\n")

        return {"report": report_html, "analysis": analysis_results or findings}

    finally:
        if temp_rubric_path and os.path.exists(temp_rubric_path):
            os.remove(temp_rubric_path)

        findings_html = ""
        if analysis_results:
            for section, analysis in analysis_results.items():
                findings_html += f"""
                <details>
                    <summary>Section: {section}</summary>
                    <div class="finding-content">
                        <p>{analysis.replace("\n", "<br>")}</p>
                    </div>
                </details>
                """
        else:
def run_rubric_analysis(file, rubric_id):
    """
    Combines advanced PHI scrubbing, rubric lookup, rule-based and section-based analysis, and HTML reporting
    """
    import shutil, os, tempfile, sqlite3
    temp_file_path = f"temp_{file.filename}"
    temp_rubric_path = None
    try:
        # Save the uploaded file temporarily
        with open(temp_file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        # Parse and scrub text
        document_chunks = parse_document_content(temp_file_path)
        document_text = " ".join([chunk[0] for chunk in document_chunks if chunk[0]])
        scrubbed_text = scrub_phi(document_text)
        if not scrubbed_text.strip():
            raise HTTPException(status_code=400, detail="Document is empty or contains no parsable text.")
        # Load rubric from database
        rubric_content = None
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
        # Create temp rubric file for advanced rule extraction
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix=".ttl") as temp_rubric_file:
            temp_rubric_file.write(rubric_content)
            temp_rubric_path = temp_rubric_file.name
        rubric_service = RubricService(ontology_path=temp_rubric_path)
        rules = rubric_service.get_rules()
        findings = []
        # Fast keyword matching from rules (preserves feature branch logic)
        for rule in rules:
            for keyword in getattr(rule, "positive_keywords", []):
                if keyword.lower() in scrubbed_text.lower():
                    findings.append(rule)
                    break
        # ALSO conduct advanced section-by-section semantic analysis (main branch logic)
        analysis_results = None
        try:
            # Only run if ComplianceAnalyzer is available in environment
            if "analyzer" in globals():
                analysis_results = analyzer.analyze_document(scrubbed_text)
        except Exception as e:
            analysis_results = None
        # Report construction
        with open("src/report_template.html", "r") as f:
            template_str = f.read()
        findings_html = ""
        # Prefer showing advanced analysis first, then fallback to findings
        if analysis_results and isinstance(analysis_results, dict):
            for section, analysis in analysis_results.items():
                findings_html += f"<div><strong>{section}</strong>: {analysis.replace('\\n', ' ')}</div>"
        elif findings:
            findings_html += "<ul>" + "".join(f"<li>{getattr(rule, 'issue_title', str(rule))}</li>" for rule in findings) + "</ul>"
        else:
            findings_html = "<p>No specific findings based on the selected rubric.</p>"
        report_html = template_str.replace("<!-- Placeholder for findings -->", findings_html)
        # Advanced guideline logic: search and collate related guideline text for each finding if available
        guideline_html = ""
        if findings and "guideline_service" in globals():
            for rule in findings:
                title = getattr(rule, "issue_title", None)
                if title:
                    guideline_results = guideline_service.search(query=title, top_k=1)
                    if guideline_results:
                        guideline_html += "<div>"
                        guideline_html += f"<h4>Related to: {title}</h4>"
                        for result in guideline_results:
                            guideline_html += f"<p><strong>Source:</strong> {result['source']}</p>"
                            guideline_html += f"<p>{result['text']}</p>"
                        guideline_html += "</div>"
        if not guideline_html:
            # Fallback message for rubric analysis guidelines
            guideline_html = "<p>Guideline correlation not performed for this rubric analysis.</p>"
        report_html = report_html.replace("<!-- Placeholder for Medicare guidelines -->", guideline_html)
        return HTMLResponse(content=report_html)
    finally:
        # Thorough cleanup of temp files
        try:
            if temp_file_path and os.path.exists(temp_file_path):
                os.remove(temp_file_path)
            if temp_rubric_path and os.path.exists(temp_rubric_path):
                os.remove(temp_rubric_path)
        except Exception:
            pass

def run_discipline_analysis(file, discipline):
    """
    Advanced discipline analysis with ComplianceAnalyzer and dynamic guideline reporting
    """
    import shutil, os
    temp_file_path = f"temp_{file.filename}"
    try:
        with open(temp_file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        # Parse and analyze
        document_chunks = parse_document_content(temp_file_path)
        document_text = " ".join([chunk[0] for chunk in document_chunks if chunk[0]])
        result = analyzer.analyze_document(document_text)
        analysis_html = "<div>" + result.get("analysis", "") + "</div>" if result else "<p>No analysis results were generated.</p>"
        sources_html = "<ul>"
        for source in result.get("sources", []):
            sources_html += f"<li>{source}</li>"
        sources_html += "</ul>"
        with open("src/report_template.html", "r") as f:
            template_str = f.read()
        report_html = template_str.replace("<!-- Placeholder for findings -->", analysis_html)
        report_html = report_html.replace("<!-- Placeholder for Medicare guidelines -->", sources_html)
        return HTMLResponse(content=report_html)
    finally:
        try:
            if temp_file_path and os.path.exists(temp_file_path):
                os.remove(temp_file_path)
        except Exception:
            pass

    return HTMLResponse(content=report_html)

except Exception as e:
    # Log the exception for easier debugging and return a clean error to the client.
    print(f"An error occurred during analysis: {e}")
    raise HTTPException(status_code=500, detail=f"An internal error occurred: {str(e)}")
finally:
    # Clean up the temporary directory and its contents.
    if os.path.exists(temp_dir):
        shutil.rmtree(temp_dir)
    return HTMLResponse(content=report_html)
