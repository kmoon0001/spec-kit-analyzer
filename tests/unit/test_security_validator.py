"""
Unit tests for SecurityValidator.

Tests all security validation functions including file validation,
input sanitization, and password strength checking.
"""

from src.core.security_validator import SecurityValidator


class TestFilenameValidation:
    """Tests for filename validation."""

    def test_valid_pdf_filename(self):
        """Test valid PDF filename passes validation."""
        is_valid, error = SecurityValidator.validate_filename("document.pdf")
        assert is_valid is True
        assert error is None

    def test_valid_docx_filename(self):
        """Test valid DOCX filename passes validation."""
        is_valid, error = SecurityValidator.validate_filename("report.docx")
        assert is_valid is True
        assert error is None

    def test_valid_txt_filename(self):
        """Test valid TXT filename passes validation."""
        is_valid, error = SecurityValidator.validate_filename("notes.txt")
        assert is_valid is True
        assert error is None

    def test_empty_filename(self):
        """Test empty filename is rejected."""
        is_valid, error = SecurityValidator.validate_filename("")
        assert is_valid is False
        assert "required" in error.lower()

    def test_path_traversal_dots(self):
        """Test path traversal with .. is blocked."""
        is_valid, error = SecurityValidator.validate_filename("../etc/passwd")
        assert is_valid is False
        assert "path traversal" in error.lower()

    def test_path_traversal_forward_slash(self):
        """Test path traversal with / is blocked."""
        is_valid, error = SecurityValidator.validate_filename("dir/file.pdf")
        assert is_valid is False
        assert "path traversal" in error.lower()

    def test_path_traversal_backslash(self):
        """Test path traversal with \\ is blocked."""
        is_valid, error = SecurityValidator.validate_filename("dir\\file.pdf")
        assert is_valid is False
        assert "path traversal" in error.lower()

    def test_invalid_extension(self):
        """Test invalid file extension is rejected."""
        is_valid, error = SecurityValidator.validate_filename("malware.exe")
        assert is_valid is False
        assert "not allowed" in error.lower()

    def test_filename_too_long(self):
        """Test excessively long filename is rejected."""
        long_name = "a" * 300 + ".pdf"
        is_valid, error = SecurityValidator.validate_filename(long_name)
        assert is_valid is False
        assert "maximum length" in error.lower()

    def test_case_insensitive_extension(self):
        """Test file extension validation is case-insensitive."""
        is_valid, error = SecurityValidator.validate_filename("Document.PDF")
        assert is_valid is True
        assert error is None


class TestFileSizeValidation:
    """Tests for file size validation."""

    def test_valid_file_size(self):
        """Test valid file size passes validation."""
        is_valid, error = SecurityValidator.validate_file_size(1024 * 1024)  # 1MB
        assert is_valid is True
        assert error is None

    def test_empty_file(self):
        """Test empty file is rejected."""
        is_valid, error = SecurityValidator.validate_file_size(0)
        assert is_valid is False
        assert "empty" in error.lower()

    def test_file_too_large(self):
        """Test file exceeding size limit is rejected."""
        too_large = 51 * 1024 * 1024  # 51MB
        is_valid, error = SecurityValidator.validate_file_size(too_large)
        assert is_valid is False
        assert "exceeds maximum" in error.lower()

    def test_max_file_size_boundary(self):
        """Test file at exact size limit passes."""
        max_size = SecurityValidator.MAX_FILE_SIZE_BYTES
        is_valid, error = SecurityValidator.validate_file_size(max_size)
        assert is_valid is True
        assert error is None


class TestDisciplineValidation:
    """Tests for discipline parameter validation."""

    def test_valid_pt_discipline(self):
        """Test PT discipline is valid."""
        is_valid, error = SecurityValidator.validate_discipline("pt")
        assert is_valid is True
        assert error is None

    def test_valid_ot_discipline(self):
        """Test OT discipline is valid."""
        is_valid, error = SecurityValidator.validate_discipline("ot")
        assert is_valid is True
        assert error is None

    def test_valid_slp_discipline(self):
        """Test SLP discipline is valid."""
        is_valid, error = SecurityValidator.validate_discipline("slp")
        assert is_valid is True
        assert error is None

    def test_case_insensitive_discipline(self):
        """Test discipline validation is case-insensitive."""
        is_valid, error = SecurityValidator.validate_discipline("PT")
        assert is_valid is True
        assert error is None

    def test_invalid_discipline(self):
        """Test invalid discipline is rejected."""
        is_valid, error = SecurityValidator.validate_discipline("invalid")
        assert is_valid is False
        assert "invalid discipline" in error.lower()

    def test_empty_discipline(self):
        """Test empty discipline is rejected."""
        is_valid, error = SecurityValidator.validate_discipline("")
        assert is_valid is False
        assert "required" in error.lower()


