import pytest
from backend.app.guideline_service import GuidelineService

def test_service_instantiation():
    """
    Tests that the GuidelineService can be instantiated.
    """
    service = GuidelineService()
    assert service is not None
