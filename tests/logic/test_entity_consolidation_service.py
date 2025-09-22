import pytest
from src.entity_consolidation_service import EntityConsolidationService

def test_service_instantiation():
    """
    Tests that the EntityConsolidationService can be instantiated.
    """
    service = EntityConsolidationService()
    assert service is not None