class TestAnalysisModeValidation:
    """Tests for analysis mode validation."""

    def test_valid_rubric_mode(self):
        """Test rubric mode is valid."""
        is_valid, error = SecurityValidator.validate_analysis_mode("rubric")
        assert is_valid is True
        assert error is None

    def test_valid_checklist_mode(self):
        """Test checklist mode is valid."""
        is_valid, error = SecurityValidator.validate_analysis_mode("checklist")
        assert is_valid is True
        assert error is None

    def test_valid_hybrid_mode(self):
        """Test hybrid mode is valid."""
        is_valid, error = SecurityValidator.validate_analysis_mode("hybrid")
        assert is_valid is True
        assert error is None

    def test_case_insensitive_mode(self):
        """Test mode validation is case-insensitive."""
        is_valid, error = SecurityValidator.validate_analysis_mode("RUBRIC")
        assert is_valid is True
        assert error is None

    def test_invalid_mode(self):
        """Test invalid mode is rejected."""
        is_valid, error = SecurityValidator.validate_analysis_mode("invalid")
        assert is_valid is False
        assert "invalid" in error.lower()

    def test_empty_mode(self):
        """Test empty mode is rejected."""
        is_valid, error = SecurityValidator.validate_analysis_mode("")
        assert is_valid is False
        assert "required" in error.lower()


class TestTextSanitization:
    """Tests for text input sanitization."""

    def test_clean_text_unchanged(self):
        """Test clean text passes through unchanged."""
        text = "This is a clean clinical note."
        result = SecurityValidator.sanitize_text_input(text)
        assert result == text

    def test_script_tag_removed(self):
        """Test script tags are removed."""
        text = "Normal text <script>alert('xss')</script> more text"
        result = SecurityValidator.sanitize_text_input(text)
        assert "<script" not in result.lower()

    def test_javascript_protocol_removed(self):
        """Test javascript: protocol is removed."""
        text = "Click here: javascript:alert('xss')"
        result = SecurityValidator.sanitize_text_input(text)
        assert "javascript:" not in result.lower()

    def test_onerror_attribute_removed(self):
        """Test onerror attribute is removed."""
        text = '<img src=x onerror="alert(1)">'
        result = SecurityValidator.sanitize_text_input(text)
        assert "onerror=" not in result.lower()

    def test_path_traversal_removed(self):
        """Test path traversal patterns are removed."""
        text = "File: ../../etc/passwd"
        result = SecurityValidator.sanitize_text_input(text)
        assert "../" not in result

    def test_empty_text_returns_empty(self):
        """Test empty text returns empty string."""
        result = SecurityValidator.sanitize_text_input("")
        assert result == ""

    def test_text_length_limit_enforced(self):
        """Test text is truncated to max length."""
        long_text = "a" * 20000
        result = SecurityValidator.sanitize_text_input(long_text)
        assert len(result) <= SecurityValidator.MAX_TEXT_INPUT_LENGTH

    def test_custom_max_length(self):
        """Test custom max length is respected."""
        text = "a" * 1000
        result = SecurityValidator.sanitize_text_input(text, max_length=100)
        assert len(result) == 100


