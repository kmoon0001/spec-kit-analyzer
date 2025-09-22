import pytest
from src.ner_service import NERService

def test_service_instantiation():
    """
    Tests that the NERService can be instantiated.
    """
    service = NERService(model_configs={})
    assert service is not None
