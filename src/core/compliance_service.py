import logging
from typing import List, Dict, Any

from ..database import get_async_db
from ..database import crud
from ..core.analysis_service import AnalysisService

logger = logging.getLogger(__name__)

class ComplianceService:
    def __init__(self, analysis_service: AnalysisService):
        logger.info("Initializing ComplianceService with injected AnalysisService...")
        self.analysis_service = analysis_service
        logger.info("ComplianceService initialized.")

    @staticmethod
    async def get_available_rubrics() -> List[Dict[str, Any]]:
        logger.info("Fetching available rubrics.")
        async for db in get_async_db():
            try:
                rubrics = await crud.get_rubrics(db)
                return [{"id": r.id, "name": r.name, "description": r.description} for r in rubrics]
            finally:
                await db.close()

    async def run_compliance_analysis(self, document_path: str, discipline: str, rubric_id: int) -> Dict[str, Any]:
        logger.info(f"Running compliance analysis for document: {document_path} with discipline: {discipline} and rubric ID: {rubric_id}")
        analysis_result = await self.analysis_service.analyze_document(
            file_path=document_path,
            discipline=discipline,
            analysis_mode="rubric" # Assuming rubric mode for now
        )
        return analysis_result