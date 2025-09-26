from typing import Dict
from ..core.analysis_service import AnalysisService

# This dictionary will hold our singleton instances
app_state: Dict[str, AnalysisService] = {}

def get_analysis_service() -> AnalysisService:
    """
    Dependency to get the singleton AnalysisService instance.
    Raises a RuntimeError if the service is not available.
    """
    service = app_state.get('analysis_service')
    if service is None:
        # This should not happen in a running application, as the service
        # is created at startup. This is a safeguard.
        raise RuntimeError("AnalysisService not initialized.")
    return service