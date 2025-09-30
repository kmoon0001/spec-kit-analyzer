import logging
import os
from unittest.mock import MagicMock
from src.core.pipeline import DocumentProcessingPipeline
from src.core.document_processing_service import DocumentProcessingService
from src.core.phi_scrubber import PhiScrubberService
from src.core.clinical_entity_service import ClinicalEntityService
from src.core.medicare_compliance_service import MedicareComplianceService
from src.core.bias_detection_service import BiasDetectionService
from src.core.quality_assurance_service import QualityAssuranceService
from src.core.audit_trail_service import AuditTrailService
from src.core.report_generator import ReportGenerator

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def main():
    # Initialize services
    doc_service = DocumentProcessingService(config={})

    phi_scrubber_config = {
        "redaction_style": "placeholder",
        "ner_labels": ["PERSON", "DATE", "GPE"]
    }
    phi_service = PhiScrubberService(config=phi_scrubber_config)

    clinical_entity_service = ClinicalEntityService(config={})
    bias_detection_service = BiasDetectionService(config={})
    quality_assurance_service = QualityAssuranceService(config={})

    audit_log_file = "test_audit_trail.log"
    if os.path.exists(audit_log_file):
        os.remove(audit_log_file)
    audit_trail_service = AuditTrailService(config={"audit_log_file": audit_log_file})

    mock_compliance_analyzer = MagicMock()
    mock_compliance_analyzer.analyze_document.return_value = {
        "findings": [
            {"risk": "High", "text": "Sample finding 1", "rule_id": "signature_rule", "suggestion": "Ensure the therapist signs the document."},
            {"risk": "Medium", "text": "Sample finding 2", "rule_id": "goals_rule", "suggestion": "This is a recommendation for a young person to improve strength."},
        ],
        "summary": "This is a mock analysis summary.",
        "overall_confidence": 0.85,
    }

    medicare_scorer = MedicareComplianceService(config={})
    report_generator = ReportGenerator()

    # Create the pipeline
    pipeline = DocumentProcessingPipeline(
        document_processing_service=doc_service,
        phi_scrubber_service=phi_service,
        clinical_entity_service=clinical_entity_service,
        compliance_analyzer=mock_compliance_analyzer,
        medicare_compliance_service=medicare_scorer,
        bias_detection_service=bias_detection_service,
        quality_assurance_service=quality_assurance_service,
        audit_trail_service=audit_trail_service,
        report_generator=report_generator
    )

    # Example: Run the pipeline with a dummy document
    try:
        with open("dummy_document.txt", "w") as f:
            f.write("This is a test document from Dr. Smith regarding patient John Doe, born on 01/01/1950. The patient reports pain and decreased range of motion.")

        result = pipeline.run("dummy_document.txt", "txt")

        if result and "error" not in result:
            logging.info("Pipeline completed successfully!")

            final_report_html = result.get('report', {}).get('report_html', 'Not available')
            # A more robust way to check the end of the report for the new section
            logging.info(f"\n--- End of Report ---\n{final_report_html[-500:]}")
            logging.info("--- End of Report Log ---\n")
        else:
            logging.error(f"Pipeline failed. Result: {result}")

    except Exception as e:
        logging.error(f"An unexpected error occurred: {e}", exc_info=True)

if __name__ == "__main__":
    main()