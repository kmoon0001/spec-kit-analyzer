from fastapi import FastAPI, UploadFile, File
from fastapi.responses import HTMLResponse
import shutil
import os
import matplotlib.pyplot as plt
import base64
import io

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


@app.post("/analyze", response_class=HTMLResponse)
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

    # 4. Calculate compliance score
    total_rules = len(rules)
    rules_failing = len(findings)
    compliance_score = ((total_rules - rules_failing) / total_rules) * 100 if total_rules > 0 else 100

    # 5. Generate compliance chart
    fig, ax = plt.subplots()
    ax.barh(['Compliance'], [compliance_score], color='green' if compliance_score > 80 else 'orange' if compliance_score > 60 else 'red')
    ax.set_xlim(0, 100)
    ax.set_xlabel('Compliance Score (%)')
    ax.set_title('Compliance Score')

    # Save chart to a bytes buffer
    buf = io.BytesIO()
    plt.savefig(buf, format='png')
    buf.seek(0)
    chart_base64 = base64.b64encode(buf.read()).decode('utf-8')
    plt.close(fig)


    # 6. Generate the HTML report
    with open("../../src/report_template.html", "r") as f:
        template_str = f.read()

    # Populate findings
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

    # Populate Medicare guidelines
    guidelines_html = ""
    if findings:
        for finding in findings:
            guideline_results = guideline_service.search(query=finding.issue_title, top_k=1)
            if guideline_results:
                guidelines_html += "<div>"
                guidelines_html += f"<h4>Related to: {finding.issue_title}</h4>"
                for result in guideline_results:
                    guidelines_html += f"<p><strong>Source:</strong> {result['source']}</p>"
                    guidelines_html += f"<p>{result['text']}</p>"
                guidelines_html += "</div>"

    if not guidelines_html:
        guidelines_html = "<p>No relevant Medicare guidelines found.</p>"

    report_html = report_html.replace("<!-- Placeholder for Medicare guidelines -->", guidelines_html)

    # Embed score and chart
    score_html = f"<p>Overall Compliance Score: {compliance_score:.2f}%</p>"
    chart_html = f'<img src="data:image/png;base64,{chart_base64}" alt="Compliance Chart">'
    report_html = report_html.replace("<!-- Placeholder for compliance score -->", score_html)
    report_html = report_html.replace("<!-- Placeholder for chart -->", chart_html)


    # Clean up the temporary file
    os.remove(temp_file_path)

    return HTMLResponse(content=report_html)
