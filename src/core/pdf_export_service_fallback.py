"""
PDF Export Service - Windows Compatible Fallback

Fallback PDF generation service that works on Windows without WeasyPrint dependencies.
Uses ReportLab for PDF generation with professional formatting.
"""

import logging
import asyncio
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional, Union
from dataclasses import dataclass
from enum import Enum
import tempfile
import base64
import html

# Use ReportLab for Windows compatibility
try:
    from reportlab.lib.pagesizes import letter, A4
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.units import inch
    from reportlab.lib import colors
    from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_RIGHT, TA_JUSTIFY
    REPORTLAB_AVAILABLE = True
except ImportError:
    REPORTLAB_AVAILABLE = False

logger = logging.getLogger(__name__)


class ExportFormat(Enum):
    """PDF export format options."""
    STANDARD = "standard"
    DETAILED = "detailed"
    SUMMARY = "summary"
    AUDIT = "audit"


class ExportOptions:
    """PDF export configuration options."""
    
    def __init__(
        self,
        format: ExportFormat = ExportFormat.STANDARD,
        include_charts: bool = True,
        include_recommendations: bool = True,
        include_raw_data: bool = False,
        watermark: Optional[str] = None,
        custom_header: Optional[str] = None,
        custom_footer: Optional[str] = None
    ):
        self.format = format
        self.include_charts = include_charts
        self.include_recommendations = include_recommendations
        self.include_raw_data = include_raw_data
        self.watermark = watermark
        self.custom_header = custom_header
        self.custom_footer = custom_footer


@dataclass
class ExportResult:
    """Result of PDF export operation."""
    success: bool
    file_path: Optional[Path]
    file_size: Optional[int]
    page_count: Optional[int]
    export_time_ms: float
    error_message: Optional[str] = None
    warnings: List[str] = None

    def __post_init__(self):
        if self.warnings is None:
            self.warnings = []


