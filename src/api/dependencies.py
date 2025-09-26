from fastapi import Request

def get_analysis_service(request: Request):
    """
    Dependency to get the singleton AnalysisService instance from the app state.
    """
    return request.app.state.analysis_service