"""PDF Export Service - Windows Compatible Fallback

Clean, working fallback PDF generation service using ReportLab.
"""

import html
import logging
import tempfile
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any

# Use ReportLab for Windows compatibility
try:
    from reportlab.lib import colors
    from reportlab.lib.enums import TA_CENTER
    from reportlab.lib.pagesizes import letter
    from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
    from reportlab.lib.units import inch
    from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle
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


@dataclass
class ExportOptions:
    """PDF export configuration options."""

    format: ExportFormat = ExportFormat.STANDARD
    include_charts: bool = True
    include_recommendations: bool = True
    include_raw_data: bool = False
    watermark: str | None = None
    page_size: str = "letter"
    margins: dict[str, float] = None

    def __post_init__(self):
        if self.margins is None:
            self.margins = {"top": 72, "bottom": 72, "left": 72, "right": 72}


@dataclass
class ExportResult:
    """Result of PDF export operation."""

    success: bool
    file_path: Path | None = None
    file_size: int | None = None
    page_count: int | None = None
    export_time_ms: float = 0
    error_message: str | None = None


class PDFExportServiceFallback:
    """Windows-compatible PDF export service using ReportLab."""

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
            name="ReportTitle",
            parent=self.styles["Heading1"],
            fontSize=18,
            spaceAfter=30,
            alignment=TA_CENTER,
            textColor=colors.darkblue,
        ))

        # Section header style
        self.styles.add(ParagraphStyle(
            name="SectionHeader",
            parent=self.styles["Heading2"],
            fontSize=14,
            spaceAfter=12,
            spaceBefore=20,
            textColor=colors.darkblue,
        ))

        # Subsection header style
        self.styles.add(ParagraphStyle(
            name="SubsectionHeader",
            parent=self.styles["Heading3"],
            fontSize=12,
            spaceAfter=8,
            spaceBefore=12,
            textColor=colors.darkgreen,
        ))

        # Finding style
        self.styles.add(ParagraphStyle(
            name="Finding",
            parent=self.styles["Normal"],
            fontSize=10,
            spaceAfter=6,
            leftIndent=20,
        ))

        # Recommendation style
        self.styles.add(ParagraphStyle(
            name="Recommendation",
            parent=self.styles["Normal"],
            fontSize=10,
            spaceAfter=6,
            leftIndent=20,
            textColor=colors.darkgreen,
        ))

        # Code style (check if it already exists)
        if "Code" not in self.styles:
            self.styles.add(ParagraphStyle(
                name="Code",
                parent=self.styles["Normal"],
                fontSize=8,
                fontName="Courier",
                leftIndent=20,
                rightIndent=20,
                backgroundColor=colors.lightgrey,
            ))

    async def export_report_to_pdf(
        self,
        report_data: dict[str, Any],
        template_name: str = "compliance_report_pdf",
        include_charts: bool = True,
        watermark: str | None = None,
    ) -> bytes:
        """Export a compliance report to PDF format."""
        try:
            # Create temporary file
            temp_file = self.temp_dir / f"temp_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"

            # Export to file
            options = ExportOptions(
                include_charts=include_charts,
                watermark=watermark,
            )
            result = await self.export_to_file(report_data, temp_file, options)

            if not result.success:
                raise Exception(result.error_message or "PDF export failed")

            # Read file content
            with open(temp_file, "rb") as f:
                pdf_bytes = f.read()

            # Clean up temp file
            temp_file.unlink(missing_ok=True)

            return pdf_bytes

        except Exception as e:
            logger.exception("PDF export failed: %s", e)
            raise

    async def export_to_file(
        self,
        report_data: dict[str, Any],
        output_path: str | Path,
        options: ExportOptions | None = None,
    ) -> ExportResult:
        """Export report to PDF file."""
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
                bottomMargin=18,
            )

            # Build document content
            story = []

            # Add title
            title = report_data.get("title", "Compliance Analysis Report")
            story.append(Paragraph(title, self.styles["ReportTitle"]))
            story.append(Spacer(1, 20))

            # Add metadata section
            self._add_metadata_section(story, report_data)

            # Add executive summary
            if "executive_summary" in report_data:
                self._add_executive_summary(story, report_data["executive_summary"])

            # Add findings section
            if "findings" in report_data:
                self._add_findings_section(story, report_data["findings"], options)

            # Add recommendations section
            if options.include_recommendations and "recommendations" in report_data:
                self._add_recommendations_section(story, report_data["recommendations"])

            # Build PDF
            doc.build(story)

            # Calculate metrics
            file_size = output_path.stat().st_size
            export_time = (datetime.now() - start_time).total_seconds() * 1000

            logger.info("PDF export completed: %s ({file_size} bytes)", output_path)

            return ExportResult(
                success=True,
                file_path=output_path,
                file_size=file_size,
                page_count=None,
                export_time_ms=export_time,
            )

        except Exception as e:
            export_time = (datetime.now() - start_time).total_seconds() * 1000
            logger.exception("PDF export failed: %s", e)

            return ExportResult(
                success=False,
                file_path=None,
                file_size=None,
                page_count=None,
                export_time_ms=export_time,
                error_message=str(e),
            )

    def _add_metadata_section(self, story: list, report_data: dict[str, Any]):
        """Add metadata section to the PDF."""
        story.append(Paragraph("Report Information", self.styles["SectionHeader"]))

        metadata = [
            ["Generated:", report_data.get("timestamp", datetime.now().strftime("%Y-%m-%d %H:%M:%S"))],
            ["Document:", report_data.get("document_name", "N/A")],
            ["Document Type:", report_data.get("document_type", "N/A")],
            ["Rubric:", report_data.get("rubric_name", "N/A")],
            ["Overall Score:", f"{report_data.get('overall_score', 0)}/100"],
        ]

        table = Table(metadata, colWidths=[2*inch, 4*inch])
        table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (0, -1), colors.lightgrey),
            ("TEXTCOLOR", (0, 0), (-1, -1), colors.black),
            ("ALIGN", (0, 0), (-1, -1), "LEFT"),
            ("FONTNAME", (0, 0), (-1, -1), "Helvetica"),
            ("FONTSIZE", (0, 0), (-1, -1), 10),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 12),
            ("BACKGROUND", (1, 0), (1, -1), colors.beige),
            ("GRID", (0, 0), (-1, -1), 1, colors.black),
        ]))

        story.append(table)
        story.append(Spacer(1, 20))

    def _add_executive_summary(self, story: list, summary_data: dict[str, Any]):
        """Add executive summary section."""
        story.append(Paragraph("Executive Summary", self.styles["SectionHeader"]))

        # Overall compliance score
        score = summary_data.get("overall_score", 0)
        score_text = f"<b>Overall Compliance Score: {score}/100</b>"
        if score >= 90:
            score_text += " (Excellent)"
        elif score >= 70:
            score_text += " (Good)"
        else:
            score_text += " (Needs Improvement)"

        story.append(Paragraph(score_text, self.styles["Normal"]))
        story.append(Spacer(1, 10))

        # Key metrics
        if "metrics" in summary_data:
            metrics = summary_data["metrics"]
            metrics_data = [
                ["Total Findings:", str(metrics.get("total_findings", 0))],
                ["High Risk:", str(metrics.get("high_risk", 0))],
                ["Medium Risk:", str(metrics.get("medium_risk", 0))],
                ["Low Risk:", str(metrics.get("low_risk", 0))],
            ]

            table = Table(metrics_data, colWidths=[2*inch, 1*inch])
            table.setStyle(TableStyle([
                ("BACKGROUND", (0, 0), (0, -1), colors.lightblue),
                ("TEXTCOLOR", (0, 0), (-1, -1), colors.black),
                ("ALIGN", (0, 0), (-1, -1), "LEFT"),
                ("FONTNAME", (0, 0), (-1, -1), "Helvetica"),
                ("FONTSIZE", (0, 0), (-1, -1), 10),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
                ("GRID", (0, 0), (-1, -1), 1, colors.black),
            ]))

            story.append(table)

        story.append(Spacer(1, 20))

    def _add_findings_section(self, story: list, findings: list[dict[str, Any]], options: ExportOptions):
        """Add findings section with detailed compliance issues."""
        story.append(Paragraph("Compliance Findings", self.styles["SectionHeader"]))

        if not findings:
            story.append(Paragraph("No compliance issues found.", self.styles["Normal"]))
            story.append(Spacer(1, 20))
            return

        for i, finding in enumerate(findings, 1):
            # Finding header
            risk_level = finding.get("risk_level", "Unknown")
            title = f"Finding {i}: {finding.get('title', 'Compliance Issue')} ({risk_level} Risk)"
            story.append(Paragraph(title, self.styles["SubsectionHeader"]))

            # Finding details
            description = finding.get("description", "No description available")
            story.append(Paragraph(f"<b>Issue:</b> {html.escape(description)}", self.styles["Finding"]))

            # Evidence
            if "evidence" in finding:
                evidence = finding["evidence"]
                story.append(Paragraph(f"<b>Evidence:</b> {html.escape(evidence)}", self.styles["Normal"]))

            # Regulation reference
            if "regulation" in finding:
                regulation = finding["regulation"]
                story.append(Paragraph(f"<b>Regulation:</b> {html.escape(regulation)}", self.styles["Normal"]))

            story.append(Spacer(1, 15))

    def _add_recommendations_section(self, story: list, recommendations: list[dict[str, Any]]):
        """Add recommendations section."""
        story.append(Paragraph("Recommendations", self.styles["SectionHeader"]))

        if not recommendations:
            story.append(Paragraph("No specific recommendations available.", self.styles["Normal"]))
            story.append(Spacer(1, 20))
            return

        for i, rec in enumerate(recommendations, 1):
            title = f"Recommendation {i}: {rec.get('title', 'Improvement Suggestion')}"
            story.append(Paragraph(title, self.styles["SubsectionHeader"]))

            description = rec.get("description", "No description available")
            story.append(Paragraph(html.escape(description), self.styles["Recommendation"]))

            # Priority and timeline
            priority = rec.get("priority", "Medium")
            timeline = rec.get("timeline", "Not specified")
            story.append(Paragraph(f"<b>Priority:</b> {priority} | <b>Timeline:</b> {timeline}", self.styles["Normal"]))

            story.append(Spacer(1, 15))


# Global service instance (lazy initialization)
pdf_export_service_fallback = None

def get_pdf_export_service_fallback():
    """Get the fallback PDF export service instance."""
    global pdf_export_service_fallback
    if pdf_export_service_fallback is None and REPORTLAB_AVAILABLE:
        pdf_export_service_fallback = PDFExportServiceFallback()
    return pdf_export_service_fallback
