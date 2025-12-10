import sys
import uuid
from pathlib import Path

import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.core import type_safety


class TestResultBehavior:
    def test_success_and_failure_accessors(self):
        success = type_safety.Result.success(10)
        failure = type_safety.Result.failure(ValueError("boom"))

        assert success.is_success is True
        assert success.is_failure is False
        assert success.value == 10
        with pytest.raises(ValueError):
            _ = success.error

        assert failure.is_success is False
        assert failure.is_failure is True
        assert isinstance(failure.error, ValueError)
        with pytest.raises(ValueError):
            _ = failure.value

    def test_map_and_flat_map_propagate_errors(self):
        success = type_safety.Result.success(3)
        failure = type_safety.Result.failure(ValueError("bad"))

        assert success.map(lambda x: x * 2).value == 6
        mapped_failure = success.map(lambda _: (_ for _ in ()).throw(RuntimeError("oops")))
        assert mapped_failure.is_failure
        assert isinstance(mapped_failure.error, RuntimeError)

        assert failure.map(lambda x: x * 2).is_failure
        assert success.flat_map(lambda x: type_safety.Result.success(str(x))).value == "3"
        assert failure.flat_map(lambda x: type_safety.Result.success(x * 2)).is_failure

    def test_recover_transforms_failures(self):
        original_error = RuntimeError("network")
        failure = type_safety.Result.failure(original_error)

        recovered = failure.recover(lambda err: f"handled: {err}")
        assert recovered.is_success
        assert recovered.value.startswith("handled: network")

        # recovery functions can also fail, surfacing the new exception for observability
        propagated = failure.recover(lambda _: (_ for _ in ()).throw(ValueError("parse")))
        assert propagated.is_failure
        assert isinstance(propagated.error, ValueError)


class TestErrorContextDefaults:
    def test_validation_error_defaults_include_ids_and_severity(self):
        error = type_safety.ValidationError(message="invalid field", field_name="age")

        assert error.message == "invalid field"
        assert error.field_name == "age"
        assert error.severity == type_safety.ErrorSeverity.MEDIUM
        assert error.category == type_safety.ErrorCategory.SYSTEM
        # IDs and timestamps should be generated automatically
        assert uuid.UUID(error.error_id)
        assert error.timestamp.tzinfo is not None


class TestValidators:
    def test_string_validator_handles_required_and_patterns(self):
        validator = type_safety.StringValidator(
            min_length=2, max_length=5, pattern=r"^[A-Z]+$"
        )

        required_failure = validator.validate(None)
        assert required_failure.is_failure
        assert required_failure.error.validation_rule == "required"

        short_failure = validator.validate("A")
        assert short_failure.is_failure
        assert "minimum 2" in short_failure.error.message

        pattern_failure = validator.validate("abcd")
        assert pattern_failure.is_failure
        assert pattern_failure.error.expected_format == validator.pattern

        assert validator.validate("ABCD").is_success

    def test_string_validator_allows_empty_when_configured(self):
        validator = type_safety.StringValidator(required=False, allow_empty=True)

        result = validator.validate("")
        assert result.is_success
        assert result.value == ""

    def test_number_and_email_validators_cover_common_edges(self):
        number_validator = type_safety.NumberValidator(
            min_value=1, max_value=3, integer_only=True
        )

        too_small = number_validator.validate(0)
        assert too_small.is_failure
        assert too_small.error.validation_rule == "min_value"

        too_large = number_validator.validate(10)
        assert too_large.is_failure
        assert too_large.error.validation_rule == "max_value"

        assert number_validator.validate("2").value == 2

        email_validator = type_safety.EmailValidator(required=False)
        assert email_validator.validate(None).is_success

        invalid_email = email_validator.validate("not-an-email")
        assert invalid_email.is_failure
        assert invalid_email.error.expected_format == "user@domain.com"