class TestUsernameValidation:
    """Tests for username validation."""

    def test_valid_username(self):
        """Test valid username passes validation."""
        is_valid, error = SecurityValidator.validate_username("john_doe")
        assert is_valid is True
        assert error is None

    def test_username_with_numbers(self):
        """Test username with numbers is valid."""
        is_valid, error = SecurityValidator.validate_username("user123")
        assert is_valid is True
        assert error is None

    def test_username_with_hyphen(self):
        """Test username with hyphen is valid."""
        is_valid, error = SecurityValidator.validate_username("john-doe")
        assert is_valid is True
        assert error is None

    def test_empty_username(self):
        """Test empty username is rejected."""
        is_valid, error = SecurityValidator.validate_username("")
        assert is_valid is False
        assert "required" in error.lower()

    def test_username_with_spaces(self):
        """Test username with spaces is rejected."""
        is_valid, error = SecurityValidator.validate_username("john doe")
        assert is_valid is False
        assert "letters, numbers" in error.lower()

    def test_username_with_special_chars(self):
        """Test username with special characters is rejected."""
        is_valid, error = SecurityValidator.validate_username("john@doe")
        assert is_valid is False
        assert "letters, numbers" in error.lower()

    def test_username_too_long(self):
        """Test excessively long username is rejected."""
        long_username = "a" * 100
        is_valid, error = SecurityValidator.validate_username(long_username)
        assert is_valid is False
        assert "maximum length" in error.lower()


class TestPasswordValidation:
    """Tests for password strength validation."""

    def test_valid_strong_password(self):
        """Test strong password passes validation."""
        is_valid, error = SecurityValidator.validate_password_strength("SecurePass123")
        assert is_valid is True
        assert error is None

    def test_empty_password(self):
        """Test empty password is rejected."""
        is_valid, error = SecurityValidator.validate_password_strength("")
        assert is_valid is False
        assert "required" in error.lower()

    def test_password_too_short(self):
        """Test password shorter than 8 characters is rejected."""
        is_valid, error = SecurityValidator.validate_password_strength("Pass1")
        assert is_valid is False
        assert "at least 8 characters" in error.lower()

    def test_password_no_uppercase(self):
        """Test password without uppercase is rejected."""
        is_valid, error = SecurityValidator.validate_password_strength("password123")
        assert is_valid is False
        assert "uppercase" in error.lower()

    def test_password_no_lowercase(self):
        """Test password without lowercase is rejected."""
        is_valid, error = SecurityValidator.validate_password_strength("PASSWORD123")
        assert is_valid is False
        assert "lowercase" in error.lower()

    def test_password_no_digit(self):
        """Test password without digit is rejected."""
        is_valid, error = SecurityValidator.validate_password_strength("PasswordOnly")
        assert is_valid is False
        assert "digit" in error.lower()

    def test_password_too_long(self):
        """Test excessively long password is rejected."""
        long_password = "A1" + "a" * 200
        is_valid, error = SecurityValidator.validate_password_strength(long_password)
        assert is_valid is False
        assert "maximum length" in error.lower()

    def test_password_with_special_chars(self):
        """Test password with special characters is valid."""
        is_valid, error = SecurityValidator.validate_password_strength("Secure@Pass123!")
        assert is_valid is True
        assert error is None


class TestFilenameSanitization:
    """Tests for filename sanitization."""

    def test_clean_filename_unchanged(self):
        """Test clean filename passes through unchanged."""
        filename = "document.pdf"
        result = SecurityValidator.sanitize_filename(filename)
        assert result == filename

    def test_spaces_replaced_with_underscores(self):
        """Test spaces are replaced with underscores."""
        filename = "my document.pdf"
        result = SecurityValidator.sanitize_filename(filename)
        assert result == "my_document.pdf"

    def test_special_chars_removed(self):
        """Test special characters are removed."""
        filename = "doc@#$ument!.pdf"
        result = SecurityValidator.sanitize_filename(filename)
        assert "@" not in result
        assert "#" not in result
        assert "!" not in result

    def test_path_stripped(self):
        """Test path components are stripped."""
        filename = "/path/to/document.pdf"
        result = SecurityValidator.sanitize_filename(filename)
        assert "/" not in result
        assert result == "document.pdf"

    def test_long_filename_truncated(self):
        """Test long filename is truncated while preserving extension."""
        long_name = "a" * 300 + ".pdf"
        result = SecurityValidator.sanitize_filename(long_name)
        assert len(result) <= SecurityValidator.MAX_FILENAME_LENGTH
        assert result.endswith(".pdf")

    def test_unicode_characters_handled(self):
        """Test unicode characters are handled properly."""
        filename = "document_résumé.pdf"
        result = SecurityValidator.sanitize_filename(filename)
        # Should preserve alphanumeric and basic punctuation
        assert ".pdf" in result
