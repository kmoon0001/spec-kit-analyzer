"""
Unit tests for PDF Export Service.

Tests PDF generation, metadata handling, auto-purge functionality,
and file management operations.
"""

import tempfile
from datetime import UTC, datetime, timedelta
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from src.core.pdf_export_service import WEASYPRINT_AVAILABLE, PDFExportService


@pytest.fixture
def temp_output_dir():
    """Create temporary directory for PDF output."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield tmpdir


@pytest.fixture
def pdf_service(temp_output_dir):
    """Create PDF export service with temporary directory."""
    return PDFExportService(
        output_dir=temp_output_dir,
        retention_hours=24,
        enable_auto_purge=True,
    )


@pytest.fixture
def sample_html():
    """Sample HTML content for testing."""
    return """
    <html>
    <head><title>Test Report</title></head>
    <body>
        <h1>Compliance Report</h1>
        <p>This is a test report.</p>
        <table>
            <tr><th>Finding</th><th>Risk</th></tr>
            <tr><td>Test finding</td><td>High</td></tr>
        </table>
    </body>
    </html>
    """


@pytest.fixture
def sample_metadata():
    """Sample metadata for testing."""
    return {
        "Document": "test_document.pdf",
        "Analysis Date": datetime.now(UTC).isoformat(),
        "Compliance Score": 85,
        "Total Findings": 3,
        "Document Type": "Progress Note",
        "Discipline": "PT",
    }


class TestPDFExportService:
    """Tests for PDF Export Service initialization and configuration."""

    def test_initialization(self, temp_output_dir):
        """Test service initializes with correct configuration."""
        service = PDFExportService(
            output_dir=temp_output_dir,
            retention_hours=48,
            enable_auto_purge=False,
        )

        assert service.output_dir == Path(temp_output_dir)
        assert service.retention_hours == 48
        assert service.enable_auto_purge is False
        assert service.output_dir.exists()

    def test_default_initialization(self):
        """Test service initializes with default values."""
        service = PDFExportService()

        assert service.output_dir == Path("temp/reports")
        assert service.retention_hours == 24
        assert service.enable_auto_purge is True

    def test_output_directory_creation(self, temp_output_dir):
        """Test output directory is created if it doesn't exist."""
        subdir = Path(temp_output_dir) / "nested" / "reports"
        PDFExportService(output_dir=str(subdir))

        assert subdir.exists()
        assert subdir.is_dir()


class TestFilenameSanitization:
    """Tests for filename sanitization."""

    def test_sanitize_simple_filename(self, pdf_service):
        """Test sanitization of simple filename."""
        result = pdf_service._sanitize_filename("document.pdf")
        assert result == "document"

    def test_sanitize_filename_with_spaces(self, pdf_service):
        """Test spaces are replaced with underscores."""
        result = pdf_service._sanitize_filename("my document.pdf")
        assert result == "my_document"

    def test_sanitize_filename_with_special_chars(self, pdf_service):
        """Test special characters are removed."""
        result = pdf_service._sanitize_filename("doc@#$ument!.pdf")
        assert "@" not in result
        assert "#" not in result
        assert "!" not in result

    def test_sanitize_long_filename(self, pdf_service):
        """Test long filenames are truncated."""
        long_name = "a" * 100 + ".pdf"
        result = pdf_service._sanitize_filename(long_name)
        assert len(result) <= 50

    def test_sanitize_empty_filename(self, pdf_service):
        """Test empty filename returns default."""
        result = pdf_service._sanitize_filename("")
        assert result == "document"


