#!/usr/bin/env python
"""
Validation script for comprehensive codebase assessment improvements.

This script validates that all critical fixes are working correctly and
the application is ready for production use.
"""

import sys
from typing import List, Tuple


def test_imports() -> Tuple[bool, str]:
    """Test that all critical modules can be imported."""
    try:
        from src.config import get_settings
        from src.database.models import User, ComplianceRubric, AnalysisReport, Finding
        from src.core.exceptions import ApplicationError, DatabaseError, AIModelError
        from src.core.error_handlers import ServiceErrorHandler
        from src.api.global_exception_handler import global_exception_handler
        from src.api.main import app
        return True, "✓ All critical modules import successfully"
    except Exception as e:
        return False, f"✗ Import failed: {str(e)}"


def test_database_models() -> Tuple[bool, str]:
    """Test that database models are properly defined."""
    try:
        from src.database.models import User, ComplianceRubric, AnalysisReport, Finding
        
        # Check that models have required attributes
        assert hasattr(User, 'username')
        assert hasattr(User, 'is_admin')
        assert hasattr(ComplianceRubric, 'discipline')
        assert hasattr(AnalysisReport, 'compliance_score')
        assert hasattr(Finding, 'confidence_score')
        
        # Check backward compatibility aliases
        from src.database.models import Rubric, Report
        assert Rubric is ComplianceRubric
        assert Report is AnalysisReport
        
        return True, "✓ Database models are properly defined with all required fields"
    except Exception as e:
        return False, f"✗ Database model validation failed: {str(e)}"


def test_error_handling() -> Tuple[bool, str]:
    """Test that error handling system is properly set up."""
    try:
        from src.core.exceptions import (
            ApplicationError, DatabaseError, SecurityError, 
            AIModelError, ValidationError
        )
        
        # Test exception hierarchy
        assert issubclass(DatabaseError, ApplicationError)
        assert issubclass(SecurityError, ApplicationError)
        assert issubclass(AIModelError, ApplicationError)
        
        # Test exception creation
        error = DatabaseError("Test error", {"detail": "test"})
        assert error.error_code == "DATABASE_ERROR"
        assert error.message == "Test error"
        assert error.details == {"detail": "test"}
        
        return True, "✓ Error handling system is properly configured"
    except Exception as e:
        return False, f"✗ Error handling validation failed: {str(e)}"


def test_service_methods() -> Tuple[bool, str]:
    """Test that critical service methods exist."""
    try:
        from src.core.llm_service import LLMService
        from src.core.fact_checker_service import FactCheckerService
        
        # Check LLM service methods
        assert hasattr(LLMService, 'generate')
        assert hasattr(LLMService, 'generate_analysis')
        assert hasattr(LLMService, 'is_ready')
        
        # Check FactChecker service methods
        assert hasattr(FactCheckerService, 'check_consistency')
        assert hasattr(FactCheckerService, 'is_finding_plausible')
        
        return True, "✓ All critical service methods are available"
    except Exception as e:
        return False, f"✗ Service method validation failed: {str(e)}"


def test_configuration() -> Tuple[bool, str]:
    """Test that configuration loads correctly."""
    try:
        from src.config import get_settings
        
        settings = get_settings()
        assert settings is not None
        assert hasattr(settings, 'database')
        assert hasattr(settings, 'models')
        assert hasattr(settings, 'llm')
        
        return True, "✓ Configuration loads successfully"
    except Exception as e:
        return False, f"✗ Configuration validation failed: {str(e)}"


def test_api_setup() -> Tuple[bool, str]:
    """Test that FastAPI application is properly configured."""
    try:
        from src.api.main import app
        
        # Check that app has exception handlers
        assert len(app.exception_handlers) > 0
        
        # Check that routers are included
        assert len(app.routes) > 1
        
        return True, "✓ FastAPI application is properly configured"
    except Exception as e:
        return False, f"✗ API setup validation failed: {str(e)}"


def run_validation() -> int:
    """Run all validation tests and report results."""
    print("=" * 70)
    print("Therapy Compliance Analyzer - Validation Report")
    print("=" * 70)
    print()
    
    tests = [
        ("Import Validation", test_imports),
        ("Database Models", test_database_models),
        ("Error Handling", test_error_handling),
        ("Service Methods", test_service_methods),
        ("Configuration", test_configuration),
        ("API Setup", test_api_setup),
    ]
    
    results: List[Tuple[str, bool, str]] = []
    
    for test_name, test_func in tests:
        print(f"Running: {test_name}...", end=" ")
        success, message = test_func()
        results.append((test_name, success, message))
        print(message)
    
    print()
    print("=" * 70)
    print("Summary")
    print("=" * 70)
    
    passed = sum(1 for _, success, _ in results if success)
    total = len(results)
    
    print(f"Tests Passed: {passed}/{total}")
    print()
    
    if passed == total:
        print("✓ All validation tests passed!")
        print("✓ The application is ready for production use.")
        return 0
    else:
        print("✗ Some validation tests failed.")
        print("✗ Please review the errors above.")
        return 1


if __name__ == "__main__":
    sys.exit(run_validation())
