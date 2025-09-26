import logging
from typing import List, Dict, Any

from ..database import get_db
from ..crud import get_rubrics
from ..core.analysis_service import AnalysisService

logger = logging.getLogger(__name__)

class ComplianceService:
    def __init__(self, analysis_service: AnalysisService):
        logger.info("Initializing ComplianceService with injected AnalysisService...")
        self.analysis_service = analysis_service
        logger.info("ComplianceService initialized.")

    def get_available_rubrics(self) -> List[Dict[str, Any]]:
        logger.info("Fetching available rubrics.")
        with get_db() as db:
            rubrics = get_rubrics(db)
            return [{"id": r.id, "name": r.name, "description": r.description} for r in rubrics]

    def run_compliance_analysis(self, document_path: str, discipline: str, rubric_id: int) -> Dict[str, Any]:
        logger.info(f"Running compliance analysis for document: {document_path} with discipline: {discipline} and rubric ID: {rubric_id}")
        analysis_result = self.analysis_service.analyze_document(
            file_path=document_path,
            discipline=discipline,
            analysis_mode="rubric" # Assuming rubric mode for now
        )
        return analysis_result