@pytest.mark.skipif(not WEASYPRINT_AVAILABLE, reason="weasyprint not installed")
class TestPDFGeneration:
    """Tests for PDF generation functionality."""

    @patch("src.core.pdf_export_service.HTML")
    @patch("src.core.pdf_export_service.CSS")
    def test_export_to_pdf_success(self, mock_css, mock_html, pdf_service, sample_html, sample_metadata):
        """Test successful PDF export."""
        # Mock HTML and CSS objects
        mock_html_instance = MagicMock()
        mock_html.return_value = mock_html_instance

        result = pdf_service.export_to_pdf(
            html_content=sample_html,
            document_name="test_document.pdf",
            metadata=sample_metadata,
        )

        assert result["success"] is True
        assert "pdf_path" in result
        assert "filename" in result
        assert result["filename"].startswith("compliance_report_")
        assert result["filename"].endswith(".pdf")
        assert "file_size" in result
        assert "generated_at" in result

    @patch("src.core.pdf_export_service.HTML")
    def test_export_to_pdf_with_metadata(self, mock_html, pdf_service, sample_html, sample_metadata):
        """Test PDF export includes metadata."""
        mock_html_instance = MagicMock()
        mock_html.return_value = mock_html_instance

        pdf_service.export_to_pdf(
            html_content=sample_html,
            document_name="test_document.pdf",
            metadata=sample_metadata,
        )

        # Check that HTML was called with enhanced content
        call_args = mock_html.call_args
        html_string = call_args[1]["string"]

        # Verify metadata is in HTML
        assert "Report Metadata" in html_string
        assert "test_document.pdf" in html_string
        assert "Progress Note" in html_string

    @patch("src.core.pdf_export_service.HTML")
    def test_export_to_pdf_without_metadata(self, mock_html, pdf_service, sample_html):
        """Test PDF export works without metadata."""
        mock_html_instance = MagicMock()
        mock_html.return_value = mock_html_instance

        result = pdf_service.export_to_pdf(
            html_content=sample_html,
            document_name="test_document.pdf",
            metadata=None,
        )

        assert result["success"] is True

    @patch("src.core.pdf_export_service.HTML", side_effect=Exception("PDF error"))
    def test_export_to_pdf_failure(self, mock_html, pdf_service, sample_html):
        """Test PDF export handles failures gracefully."""
        result = pdf_service.export_to_pdf(
            html_content=sample_html,
            document_name="test_document.pdf",
        )

        assert result["success"] is False
        assert "error" in result
        assert result["pdf_path"] is None

    def test_export_generates_unique_filenames(self, pdf_service, sample_html):
        """Test each export generates unique filename."""
        with patch("src.core.pdf_export_service.HTML"):
            result1 = pdf_service.export_to_pdf(sample_html, "doc.pdf")
            result2 = pdf_service.export_to_pdf(sample_html, "doc.pdf")

            assert result1["filename"] != result2["filename"]


class TestHTMLEnhancement:
    """Tests for HTML enhancement for PDF."""

    def test_enhance_html_adds_metadata(self, pdf_service, sample_metadata):
        """Test HTML enhancement adds metadata section."""
        html = "<h1>Test</h1>"
        enhanced = pdf_service._enhance_html_for_pdf(html, sample_metadata)

        assert "Report Metadata" in enhanced
        assert "test_document.pdf" in enhanced
        assert "Progress Note" in enhanced

    def test_enhance_html_adds_footer(self, pdf_service):
        """Test HTML enhancement adds footer disclaimer."""
        html = "<h1>Test</h1>"
        enhanced = pdf_service._enhance_html_for_pdf(html, None)

        assert "CONFIDENTIAL" in enhanced
        assert "HIPAA Protected" in enhanced
        assert "AI-assisted technology" in enhanced

    def test_enhance_html_adds_styling(self, pdf_service):
        """Test HTML enhancement includes CSS styling."""
        html = "<h1>Test</h1>"
        enhanced = pdf_service._enhance_html_for_pdf(html, None)

        assert "<style>" in enhanced
        assert "risk-high" in enhanced
        assert "confidence-indicator" in enhanced


class TestAutoPurge:
    """Tests for automatic PDF purging functionality."""

    def test_purge_old_pdfs_when_disabled(self, temp_output_dir):
        """Test purge does nothing when disabled."""
        service = PDFExportService(
            output_dir=temp_output_dir,
            enable_auto_purge=False,
        )

        result = service.purge_old_pdfs()

        assert result["purged"] == 0
        assert "Auto-purge disabled" in result["message"]

    def test_purge_old_pdfs_no_files(self, pdf_service):
        """Test purge with no files to purge."""
        result = pdf_service.purge_old_pdfs()

        assert result["purged"] == 0

    def test_purge_old_pdfs_removes_old_files(self, temp_output_dir):
        """Test purge removes files older than retention period."""
        service = PDFExportService(
            output_dir=temp_output_dir,
            retention_hours=1,  # 1 hour retention
        )

        # Create old PDF file
        old_pdf = Path(temp_output_dir) / "old_report.pdf"
        old_pdf.write_text("old content")

        # Set modification time to 2 hours ago
        old_time = (datetime.now(UTC) - timedelta(hours=2)).timestamp()
        old_pdf.touch()
        import os

        os.utime(old_pdf, (old_time, old_time))

        # Create recent PDF file
        recent_pdf = Path(temp_output_dir) / "recent_report.pdf"
        recent_pdf.write_text("recent content")

        result = service.purge_old_pdfs()

        assert result["purged"] == 1
        assert not old_pdf.exists()
        assert recent_pdf.exists()


