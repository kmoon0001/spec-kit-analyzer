import logging
from typing import Dict, Any, Tuple, List

from src.core.risk_scoring_service import RiskScoringService

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ReportGenerator:
    """
    This class is responsible for generating the final report data structure
    and calculating the compliance score.
    """
    def __init__(self):
        """
        Initializes the ReportGenerator with a scoring service.
        """
        self.scoring_service = RiskScoringService()
        logger.info("ReportGenerator initialized.")

    def generate_report(self, doc_name: str, analysis_result: Dict) -> Tuple[Dict, List]:
        """
        Generates the final report data and calculates the compliance score.

        Args:
            doc_name: The name of the document.
            analysis_result: The raw analysis from the LLM.

        Returns:
            A tuple containing the report data dictionary and a list of findings.
        """
        findings = analysis_result.get("findings", [])

        # Calculate the compliance score based on the findings
        compliance_score = self.scoring_service.calculate_compliance_score(findings)

        # Prepare the report data for database storage
        report_data = {
            "document_name": doc_name,
            "compliance_score": compliance_score,
            "analysis_result": analysis_result,
        }

        # Prepare the findings data for database storage
        findings_data = [
            {
                "rule_id": finding.get("rule_id", "N/A"),
                "problematic_text": finding.get("text", ""),
                "risk": finding.get("risk", "Unknown"),
                "personalized_tip": finding.get("suggestion", "")
            }
            for finding in findings
        ]

        logger.info(f"Generated report for {doc_name} with score: {compliance_score}")
        return report_data, findings_data