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
from src import rubric_router

initialize_database()

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
async def analyze_document(file: UploadFile = File(...)):
    # Use a temporary directory for robust cleanup of the uploaded file.
    temp_dir = tempfile.mkdtemp()
    temp_file_path = os.path.join(temp_dir, file.filename)
    try:
        with open(temp_file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        # 1. Parse the document content and scrub for PHI.
        document_chunks = parse_document_content(temp_file_path)
        if not document_chunks or not document_chunks[0][0]:
             raise HTTPException(status_code=400, detail="Could not extract text from document.")

        document_text = " ".join([chunk[0] for chunk in document_chunks if chunk[0]])
        scrubbed_text = scrub_phi(document_text)

        if not scrubbed_text.strip():
            raise HTTPException(status_code=400, detail="Document is empty or contains no parsable text.")

        # 2. Perform analysis using the new, refactored ComplianceAnalyzer.
        # This replaces the old keyword-based analysis.
        analysis_results = analyzer.analyze_document(scrubbed_text)

        # 3. Generate the HTML report from the section-by-section results.
        # Note: The path to the template is relative to the root, where the app is run.
        with open("src/report_template.html", "r") as f:
            template_str = f.read()

        # Populate findings using the new dictionary structure and collapsible sections.
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
            findings_html = "<p>No analysis results were generated.</p>"

        report_html = template_str.replace("<!-- Placeholder for findings -->", findings_html)

        # The new analyzer incorporates guideline retrieval, so the old guideline search is no longer needed.
        # We can provide a generic message here.
        report_html = report_html.replace("<!-- Placeholder for Medicare guidelines -->", "<p>Guideline analysis is now integrated into the section-by-section results.</p>")

    except Exception as e:
        # Log the exception for easier debugging and return a clean error to the client.
        print(f"An error occurred during analysis: {e}")
        raise HTTPException(status_code=500, detail=f"An internal error occurred: {str(e)}")
    finally:
        # Clean up the temporary directory and its contents.
        if os.path.exists(temp_dir):
            shutil.rmtree(temp_dir)

    return HTMLResponse(content=report_html)
