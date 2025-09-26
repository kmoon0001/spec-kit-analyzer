import pytest
from unittest.mock import patch, MagicMock

@pytest.fixture(autouse=True, scope="session")
def mock_model_loading():
    """
    Globally mocks the Hugging Face model downloader to prevent
    tests from failing due to network or disk space issues.
    This patch is active for the entire test session.
    """
    # Patch the function responsible for downloading the model
    patcher = patch('ctransformers.AutoModelForCausalLM.from_pretrained', return_value=MagicMock())

    # Start the patch
    patcher.start()

    # Yield control to the test session
    yield

    # Stop the patch after all tests are done
    patcher.stop()