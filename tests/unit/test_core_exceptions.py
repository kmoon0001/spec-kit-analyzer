from src.core import exceptions


def test_application_error_defaults():
    err = exceptions.ApplicationError("Problem occurred")
    assert err.message == "Problem occurred"
    assert err.error_code == "APPLICATION_ERROR"
    assert err.details == {}


def test_ai_model_error_sets_model_name_and_code():
    err = exceptions.AIModelError("Model failed", model_name="gpt-4")
    assert err.model_name == "gpt-4"
    assert err.error_code == "AI_MODEL_ERROR"
    assert isinstance(err, exceptions.ApplicationError)
