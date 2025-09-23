from fastapi import FastAPI, UploadFile, File
from fastapi.responses import JSONResponse
import shutil
import os
from collections import Counter

from rubric_service import RubricService, ComplianceRule
from parsing import parse_document_content
from guideline_service import GuidelineService

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
    # Save the uploaded file temporarily
    temp_file_path = f"temp_{file.filename}"
    with open(temp_file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    # 1. Parse the document content
    document_chunks = parse_document_content(temp_file_path)
    document_text = " ".join([chunk[0] for chunk in document_chunks])

    # 2. Load the rubric
    rubric_service = RubricService(ontology_path="pt_compliance_rubric.ttl")
    rules = rubric_service.get_rules()

    # 3. Perform analysis
    findings = []
    for rule in rules:
        for keyword in rule.positive_keywords:
            if keyword.lower() in document_text.lower():
                findings.append(rule)
                break

    # 4. Calculate Metrics
    risk_count = len(findings)
    findings_by_category = Counter(rule.issue_category for rule in findings)
    findings_by_severity = Counter(rule.severity for rule in findings)

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
    findings_as_dicts = [
        {
            "uri": finding.uri,
            "severity": finding.severity,
            "issue_title": finding.issue_title,
            "issue_detail": finding.issue_detail,
            "issue_category": finding.issue_category,
            "discipline": finding.discipline,
            "financial_impact": finding.financial_impact,
        } for finding in findings
    ]

    response_data = {
        "document": {
            "text": document_text,
            "filename": file.filename
        },
        "analysis": {
            "findings": findings_as_dicts,
            "guidelines": guideline_details
        },
        "metrics": {
            "risk_count": risk_count,
            "by_category": dict(findings_by_category),
            "by_severity": dict(findings_by_severity)
        }
    }

    # Clean up the temporary file
    os.remove(temp_file_path)

    return JSONResponse(content=response_data)