class TestPDFInfo:
    """Tests for PDF file information retrieval."""

    def test_get_pdf_info_existing_file(self, temp_output_dir):
        """Test getting info for existing PDF."""
        service = PDFExportService(output_dir=temp_output_dir)

        # Create test PDF
        pdf_path = Path(temp_output_dir) / "test.pdf"
        pdf_path.write_text("test content")

        info = service.get_pdf_info(str(pdf_path))

        assert info is not None
        assert info["filename"] == "test.pdf"
        assert info["size_bytes"] > 0
        assert "created_at" in info
        assert "modified_at" in info

    def test_get_pdf_info_nonexistent_file(self, pdf_service):
        """Test getting info for nonexistent PDF returns None."""
        info = pdf_service.get_pdf_info("/nonexistent/file.pdf")
        assert info is None

    def test_list_pdfs_empty_directory(self, pdf_service):
        """Test listing PDFs in empty directory."""
        pdfs = pdf_service.list_pdfs()
        assert pdfs == []

    def test_list_pdfs_with_files(self, temp_output_dir):
        """Test listing PDFs returns all PDF files."""
        service = PDFExportService(output_dir=temp_output_dir)

        # Create test PDFs
        pdf1 = Path(temp_output_dir) / "report1.pdf"
        pdf2 = Path(temp_output_dir) / "report2.pdf"
        pdf1.write_text("content1")
        pdf2.write_text("content2")

        # Create non-PDF file (should be ignored)
        txt_file = Path(temp_output_dir) / "notes.txt"
        txt_file.write_text("notes")

        pdfs = service.list_pdfs()

        assert len(pdfs) == 2
        filenames = [pdf["filename"] for pdf in pdfs]
        assert "report1.pdf" in filenames
        assert "report2.pdf" in filenames
        assert "notes.txt" not in filenames


class TestPDFStyles:
    """Tests for PDF styling and formatting."""

    def test_pdf_css_includes_page_settings(self, pdf_service):
        """Test PDF CSS includes page size and margins."""
        css = pdf_service.pdf_css

        assert "@page" in css
        assert "size: Letter" in css
        assert "margin:" in css

    def test_pdf_css_includes_headers_footers(self, pdf_service):
        """Test PDF CSS includes header and footer content."""
        css = pdf_service.pdf_css

        assert "@top-left" in css
        assert "@top-right" in css
        assert "@bottom-center" in css
        assert "@bottom-right" in css
        assert "CONFIDENTIAL" in css

    def test_pdf_css_includes_risk_styling(self, pdf_service):
        """Test PDF CSS includes risk level styling."""
        css = pdf_service.pdf_css

        assert ".risk-high" in css
        assert ".risk-medium" in css
        assert ".risk-low" in css

    def test_pdf_css_includes_confidence_styling(self, pdf_service):
        """Test PDF CSS includes confidence level styling."""
        css = pdf_service.pdf_css

        assert ".high-confidence" in css
        assert ".medium-confidence" in css
        assert ".low-confidence" in css
        assert ".disputed" in css


@pytest.mark.skipif(not WEASYPRINT_AVAILABLE, reason="weasyprint not installed")
class TestRetentionAndPurge:
    """Tests for retention policy and purge scheduling."""

    @patch("src.core.pdf_export_service.HTML")
    def test_export_sets_purge_time(self, mock_html, pdf_service, sample_html):
        """Test export sets purge time when auto-purge enabled."""
        mock_html_instance = MagicMock()
        mock_html.return_value = mock_html_instance

        result = pdf_service.export_to_pdf(sample_html, "test.pdf")

        assert result["purge_at"] is not None
        purge_time = datetime.fromisoformat(result["purge_at"])
        expected_purge = datetime.now(UTC) + timedelta(hours=24)

        # Allow 1 minute tolerance
        assert abs((purge_time - expected_purge).total_seconds()) < 60

    @patch("src.core.pdf_export_service.HTML")
    def test_export_no_purge_time_when_disabled(self, mock_html, temp_output_dir, sample_html):
        """Test export doesn't set purge time when auto-purge disabled."""
        service = PDFExportService(
            output_dir=temp_output_dir,
            enable_auto_purge=False,
        )

        mock_html_instance = MagicMock()
        mock_html.return_value = mock_html_instance

        result = service.export_to_pdf(sample_html, "test.pdf")

        assert result["purge_at"] is None
