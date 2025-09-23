from fastapi import FastAPI, UploadFile, File
from fastapi.responses import HTMLResponse
import shutil
import os

from rubric_service import RubricService, ComplianceRule
from parsing import parse_document_content
from guideline_service import GuidelineService
from document_classifier import classify_document

app = FastAPI()

# Instantiate and load guidelines at startup
guideline_service = GuidelineService()
guideline_sources = [
    "../../_default_medicare_benefit_policy_manual.txt",
    "../../_default_medicare_part.txt"
]
guideline_service.load_and_index_guidelines(sources=guideline_sources)


@app.get("/")
def read_root():
    return {"message": "Backend for Therapy Compliance Analyzer"}


@app.post("/analyze")
async def analyze_document(file: UploadFile = File(...)):
    # This is a combination of the previous correct implementation and the new features.
    # I am replacing the whole function to ensure correctness.
    from collections import Counter
    from fastapi.responses import JSONResponse

    # Save the uploaded file temporarily
    temp_file_path = f"temp_{file.filename}"
    with open(temp_file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    # 1. Parse the document content
    document_chunks = parse_document_content(temp_file_path)
    document_text = " ".join([chunk[0] for chunk in document_chunks])

    # 2. Classify Document and Load Appropriate Rubric
    doc_type = classify_document(document_text)

    rubric_mapping = {
        "Evaluation / Recertification": "pt_evaluation_rubric.ttl",
        # Add other mappings here for Progress Notes, etc.
    }
    # Default to the general rubric if no specific one is found
    rubric_file = rubric_mapping.get(doc_type, "pt_compliance_rubric.ttl")

    rubric_service = RubricService(ontology_path=rubric_file)
    rules = rubric_service.get_rules()

    # 3. Perform analysis
    findings = []
    for rule in rules:
        # This is a simplified logic. A real implementation would handle positive/negative keywords better.
        if any(keyword.lower() in document_text.lower() for keyword in rule.positive_keywords):
             findings.append(rule)

    # 4. Calculate Metrics
    risk_count = len(findings)
    findings_by_category = Counter(rule.issue_category for rule in findings)
    findings_by_severity = Counter(rule.severity for rule in findings)

    # Calculate compliance score
    compliance_score = 100
    severity_map = {"High": 15, "Medium": 10, "Low": 5, "finding": 10, "suggestion": 2}
    for finding in findings:
        compliance_score -= severity_map.get(finding.severity, 0)
    compliance_score = max(0, compliance_score)

    # 5. Get Guideline Details
    guideline_details = []
    if findings:
        for finding in findings:
            guideline_results = guideline_service.search(query=finding.issue_title, top_k=1)
            if guideline_results:
                guideline_details.append({
                    "related_to": finding.issue_title,
                    "guidelines": guideline_results
                })

    # 6. Construct JSON Response
    findings_as_dicts = [finding.__dict__ for finding in findings]

    response_data = {
        "document": {
            "text": document_text,
            "filename": file.filename,
            "document_type": doc_type
        },
        "analysis": {
            "findings": findings_as_dicts,
            "guidelines": guideline_details
        },
        "metrics": {
            "risk_count": risk_count,
            "compliance_score": compliance_score,
            "by_category": dict(findings_by_category),
            "by_severity": dict(findings_by_severity)
        }
    }

    # Clean up the temporary file
    os.remove(temp_file_path)

    return JSONResponse(content=response_data)

