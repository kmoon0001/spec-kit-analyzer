"""
Tests for PDF export functionality.
"""

import pytest
from unittest.mock import patch
from src.core.pdf_export_service import PDFExportService, PDFExportError


class TestPDFExportService:
    """Test suite for PDF export service."""
    
    @pytest.fixture
    def pdf_service(self):
        """Create PDF export service instance."""
        return PDFExportService()
    
    @pytest.fixture
    def sample_report_data(self):
        """Sample report data for testing."""
        return {
            "title": "Test Compliance Report",
            "generated_at": "2024-01-15T10:30:00",
            "findings": [
                {
                    "rule_id": "TEST_001",
                    "risk_level": "high",
                    "evidence": "Test evidence text",
                    "issue": "Test compliance issue",
                    "recommendation": "Test recommendation",
                    "confidence_score": 0.85
                }
            ],
            "compliance_score": 87.5,
            "document_name": "test_document.txt"
        }
    
    def test_initialization(self, pdf_service):
        """Test PDF service initialization."""
        assert pdf_service is not None
        assert pdf_service.template_engine is not None
        assert pdf_service.pdf_settings is not None
    
    @patch('src.core.pdf_export_service.WEASYPRINT_AVAILABLE', False)
    async def test_export_without_weasyprint(self, pdf_service, sample_report_data):
        """Test PDF export when WeasyPrint is not available."""
        with pytest.raises(PDFExportError, match="PDF export requires WeasyPrint"):
            await pdf_service.export_report_to_pdf(sample_report_data)
    
    def test_validate_report_data_success(self, pdf_service, sample_report_data):
        """Test successful report data validation."""
        # Should not raise exception
        pdf_service._validate_report_data(sample_report_data)
    
    def test_validate_report_data_missing_fields(self, pdf_service):
        """Test report data validation with missing fields."""
        invalid_data = {"title": "Test"}  # Missing required fields
        
        with pytest.raises(ValueError, match="missing required fields"):
            pdf_service._validate_report_data(invalid_data)
    
    async def test_prepare_pdf_data(self, pdf_service, sample_report_data):
        """Test PDF data preparation."""
        pdf_data = await pdf_service._prepare_pdf_data(
            sample_report_data, 
            include_charts=True, 
            watermark="CONFIDENTIAL"
        )
        
        assert pdf_data["export_format"] == "PDF"
        assert pdf_data["include_charts"] is True
        assert pdf_data["watermark"] == "CONFIDENTIAL"
        assert "export_timestamp" in pdf_data
    
    def test_get_pdf_css_styles(self, pdf_service):
        """Test PDF CSS styles generation."""
        css = pdf_service._get_pdf_css_styles()
        
        assert "@page" in css
        assert "font-family" in css
        assert ".finding" in css
        assert ".high-risk" in css
    
    async def test_convert_charts_for_pdf(self, pdf_service):
        """Test chart conversion for PDF."""
        charts = [
            {"title": "Test Chart", "data": [1, 2, 3]},
            {"title": "Another Chart", "data": [4, 5, 6]}
        ]
        
        converted = await pdf_service._convert_charts_for_pdf(charts)
        
        assert len(converted) == 2
        for chart in converted:
            assert "image_data" in chart
            assert chart["image_data"].startswith("data:image/png;base64,")
    
    def test_optimize_content_for_print(self, pdf_service, sample_report_data):
        """Test content optimization for print layout."""
        # Add many findings to trigger grouping
        sample_report_data["findings"] = [
            {"rule_id": f"TEST_{i:03d}", "risk_level": "medium"} 
            for i in range(15)
        ]
        
        optimized = pdf_service._optimize_content_for_print(sample_report_data)
        
        assert "grouped_findings" in optimized
        assert len(optimized["grouped_findings"]) == 3  # 15 findings / 5 per group
    
    def test_combine_reports_data(self, pdf_service, sample_report_data):
        """Test combining multiple reports."""
        reports = [sample_report_data, sample_report_data.copy()]
        reports[1]["title"] = "Second Report"
        
        combined = pdf_service._combine_reports_data(reports)
        
        assert combined["report_count"] == 2
        assert "Combined Compliance Analysis Report" in combined["title"]
        assert len(combined["findings"]) == 2  # One from each report
        assert "combined_metrics" in combined
    
    def test_calculate_combined_metrics(self, pdf_service, sample_report_data):
        """Test combined metrics calculation."""
        reports = [
            {**sample_report_data, "compliance_score": 85.0},
            {**sample_report_data, "compliance_score": 90.0}
        ]
        
        metrics = pdf_service._calculate_combined_metrics(reports)
        
        assert metrics["total_findings"] == 2
        assert metrics["average_compliance_score"] == 87.5
        assert metrics["report_count"] == 2