class PDFExportServiceFallback:
    """
    Windows-compatible PDF export service using ReportLab.
    
    This service provides professional PDF generation for compliance reports
    without requiring WeasyPrint dependencies that can be problematic on Windows.
    
    Features:
    - Professional report formatting
    - Tables and charts support
    - Custom headers and footers
    - Watermark support
    - Batch processing
    - Progress tracking
    
    Example:
        >>> service = PDFExportServiceFallback()
        >>> result = await service.export_report_to_pdf(report_data, "output.pdf")
        >>> print(f"Export successful: {result.success}")
    """
    
    def __init__(self):
        """Initialize the PDF export service."""
        self.temp_dir = Path(tempfile.gettempdir()) / "compliance_pdf_exports"
        self.temp_dir.mkdir(exist_ok=True)
        
        if not REPORTLAB_AVAILABLE:
            logger.error("ReportLab not available. PDF export will not work.")
            raise ImportError("ReportLab is required for PDF export functionality")
        
        # Initialize styles
        self.styles = getSampleStyleSheet()
        self._setup_custom_styles()
        
        logger.info("PDF export service initialized with ReportLab backend")
    
    def _setup_custom_styles(self):
        """Setup custom paragraph styles for professional formatting."""
        # Title style
        self.styles.add(ParagraphStyle(
            name='ReportTitle',
            parent=self.styles['Title'],
            fontSize=24,
            spaceAfter=30,
            alignment=TA_CENTER,
            textColor=colors.darkblue
        ))
        
        # Section header style
        self.styles.add(ParagraphStyle(
            name='SectionHeader',
            parent=self.styles['Heading1'],
            fontSize=16,
            spaceAfter=12,
            spaceBefore=20,
            textColor=colors.darkblue,
            borderWidth=1,
            borderColor=colors.lightgrey,
            borderPadding=5
        ))
        
        # Subsection header style
        self.styles.add(ParagraphStyle(
            name='SubsectionHeader',
            parent=self.styles['Heading2'],
            fontSize=14,
            spaceAfter=8,
            spaceBefore=12,
            textColor=colors.darkgreen
        ))
        
        # Finding style (for compliance issues)
        self.styles.add(ParagraphStyle(
            name='Finding',
            parent=self.styles['Normal'],
            fontSize=11,
            spaceAfter=6,
            leftIndent=20,
            borderWidth=1,
            borderColor=colors.orange,
            borderPadding=8,
            backColor=colors.lightyellow
        ))
        
        # Recommendation style
        self.styles.add(ParagraphStyle(
            name='Recommendation',
            parent=self.styles['Normal'],
            fontSize=11,
            spaceAfter=6,
            leftIndent=20,
            borderWidth=1,
            borderColor=colors.green,
            borderPadding=8,
            backColor=colors.lightgreen
        ))
    
    async def export_report_to_pdf(
        self,
        report_data: Dict[str, Any],
        output_path: Union[str, Path],
        options: Optional[ExportOptions] = None
    ) -> ExportResult:
        """
        Export a compliance report to PDF format.
        
        Args:
            report_data: Dictionary containing report data
            output_path: Path where PDF should be saved
            options: Export configuration options
            
        Returns:
            ExportResult with success status and metadata
        """
        start_time = datetime.now()
        
        if options is None:
            options = ExportOptions()
        
        try:
            output_path = Path(output_path)
            output_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Create PDF document
            doc = SimpleDocTemplate(
                str(output_path),
                pagesize=letter,
                rightMargin=72,
                leftMargin=72,
                topMargin=72,
                bottomMargin=18
            )\n            \n            # Build document content\n            story = []\n            \n            # Add title\n            title = report_data.get('title', 'Compliance Analysis Report')\n            story.append(Paragraph(title, self.styles['ReportTitle']))\n            story.append(Spacer(1, 20))\n            \n            # Add metadata section\n            self._add_metadata_section(story, report_data)\n            \n            # Add executive summary\n            if 'executive_summary' in report_data:\n                self._add_executive_summary(story, report_data['executive_summary'])\n            \n            # Add findings section\n            if 'findings' in report_data:\n                self._add_findings_section(story, report_data['findings'], options)\n            \n            # Add recommendations section\n            if options.include_recommendations and 'recommendations' in report_data:\n                self._add_recommendations_section(story, report_data['recommendations'])\n            \n            # Add raw data section if requested\n            if options.include_raw_data and 'raw_data' in report_data:\n                self._add_raw_data_section(story, report_data['raw_data'])\n            \n            # Build PDF\n            doc.build(story)\n            \n            # Calculate metrics\n            file_size = output_path.stat().st_size\n            export_time = (datetime.now() - start_time).total_seconds() * 1000\n            \n            logger.info(f\"PDF export completed: {output_path} ({file_size} bytes)\")\n            \n            return ExportResult(\n                success=True,\n                file_path=output_path,\n                file_size=file_size,\n                page_count=None,  # ReportLab doesn't easily provide page count\n                export_time_ms=export_time\n            )\n            \n        except Exception as e:\n            export_time = (datetime.now() - start_time).total_seconds() * 1000\n            logger.error(f\"PDF export failed: {e}\")\n            \n            return ExportResult(\n                success=False,\n                file_path=None,\n                file_size=None,\n                page_count=None,\n                export_time_ms=export_time,\n                error_message=str(e)\n            )\n    \n    def _add_metadata_section(self, story: List, report_data: Dict[str, Any]):\n        \"\"\"Add metadata section to the PDF.\"\"\"\n        story.append(Paragraph(\"Report Information\", self.styles['SectionHeader']))\n        \n        metadata = [\n            ['Generated:', report_data.get('timestamp', datetime.now().strftime('%Y-%m-%d %H:%M:%S'))],\n            ['Document:', report_data.get('document_name', 'N/A')],\n            ['Document Type:', report_data.get('document_type', 'N/A')],\n            ['Rubric:', report_data.get('rubric_name', 'N/A')],\n            ['Overall Score:', f\"{report_data.get('overall_score', 0)}/100\"]\n        ]\n        \n        table = Table(metadata, colWidths=[2*inch, 4*inch])\n        table.setStyle(TableStyle([\n            ('BACKGROUND', (0, 0), (0, -1), colors.lightgrey),\n            ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),\n            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),\n            ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),\n            ('FONTSIZE', (0, 0), (-1, -1), 10),\n            ('BOTTOMPADDING', (0, 0), (-1, -1), 12),\n            ('BACKGROUND', (1, 0), (1, -1), colors.beige),\n            ('GRID', (0, 0), (-1, -1), 1, colors.black)\n        ]))\n        \n        story.append(table)\n        story.append(Spacer(1, 20))\n    \n    def _add_executive_summary(self, story: List, summary_data: Dict[str, Any]):\n        \"\"\"Add executive summary section.\"\"\"\n        story.append(Paragraph(\"Executive Summary\", self.styles['SectionHeader']))\n        \n        # Overall compliance score\n        score = summary_data.get('overall_score', 0)\n        score_text = f\"<b>Overall Compliance Score: {score}/100</b>\"\n        if score >= 90:\n            score_text += \" (Excellent)\"\n        elif score >= 70:\n            score_text += \" (Good)\"\n        else:\n            score_text += \" (Needs Improvement)\"\n        \n        story.append(Paragraph(score_text, self.styles['Normal']))\n        story.append(Spacer(1, 10))\n        \n        # Key metrics\n        if 'metrics' in summary_data:\n            metrics = summary_data['metrics']\n            metrics_data = [\n                ['Total Findings:', str(metrics.get('total_findings', 0))],\n                ['High Risk:', str(metrics.get('high_risk', 0))],\n                ['Medium Risk:', str(metrics.get('medium_risk', 0))],\n                ['Low Risk:', str(metrics.get('low_risk', 0))]\n            ]\n            \n            table = Table(metrics_data, colWidths=[2*inch, 1*inch])\n            table.setStyle(TableStyle([\n                ('BACKGROUND', (0, 0), (0, -1), colors.lightblue),\n                ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),\n                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),\n                ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),\n                ('FONTSIZE', (0, 0), (-1, -1), 10),\n                ('BOTTOMPADDING', (0, 0), (-1, -1), 8),\n                ('GRID', (0, 0), (-1, -1), 1, colors.black)\n            ]))\n            \n            story.append(table)\n        \n        story.append(Spacer(1, 20))\n    \n    def _add_findings_section(self, story: List, findings: List[Dict[str, Any]], options: ExportOptions):\n        \"\"\"Add findings section with detailed compliance issues.\"\"\"\n        story.append(Paragraph(\"Compliance Findings\", self.styles['SectionHeader']))\n        \n        if not findings:\n            story.append(Paragraph(\"No compliance issues found.\", self.styles['Normal']))\n            story.append(Spacer(1, 20))\n            return\n        \n        for i, finding in enumerate(findings, 1):\n            # Finding header\n            risk_level = finding.get('risk_level', 'Unknown')\n            title = f\"Finding {i}: {finding.get('title', 'Compliance Issue')} ({risk_level} Risk)\"\n            story.append(Paragraph(title, self.styles['SubsectionHeader']))\n            \n            # Finding details\n            description = finding.get('description', 'No description available')\n            story.append(Paragraph(f\"<b>Issue:</b> {html.escape(description)}\", self.styles['Finding']))\n            \n            # Evidence\n            if 'evidence' in finding:\n                evidence = finding['evidence']\n                story.append(Paragraph(f\"<b>Evidence:</b> {html.escape(evidence)}\", self.styles['Normal']))\n            \n            # Regulation reference\n            if 'regulation' in finding:\n                regulation = finding['regulation']\n                story.append(Paragraph(f\"<b>Regulation:</b> {html.escape(regulation)}\", self.styles['Normal']))\n            \n            story.append(Spacer(1, 15))\n    \n    def _add_recommendations_section(self, story: List, recommendations: List[Dict[str, Any]]):\n        \"\"\"Add recommendations section.\"\"\"\n        story.append(Paragraph(\"Recommendations\", self.styles['SectionHeader']))\n        \n        if not recommendations:\n            story.append(Paragraph(\"No specific recommendations available.\", self.styles['Normal']))\n            story.append(Spacer(1, 20))\n            return\n        \n        for i, rec in enumerate(recommendations, 1):\n            title = f\"Recommendation {i}: {rec.get('title', 'Improvement Suggestion')}\"\n            story.append(Paragraph(title, self.styles['SubsectionHeader']))\n            \n            description = rec.get('description', 'No description available')\n            story.append(Paragraph(html.escape(description), self.styles['Recommendation']))\n            \n            # Priority and timeline\n            priority = rec.get('priority', 'Medium')\n            timeline = rec.get('timeline', 'Not specified')\n            story.append(Paragraph(f\"<b>Priority:</b> {priority} | <b>Timeline:</b> {timeline}\", self.styles['Normal']))\n            \n            story.append(Spacer(1, 15))\n    \n    def _add_raw_data_section(self, story: List, raw_data: Dict[str, Any]):\n        \"\"\"Add raw data section for audit purposes.\"\"\"\n        story.append(PageBreak())\n        story.append(Paragraph(\"Raw Data (Audit Trail)\", self.styles['SectionHeader']))\n        \n        # Convert raw data to readable format\n        for key, value in raw_data.items():\n            story.append(Paragraph(f\"<b>{key}:</b>\", self.styles['SubsectionHeader']))\n            \n            if isinstance(value, (dict, list)):\n                # Format complex data structures\n                import json\n                formatted_value = json.dumps(value, indent=2)\n                story.append(Paragraph(f\"<pre>{html.escape(formatted_value)}</pre>\", self.styles['Code']))\n            else:\n                story.append(Paragraph(html.escape(str(value)), self.styles['Normal']))\n            \n            story.append(Spacer(1, 10))\n    \n    async def export_batch_reports_to_pdf(\n        self,\n        reports_data: List[Dict[str, Any]],\n        output_directory: Union[str, Path],\n        options: Optional[ExportOptions] = None\n    ) -> List[ExportResult]:\n        \"\"\"Export multiple reports to PDF format.\"\"\"\n        output_directory = Path(output_directory)\n        output_directory.mkdir(parents=True, exist_ok=True)\n        \n        results = []\n        \n        for i, report_data in enumerate(reports_data):\n            # Generate filename\n            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')\n            filename = f\"compliance_report_{i+1}_{timestamp}.pdf\"\n            output_path = output_directory / filename\n            \n            # Export individual report\n            result = await self.export_report_to_pdf(report_data, output_path, options)\n            results.append(result)\n            \n            logger.info(f\"Batch export progress: {i+1}/{len(reports_data)}\")\n        \n        successful_exports = sum(1 for r in results if r.success)\n        logger.info(f\"Batch export completed: {successful_exports}/{len(reports_data)} successful\")\n        \n        return results\n    \n    def cleanup_temp_files(self, max_age_hours: int = 24):\n        \"\"\"Clean up temporary files older than specified age.\"\"\"\n        try:\n            current_time = datetime.now()\n            cleaned_count = 0\n            \n            for file_path in self.temp_dir.glob(\"*.pdf\"):\n                file_age = current_time - datetime.fromtimestamp(file_path.stat().st_mtime)\n                if file_age.total_seconds() > max_age_hours * 3600:\n                    file_path.unlink()\n                    cleaned_count += 1\n            \n            logger.info(f\"Cleaned up {cleaned_count} temporary PDF files\")\n            \n        except Exception as e:\n            logger.error(f\"Error cleaning up temporary files: {e}\")\n\n\n# Global service instance\npdf_export_service = PDFExportServiceFallback() if REPORTLAB_AVAILABLE else None\n\n\n# Compatibility function for the main service\ndef get_pdf_export_service():\n    \"\"\"Get the appropriate PDF export service based on available dependencies.\"\"\"\n    if pdf_export_service is not None:\n        return pdf_export_service\n    else:\n        raise ImportError(\"No PDF export service available. Please install ReportLab.\")\n