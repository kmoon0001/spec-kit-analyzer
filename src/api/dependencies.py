from ..core.analysis_service import AnalysisService

# This dictionary will hold our singleton instances
app_state = {}

def get_analysis_service() -> AnalysisService:
    """Dependency to get the singleton AnalysisService instance."""
    return app_state.get('analysis_service')