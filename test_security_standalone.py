"""
Standalone test for SecurityValidator - runs without pytest fixtures.
"""

from src.core.security_validator import SecurityValidator


def test_all_validators():
    """Run all security validator tests."""
    print("\n=== Testing SecurityValidator ===\n")

    # Filename validation tests
    print("1. Testing filename validation...")
    assert SecurityValidator.validate_filename("document.pdf") == (True, None)
    assert SecurityValidator.validate_filename("../etc/passwd")[0] is False
    assert SecurityValidator.validate_filename("malware.exe")[0] is False
    print("   ✓ Filename validation passed")

    # File size validation tests
    print("2. Testing file size validation...")
    assert SecurityValidator.validate_file_size(1024 * 1024) == (True, None)
    assert SecurityValidator.validate_file_size(0)[0] is False
    assert SecurityValidator.validate_file_size(51 * 1024 * 1024)[0] is False
    print("   ✓ File size validation passed")

    # Discipline validation tests
    print("3. Testing discipline validation...")
    assert SecurityValidator.validate_discipline("pt") == (True, None)
    assert SecurityValidator.validate_discipline("ot") == (True, None)
    assert SecurityValidator.validate_discipline("slp") == (True, None)
    assert SecurityValidator.validate_discipline("invalid")[0] is False
    print("   ✓ Discipline validation passed")

    # Analysis mode validation tests
    print("4. Testing analysis mode validation...")
    assert SecurityValidator.validate_analysis_mode("rubric") == (True, None)
    assert SecurityValidator.validate_analysis_mode("checklist") == (True, None)
    assert SecurityValidator.validate_analysis_mode("hybrid") == (True, None)
    assert SecurityValidator.validate_analysis_mode("invalid")[0] is False
    print("   ✓ Analysis mode validation passed")

    # Text sanitization tests
    print("5. Testing text sanitization...")
    clean_text = "This is a clean clinical note."
    assert SecurityValidator.sanitize_text_input(clean_text) == clean_text
    
    xss_text = "Normal text <script>alert('xss')</script> more text"
    sanitized = SecurityValidator.sanitize_text_input(xss_text)
    assert "<script" not in sanitized.lower()
    
    path_traversal = "File: ../../etc/passwd"
    sanitized = SecurityValidator.sanitize_text_input(path_traversal)
    assert "../" not in sanitized
    print("   ✓ Text sanitization passed")

    # Username validation tests
    print("6. Testing username validation...")
    assert SecurityValidator.validate_username("john_doe") == (True, None)
    assert SecurityValidator.validate_username("user123") == (True, None)
    assert SecurityValidator.validate_username("john-doe") == (True, None)
    assert SecurityValidator.validate_username("john doe")[0] is False
    assert SecurityValidator.validate_username("john@doe")[0] is False
    print("   ✓ Username validation passed")

    # Password validation tests
    print("7. Testing password validation...")
    assert SecurityValidator.validate_password_strength("SecurePass123") == (True, None)
    assert SecurityValidator.validate_password_strength("Pass1")[0] is False
    assert SecurityValidator.validate_password_strength("password123")[0] is False
    assert SecurityValidator.validate_password_strength("PASSWORD123")[0] is False
    assert SecurityValidator.validate_password_strength("PasswordOnly")[0] is False
    print("   ✓ Password validation passed")

    # Filename sanitization tests
    print("8. Testing filename sanitization...")
    assert SecurityValidator.sanitize_filename("document.pdf") == "document.pdf"
    assert SecurityValidator.sanitize_filename("my document.pdf") == "my_document.pdf"
    
    sanitized = SecurityValidator.sanitize_filename("doc@#$ument!.pdf")
    assert "@" not in sanitized
    assert "#" not in sanitized
    
    sanitized = SecurityValidator.sanitize_filename("/path/to/document.pdf")
    assert "/" not in sanitized
    assert sanitized == "document.pdf"
    print("   ✓ Filename sanitization passed")

    print("\n=== All SecurityValidator tests passed! ===\n")


if __name__ == "__main__":
    test_all_validators()
