"""
PDF Export Service - Optional feature for professional report generation.
Can be enabled/disabled via configuration.
"""

import logging
from typing import Dict, Any, Optional, List
from datetime import datetime

logger = logging.getLogger(__name__)

# Optional dependency - graceful fallback if not available
try:
    from reportlab.lib.pagesizes import letter
    from reportlab.platypus import (
        SimpleDocTemplate,
        Paragraph,
        Spacer,
        Table,
        TableStyle,
    )
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.units import inch
    from reportlab.lib import colors
    from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY

    PDF_AVAILABLE = True
except ImportError:
    logger.warning("ReportLab not available - PDF export disabled")
    PDF_AVAILABLE = False


class PDFExportService:
    """
    Professional PDF report generation service.
    Optional feature that can be enabled/disabled.
    """

    def __init__(self, enabled: bool = True):
        self.enabled = enabled and PDF_AVAILABLE
        if not self.enabled:
            logger.info("PDF export service disabled")
            return

        self.styles = getSampleStyleSheet()
        self._setup_custom_styles()
        logger.info("PDF export service initialized")

    def _setup_custom_styles(self):
        """Setup custom paragraph styles for professional reports."""
        if not self.enabled:
            return

        # Title style
        self.title_style = ParagraphStyle(
            "CustomTitle",
            parent=self.styles["Heading1"],
            fontSize=18,
            spaceAfter=30,
            alignment=TA_CENTER,
            textColor=colors.HexColor("#2c3e50"),
        )

        # Subtitle style
        self.subtitle_style = ParagraphStyle(
            "CustomSubtitle",
            parent=self.styles["Heading2"],
            fontSize=14,
            spaceAfter=12,
            textColor=colors.HexColor("#34495e"),
        )

        # Body text style
        self.body_style = ParagraphStyle(
            "CustomBody",
            parent=self.styles["Normal"],
            fontSize=10,
            spaceAfter=6,
            alignment=TA_JUSTIFY,
        )

        # Finding style for compliance issues
        self.finding_style = ParagraphStyle(
            "FindingStyle",
            parent=self.styles["Normal"],
            fontSize=9,
            leftIndent=20,
            spaceAfter=8,
        )

    def is_available(self) -> bool:
        """Check if PDF export is available and enabled."""
        return self.enabled

    def export_compliance_report(
        self,
        report_data: Dict[str, Any],
        output_path: str,
        include_branding: bool = True,
    ) -> bool:
        """
        Export compliance analysis report as professional PDF.

        Args:
            report_data: Analysis results and metadata
            output_path: Path where PDF should be saved
            include_branding: Whether to include custom branding

        Returns:
            True if export successful, False otherwise
        """
        if not self.enabled:
            logger.warning("PDF export not available")
            return False

        try:
            # Create document
            doc = SimpleDocTemplate(
                output_path,
                pagesize=letter,
                rightMargin=72,
                leftMargin=72,
                topMargin=72,
                bottomMargin=18,
            )

            # Build content
            story: List[Any] = []

            # Header
            self._add_header(story, report_data, include_branding)

            # Executive Summary
            self._add_executive_summary(story, report_data)

            # Detailed Findings
            self._add_detailed_findings(story, report_data)

            # Recommendations
            self._add_recommendations(story, report_data)

            # Footer information
            self._add_footer_info(story, report_data)

            # Build PDF
            doc.build(story)

            logger.info(f"PDF report exported successfully to {output_path}")
            return True

        except Exception as e:
            logger.error(f"PDF export failed: {e}")
            return False

    def _add_header(
        self, story: List, report_data: Dict[str, Any], include_branding: bool
    ):
        """Add report header with title and metadata."""
        if not self.enabled:
            return

        # Title
        title = Paragraph("Clinical Compliance Analysis Report", self.title_style)
        story.append(title)
        story.append(Spacer(1, 12))

        # Document information table
        doc_info = [
            ["Document Name:", report_data.get("document_name", "Unknown")],
            [
                "Analysis Date:",
                report_data.get(
                    "analysis_date", datetime.now().strftime("%Y-%m-%d %H:%M")
                ),
            ],
            ["Document Type:", report_data.get("document_type", "Not specified")],
            ["Compliance Score:", f"{report_data.get('compliance_score', 0):.1f}%"],
        ]

        info_table = Table(doc_info, colWidths=[2 * inch, 4 * inch])
        info_table.setStyle(
            TableStyle(
                [
                    ("ALIGN", (0, 0), (-1, -1), "LEFT"),
                    ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
                    ("FONTSIZE", (0, 0), (-1, -1), 10),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
                ]
            )
        )

        story.append(info_table)
        story.append(Spacer(1, 20))

    def _add_executive_summary(self, story: List, report_data: Dict[str, Any]):
        """Add executive summary section."""
        if not self.enabled:
            return

        story.append(Paragraph("Executive Summary", self.subtitle_style))

        # Compliance score and risk distribution
        findings = report_data.get("findings", [])
        risk_counts = {"High": 0, "Medium": 0, "Low": 0}

        for finding in findings:
            risk = finding.get("risk", "Low")
            risk_counts[risk] = risk_counts.get(risk, 0) + 1

        summary_text = f"""
        This document analysis identified {len(findings)} compliance findings with an overall
        compliance score of {report_data.get("compliance_score", 0):.1f}%.
        The risk distribution includes {risk_counts["High"]} high-risk,
        {risk_counts["Medium"]} medium-risk, and {risk_counts["Low"]} low-risk findings.
        """

        story.append(Paragraph(summary_text, self.body_style))
        story.append(Spacer(1, 15))

    def _add_detailed_findings(self, story: List, report_data: Dict[str, Any]):
        """Add detailed findings section."""
        if not self.enabled:
            return

        story.append(Paragraph("Detailed Findings", self.subtitle_style))

        findings = report_data.get("findings", [])

        if not findings:
            story.append(Paragraph("No compliance issues identified.", self.body_style))
            return

        # Create findings table
        table_data = [["Risk Level", "Issue Description", "Recommendation"]]

        for finding in findings:
            risk = finding.get("risk", "Unknown")
            issue = finding.get("problematic_text", "No description")[:100] + "..."
            recommendation = (
                finding.get("personalized_tip", "No recommendation")[:100] + "..."
            )

            table_data.append([risk, issue, recommendation])

        findings_table = Table(table_data, colWidths=[1 * inch, 2.5 * inch, 2.5 * inch])
        findings_table.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, 0), colors.grey),
                    ("TEXTCOLOR", (0, 0), (-1, 0), colors.whitesmoke),
                    ("ALIGN", (0, 0), (-1, -1), "LEFT"),
                    ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                    ("FONTSIZE", (0, 0), (-1, -1), 8),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
                    ("GRID", (0, 0), (-1, -1), 1, colors.black),
                    ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ]
            )
        )

        story.append(findings_table)
        story.append(Spacer(1, 15))

    def _add_recommendations(self, story: List, report_data: Dict[str, Any]):
        """Add recommendations section."""
        if not self.enabled:
            return

        story.append(Paragraph("Key Recommendations", self.subtitle_style))

        # Extract unique recommendations
        findings = report_data.get("findings", [])
        recommendations = set()

        for finding in findings:
            tip = finding.get("personalized_tip", "")
            if tip and len(tip) > 10:  # Filter out empty or very short tips
                recommendations.add(tip)

        if recommendations:
            for i, rec in enumerate(sorted(recommendations)[:10], 1):  # Limit to top 10
                rec_text = f"{i}. {rec}"
                story.append(Paragraph(rec_text, self.finding_style))
        else:
            story.append(
                Paragraph("No specific recommendations available.", self.body_style)
            )

        story.append(Spacer(1, 15))

    def _add_footer_info(self, story: List, report_data: Dict[str, Any]):
        """Add footer information and disclaimers."""
        if not self.enabled:
            return

        story.append(Paragraph("Important Information", self.subtitle_style))

        disclaimer = """
        This report was generated by an AI-powered compliance analysis system.
        While the system uses advanced natural language processing and machine learning
        techniques, all findings should be reviewed by qualified healthcare professionals.
        This analysis is intended to assist with compliance review and should not replace
        professional judgment or comprehensive manual review.
        """

        story.append(Paragraph(disclaimer, self.body_style))

        # Generation info
        gen_info = (
            f"Report generated on {datetime.now().strftime('%Y-%m-%d at %H:%M:%S')}"
        )
        story.append(Spacer(1, 10))
        story.append(Paragraph(gen_info, self.body_style))


def create_pdf_export_service(enabled: bool = True) -> Optional[PDFExportService]:
    """
    Factory function to create PDF export service.

    Args:
        enabled: Whether PDF export should be enabled

    Returns:
        PDFExportService instance if available, None otherwise
    """
    if not enabled:
        logger.info("PDF export service creation skipped (disabled)")
        return None

    if not PDF_AVAILABLE:
        logger.warning("PDF export service unavailable (missing dependencies)")
        return None

    return PDFExportService(enabled=True)


# Configuration
PDF_EXPORT_CONFIG = {
    "enabled": True,  # Can be set to False to disable PDF export
    "include_branding": True,
    "default_output_dir": "reports",
    "max_file_size_mb": 50,
}


def is_pdf_export_enabled() -> bool:
    """Check if PDF export is enabled and available."""
    return PDF_EXPORT_CONFIG.get("enabled", False) and PDF_AVAILABLE
