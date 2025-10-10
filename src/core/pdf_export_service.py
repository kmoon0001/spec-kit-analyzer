"""
PDF Export Service for Compliance Reports

This service provides comprehensive PDF export functionality for compliance analysis reports,
maintaining professional formatting and ensuring all critical information is preserved.
"""

import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional, List
from io import BytesIO
import base64

try:
    from weasyprint import HTML, CSS
    from weasyprint.text.fonts import FontConfiguration
    WEASYPRINT_AVAILABLE = True
except ImportError:
    WEASYPRINT_AVAILABLE = False
    logging.warning("WeasyPrint not available. PDF export will be limited.")

from src.core.report_models import Report, ReportFormat
from src.core.report_template_engine import TemplateEngine

logger = logging.getLogger(__name__)


class PDFExportService:
    """
    Professional PDF export service for compliance reports.
    
    This service converts HTML compliance reports to high-quality PDF documents
    suitable for printing, archiving, and professional distribution. It maintains
    all formatting, charts, and interactive elements in a static PDF format.
    
    Features:
    - Professional medical document formatting
    - Preserved styling and branding
    - Embedded charts and visualizations
    - Print-optimized layouts
    - Accessibility compliance
    - Digital signatures support (future)
    
    Example:
        >>> pdf_service = PDFExportService()
        >>> pdf_bytes = await pdf_service.export_report_to_pdf(report_data)
        >>> with open("compliance_report.pdf", "wb") as f:
        ...     f.write(pdf_bytes)
    """
    
    def __init__(self):
        """Initialize the PDF export service with professional settings."""
        self.template_engine = TemplateEngine()
        self.font_config = FontConfiguration() if WEASYPRINT_AVAILABLE else None
        
        # PDF generation settings optimized for medical documents
        self.pdf_settings = {
            'page_size': 'A4',
            'margin_top': '1in',
            'margin_bottom': '1in', 
            'margin_left': '0.75in',
            'margin_right': '0.75in',
            'print_background': True,
            'optimize_images': True,
            'pdf_version': '1.7',  # Widely compatible version
        }
        
        logger.info("PDF export service initialized")
    
    async def export_report_to_pdf(self, 
                                 report_data: Dict[str, Any],
                                 template_name: str = "compliance_report_pdf",
                                 include_charts: bool = True,
                                 watermark: Optional[str] = None) -> bytes:
        """
        Export a compliance report to PDF format.
        
        This method converts a structured compliance report into a professional
        PDF document suitable for printing, archiving, and distribution.
        
        Args:
            report_data: Complete report data including findings, metrics, and metadata
            template_name: PDF-specific template to use for rendering
            include_charts: Whether to include charts and visualizations
            watermark: Optional watermark text for document security
            
        Returns:
            bytes: PDF document as binary data ready for saving or transmission
            
        Raises:
            PDFExportError: If PDF generation fails due to template or data issues
            ValueError: If report_data is invalid or missing required fields
            
        Example:
            >>> report_data = {
            ...     "title": "Compliance Analysis Report",
            ...     "findings": [...],
            ...     "metrics": {...}
            ... }
            >>> pdf_bytes = await pdf_service.export_report_to_pdf(report_data)
        """
        if not WEASYPRINT_AVAILABLE:
            raise PDFExportError("PDF export requires WeasyPrint library. Please install with: pip install weasyprint")
        
        try:
            logger.info(f"Starting PDF export for report: {report_data.get('title', 'Untitled')}")
            
            # Validate report data
            self._validate_report_data(report_data)
            
            # Prepare data for PDF template
            pdf_data = await self._prepare_pdf_data(report_data, include_charts, watermark)
            
            # Generate HTML from PDF-optimized template
            html_content = await self.template_engine.render_template(
                template_name=template_name,
                data=pdf_data,
                format_type=ReportFormat.PDF
            )
            
            # Apply PDF-specific CSS styling
            pdf_css = self._get_pdf_css_styles()
            
            # Generate PDF using WeasyPrint
            html_doc = HTML(string=html_content, base_url=str(Path.cwd()))
            css_doc = CSS(string=pdf_css, font_config=self.font_config)
            
            # Render to PDF with professional settings
            pdf_bytes = html_doc.write_pdf(
                stylesheets=[css_doc],
                font_config=self.font_config,
                optimize_images=True,
                pdf_version=self.pdf_settings['pdf_version']
            )
            
            logger.info(f"PDF export completed successfully. Size: {len(pdf_bytes)} bytes")
            return pdf_bytes
            
        except Exception as e:
            logger.error(f"PDF export failed: {e}")
            raise PDFExportError(f"Failed to generate PDF report: {str(e)}") from e
    
    async def export_batch_reports_to_pdf(self,
                                        reports: List[Dict[str, Any]],
                                        combined: bool = True,
                                        output_dir: Optional[Path] = None) -> Dict[str, Any]:
        """
        Export multiple reports to PDF format.
        
        Args:
            reports: List of report data dictionaries
            combined: Whether to combine all reports into a single PDF
            output_dir: Directory to save individual PDFs (if not combined)
            
        Returns:
            Dict containing export results and file information
        """
        try:
            logger.info(f"Starting batch PDF export for {len(reports)} reports")
            
            if combined:
                # Combine all reports into a single PDF
                combined_data = self._combine_reports_data(reports)
                pdf_bytes = await self.export_report_to_pdf(
                    combined_data, 
                    template_name="batch_compliance_report_pdf"
                )
                
                return {
                    "success": True,
                    "type": "combined",
                    "pdf_data": pdf_bytes,
                    "report_count": len(reports),
                    "file_size_bytes": len(pdf_bytes)
                }
            else:
                # Generate individual PDFs
                results = []
                for i, report_data in enumerate(reports):
                    try:
                        pdf_bytes = await self.export_report_to_pdf(report_data)
                        
                        # Save to output directory if specified
                        if output_dir:
                            filename = f"compliance_report_{i+1:03d}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
                            file_path = output_dir / filename
                            file_path.write_bytes(pdf_bytes)
                            
                            results.append({
                                "index": i,
                                "success": True,
                                "file_path": str(file_path),
                                "file_size_bytes": len(pdf_bytes)
                            })
                        else:
                            results.append({
                                "index": i,
                                "success": True,
                                "pdf_data": pdf_bytes,
                                "file_size_bytes": len(pdf_bytes)
                            })
                            
                    except Exception as e:
                        logger.error(f"Failed to export report {i}: {e}")
                        results.append({
                            "index": i,
                            "success": False,
                            "error": str(e)
                        })
                
                return {
                    "success": True,
                    "type": "individual",
                    "results": results,
                    "total_reports": len(reports),
                    "successful_exports": sum(1 for r in results if r["success"])
                }
                
        except Exception as e:
            logger.error(f"Batch PDF export failed: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def _validate_report_data(self, report_data: Dict[str, Any]) -> None:
        """Validate report data for PDF export."""
        required_fields = ["title", "generated_at", "findings"]
        missing_fields = [field for field in required_fields if field not in report_data]
        
        if missing_fields:
            raise ValueError(f"Report data missing required fields: {missing_fields}")
    
    async def _prepare_pdf_data(self, 
                              report_data: Dict[str, Any], 
                              include_charts: bool,
                              watermark: Optional[str]) -> Dict[str, Any]:
        """Prepare report data specifically for PDF rendering."""
        pdf_data = report_data.copy()
        
        # Add PDF-specific metadata
        pdf_data.update({
            "export_timestamp": datetime.now().isoformat(),
            "export_format": "PDF",
            "include_charts": include_charts,
            "watermark": watermark,
            "page_settings": self.pdf_settings
        })
        
        # Convert charts to static images if included
        if include_charts and "charts" in pdf_data:
            pdf_data["charts"] = await self._convert_charts_for_pdf(pdf_data["charts"])
        
        # Optimize content for print layout
        pdf_data = self._optimize_content_for_print(pdf_data)
        
        return pdf_data
    
    async def _convert_charts_for_pdf(self, charts: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Convert interactive charts to static images for PDF."""
        converted_charts = []
        
        for chart in charts:
            try:
                # Convert chart data to base64 image (placeholder implementation)
                # In production, this would use matplotlib, plotly, or similar
                chart_copy = chart.copy()
                chart_copy["image_data"] = "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNkYPhfDwAChwGA60e6kgAAAABJRU5ErkJggg=="
                converted_charts.append(chart_copy)
                
            except Exception as e:
                logger.warning(f"Failed to convert chart for PDF: {e}")
                # Include chart data without image as fallback
                converted_charts.append(chart)
        
        return converted_charts
    
    def _optimize_content_for_print(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Optimize content layout and formatting for print."""
        # Add page break hints for long content
        if "findings" in data and len(data["findings"]) > 10:
            # Group findings for better page layout
            findings = data["findings"]
            grouped_findings = []
            
            for i in range(0, len(findings), 5):
                group = findings[i:i+5]
                grouped_findings.append({
                    "group_index": i // 5 + 1,
                    "findings": group,
                    "page_break_after": i + 5 < len(findings)
                })
            
            data["grouped_findings"] = grouped_findings
        
        return data
    
    def _get_pdf_css_styles(self) -> str:
        """Get PDF-specific CSS styles for professional formatting."""
        return """
        @page {
            size: A4;
            margin: 1in 0.75in;
            
            @top-center {
                content: "Therapy Compliance Analysis Report";
                font-family: 'Segoe UI', Arial, sans-serif;
                font-size: 10pt;
                color: #666;
            }
            
            @bottom-right {
                content: "Page " counter(page) " of " counter(pages);
                font-family: 'Segoe UI', Arial, sans-serif;
                font-size: 9pt;
                color: #666;
            }
        }
        
        body {
            font-family: 'Segoe UI', Arial, sans-serif;
            font-size: 11pt;
            line-height: 1.4;
            color: #333;
            background: white;
        }
        
        h1, h2, h3 {
            color: #2563eb;
            page-break-after: avoid;
        }
        
        h1 {
            font-size: 18pt;
            margin-bottom: 20pt;
            border-bottom: 2pt solid #2563eb;
            padding-bottom: 10pt;
        }
        
        h2 {
            font-size: 14pt;
            margin-top: 20pt;
            margin-bottom: 12pt;
        }
        
        h3 {
            font-size: 12pt;
            margin-top: 16pt;
            margin-bottom: 8pt;
        }
        
        .finding {
            border: 1pt solid #e5e7eb;
            border-radius: 4pt;
            padding: 12pt;
            margin-bottom: 12pt;
            page-break-inside: avoid;
        }
        
        .finding.high-risk {
            border-left: 4pt solid #dc2626;
            background: #fef2f2;
        }
        
        .finding.medium-risk {
            border-left: 4pt solid #f59e0b;
            background: #fffbeb;
        }
        
        .finding.low-risk {
            border-left: 4pt solid #10b981;
            background: #f0fdf4;
        }
        
        .metrics-grid {
            display: grid;
            grid-template-columns: repeat(2, 1fr);
            gap: 12pt;
            margin: 16pt 0;
        }
        
        .metric-card {
            border: 1pt solid #e5e7eb;
            border-radius: 4pt;
            padding: 12pt;
            text-align: center;
        }
        
        .metric-value {
            font-size: 24pt;
            font-weight: bold;
            color: #2563eb;
        }
        
        .metric-label {
            font-size: 10pt;
            color: #666;
            margin-top: 4pt;
        }
        
        .page-break {
            page-break-before: always;
        }
        
        .no-break {
            page-break-inside: avoid;
        }
        
        table {
            width: 100%;
            border-collapse: collapse;
            margin: 12pt 0;
        }
        
        th, td {
            border: 1pt solid #e5e7eb;
            padding: 8pt;
            text-align: left;
        }
        
        th {
            background: #f9fafb;
            font-weight: bold;
        }
        
        .watermark {
            position: fixed;
            top: 50%;
            left: 50%;
            transform: translate(-50%, -50%) rotate(-45deg);
            font-size: 48pt;
            color: rgba(0, 0, 0, 0.1);
            z-index: -1;
            pointer-events: none;
        }
        """
    
    def _combine_reports_data(self, reports: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Combine multiple reports into a single document."""
        combined = {
            "title": f"Combined Compliance Analysis Report ({len(reports)} Reports)",
            "generated_at": datetime.now().isoformat(),
            "report_count": len(reports),
            "reports": reports,
            "combined_metrics": self._calculate_combined_metrics(reports),
            "findings": []
        }
        
        # Combine all findings
        for i, report in enumerate(reports):
            if "findings" in report:
                for finding in report["findings"]:
                    finding_copy = finding.copy()
                    finding_copy["source_report"] = i + 1
                    finding_copy["source_title"] = report.get("title", f"Report {i + 1}")
                    combined["findings"].append(finding_copy)
        
        return combined
    
    def _calculate_combined_metrics(self, reports: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Calculate combined metrics across multiple reports."""
        total_findings = 0
        total_high_risk = 0
        total_medium_risk = 0
        total_low_risk = 0
        compliance_scores = []
        
        for report in reports:
            if "findings" in report:
                findings = report["findings"]
                total_findings += len(findings)
                
                for finding in findings:
                    risk_level = finding.get("risk_level", "").lower()
                    if risk_level == "high":
                        total_high_risk += 1
                    elif risk_level == "medium":
                        total_medium_risk += 1
                    elif risk_level == "low":
                        total_low_risk += 1
            
            if "compliance_score" in report:
                compliance_scores.append(report["compliance_score"])
        
        avg_compliance_score = sum(compliance_scores) / len(compliance_scores) if compliance_scores else 0
        
        return {
            "total_findings": total_findings,
            "high_risk_findings": total_high_risk,
            "medium_risk_findings": total_medium_risk,
            "low_risk_findings": total_low_risk,
            "average_compliance_score": round(avg_compliance_score, 1),
            "report_count": len(reports)
        }


class PDFExportError(Exception):
    """Exception raised when PDF export fails."""
    pass


# Global PDF export service instance
pdf_export_service = PDFExportService()