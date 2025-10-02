"""
PDF Export Service for Clinical Compliance Reports.

Converts HTML reports to professional, audit-ready PDF documents with:
- Professional formatting and styling
- Headers and footers with metadata
- Page numbers and timestamps
- Digital signature support (optional)
- Auto-purge after configurable retention period
"""

import logging
import os
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any, Dict, Optional

from weasyprint import HTML, CSS
from weasyprint.text.fonts import FontConfiguration

logger = logging.getLogger(__name__)


class PDFExportService:
    """
    Service for exporting compliance reports to PDF format.
    
    Features:
    - HTML to PDF conversion with professional styling
    - Custom headers/footers with metadata
    - Page numbering and timestamps
    - Configurable retention and auto-purge
    - HIPAA-compliant file handling
    """

    def __init__(
        self,
        output_dir: Optional[str] = None,
        retention_hours: int = 24,
        enable_auto_purge: bool = True,
    ):
        """
        Initialize PDF export service.

        Args:
            output_dir: Directory for PDF output (default: temp/reports)
            retention_hours: Hours to retain PDFs before auto-purge (default: 24)
            enable_auto_purge: Enable automatic purging of old PDFs
        """
        self.output_dir = Path(output_dir or "temp/reports")
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        self.retention_hours = retention_hours
        self.enable_auto_purge = enable_auto_purge
        
        # Font configuration for better rendering
        self.font_config = FontConfiguration()
        
        # Custom CSS for PDF styling
        self.pdf_css = self._load_pdf_styles()
        
        logger.info(
            f"PDF Export Service initialized: output_dir={self.output_dir}, "
            f"retention={retention_hours}h, auto_purge={enable_auto_purge}"
        )

    def _load_pdf_styles(self) -> str:
        """Load custom CSS styles for PDF rendering."""
        return """
        @page {
            size: Letter;
            margin: 1in 0.75in;
            
            @top-left {
                content: "Therapy Compliance Report";
                font-size: 9pt;
                color: #666;
            }
            
            @top-right {
                content: "Generated: " string(report-date);
                font-size: 9pt;
                color: #666;
            }
            
            @bottom-center {
                content: "Page " counter(page) " of " counter(pages);
                font-size: 9pt;
                color: #666;
            }
            
            @bottom-right {
                content: "CONFIDENTIAL - HIPAA Protected";
                font-size: 8pt;
                color: #999;
                font-style: italic;
            }
        }
        
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            font-size: 11pt;
            line-height: 1.6;
            color: #333;
        }
        
        h1 {
            color: #2c3e50;
            border-bottom: 3px solid #3498db;
            padding-bottom: 10px;
            page-break-after: avoid;
        }
        
        h2 {
            color: #34495e;
            border-bottom: 2px solid #95a5a6;
            padding-bottom: 5px;
            margin-top: 30px;
            page-break-after: avoid;
        }
        
        h3 {
            color: #7f8c8d;
            margin-top: 20px;
            page-break-after: avoid;
        }
        
        table {
            width: 100%;
            border-collapse: collapse;
            margin: 20px 0;
            page-break-inside: avoid;
        }
        
        th {
            background-color: #3498db;
            color: white;
            padding: 12px;
            text-align: left;
            font-weight: bold;
        }
        
        td {
            padding: 10px;
            border: 1px solid #ddd;
        }
        
        tr:nth-child(even) {
            background-color: #f9f9f9;
        }
        
        .risk-high {
            color: #e74c3c;
            font-weight: bold;
        }
        
        .risk-medium {
            color: #f39c12;
            font-weight: bold;
        }
        
        .risk-low {
            color: #27ae60;
        }
        
        .high-confidence {
            background-color: #d5f4e6;
        }
        
        .medium-confidence {
            background-color: #fff3cd;
        }
        
        .low-confidence {
            background-color: #f8d7da;
        }
        
        .disputed {
            background-color: #ffebee;
            text-decoration: line-through;
        }
        
        .confidence-indicator {
            font-size: 9pt;
            color: #666;
        }
        
        .habit-name {
            font-weight: bold;
            color: #2980b9;
        }
        
        .habit-explanation {
            font-size: 9pt;
            color: #555;
            margin-top: 5px;
        }
        
        .executive-summary {
            background-color: #ecf0f1;
            padding: 20px;
            border-left: 5px solid #3498db;
            margin: 20px 0;
            page-break-inside: avoid;
        }
        
        .compliance-score {
            font-size: 36pt;
            font-weight: bold;
            color: #2c3e50;
            text-align: center;
        }
        
        .metadata-table {
            background-color: #f8f9fa;
            border: 1px solid #dee2e6;
            padding: 15px;
            margin: 20px 0;
        }
        
        .footer-disclaimer {
            font-size: 8pt;
            color: #999;
            text-align: center;
            margin-top: 30px;
            padding-top: 10px;
            border-top: 1px solid #ddd;
        }
        
        /* Remove interactive elements for PDF */
        a[href^="highlight://"],
        a[href^="chat://"],
        a[href^="dispute://"] {
            color: #3498db;
            text-decoration: none;
            pointer-events: none;
        }
        
        /* Print-friendly adjustments */
        @media print {
            body {
                background: white;
            }
            
            .no-print {
                display: none;
            }
        }
        """

    def export_to_pdf(
        self,
        html_content: str,
        document_name: str,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Export HTML report to PDF format.

        Args:
            html_content: HTML content of the report
            document_name: Name of the source document
            metadata: Optional metadata to include in PDF

        Returns:
            Dict with PDF file path, size, and metadata

        Raises:
            Exception: If PDF generation fails
        """
        try:
            # Generate unique filename
            timestamp = datetime.now(UTC).strftime("%Y%m%d_%H%M%S")
            safe_doc_name = self._sanitize_filename(document_name)
            pdf_filename = f"compliance_report_{safe_doc_name}_{timestamp}.pdf"
            pdf_path = self.output_dir / pdf_filename

            # Enhance HTML with metadata
            enhanced_html = self._enhance_html_for_pdf(html_content, metadata)

            # Convert to PDF
            logger.info(f"Generating PDF: {pdf_filename}")
            html_doc = HTML(string=enhanced_html)
            css_doc = CSS(string=self.pdf_css, font_config=self.font_config)
            
            html_doc.write_pdf(
                target=str(pdf_path),
                stylesheets=[css_doc],
                font_config=self.font_config,
            )

            # Get file size
            file_size = pdf_path.stat().st_size

            # Schedule auto-purge if enabled
            purge_time = None
            if self.enable_auto_purge:
                purge_time = datetime.now(UTC) + timedelta(hours=self.retention_hours)
                logger.info(f"PDF will be auto-purged at: {purge_time}")

            result = {
                "success": True,
                "pdf_path": str(pdf_path),
                "filename": pdf_filename,
                "file_size": file_size,
                "file_size_mb": round(file_size / (1024 * 1024), 2),
                "generated_at": datetime.now(UTC).isoformat(),
                "purge_at": purge_time.isoformat() if purge_time else None,
            }

            logger.info(
                f"PDF generated successfully: {pdf_filename} ({result['file_size_mb']}MB)"
            )
            return result

        except Exception as e:
            logger.exception(f"Failed to generate PDF: {e}")
            return {
                "success": False,
                "error": str(e),
                "pdf_path": None,
            }

    def _enhance_html_for_pdf(
        self, html_content: str, metadata: Optional[Dict[str, Any]]
    ) -> str:
        """
        Enhance HTML content with PDF-specific elements.

        Args:
            html_content: Original HTML content
            metadata: Optional metadata to include

        Returns:
            Enhanced HTML with PDF-specific styling and metadata
        """
        # Add report date for header
        report_date = datetime.now().strftime("%Y-%m-%d %H:%M")
        
        # Build metadata section
        metadata_html = ""
        if metadata:
            metadata_html = '<div class="metadata-table">'
            metadata_html += "<h3>Report Metadata</h3>"
            metadata_html += "<table>"
            
            for key, value in metadata.items():
                if value is not None:
                    metadata_html += f"<tr><td><strong>{key}:</strong></td><td>{value}</td></tr>"
            
            metadata_html += "</table></div>"

        # Add footer disclaimer
        footer_html = """
        <div class="footer-disclaimer">
            <p><strong>CONFIDENTIAL - HIPAA Protected Health Information</strong></p>
            <p>This report contains Protected Health Information (PHI) and is intended solely for 
            authorized healthcare professionals. Unauthorized disclosure, copying, or distribution 
            is strictly prohibited and may violate federal and state laws.</p>
            <p>This analysis was generated using AI-assisted technology. All findings should be 
            reviewed and validated by qualified healthcare professionals before making clinical 
            or compliance decisions.</p>
            <p>Report generated by Therapy Compliance Analyzer - 
            © 2025 All Rights Reserved</p>
        </div>
        """

        # Wrap content with PDF-specific structure
        enhanced_html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <title>Compliance Report - {report_date}</title>
            <style>
                {self.pdf_css}
            </style>
        </head>
        <body>
            <div style="string-set: report-date '{report_date}';">
                {metadata_html}
                {html_content}
                {footer_html}
            </div>
        </body>
        </html>
        """

        return enhanced_html

    def _sanitize_filename(self, filename: str) -> str:
        """
        Sanitize filename for safe file system operations.

        Args:
            filename: Original filename

        Returns:
            Sanitized filename safe for file system
        """
        # Remove file extension if present
        name = Path(filename).stem
        
        # Replace unsafe characters
        safe_chars = []
        for char in name:
            if char.isalnum() or char in ("-", "_"):
                safe_chars.append(char)
            elif char.isspace():
                safe_chars.append("_")
        
        safe_name = "".join(safe_chars)
        
        # Limit length
        if len(safe_name) > 50:
            safe_name = safe_name[:50]
        
        return safe_name or "document"

    def purge_old_pdfs(self) -> Dict[str, Any]:
        """
        Purge PDFs older than retention period.

        Returns:
            Dict with purge statistics

        Raises:
            Exception: If purge operation fails
        """
        if not self.enable_auto_purge:
            logger.info("Auto-purge is disabled")
            return {"purged": 0, "message": "Auto-purge disabled"}

        try:
            cutoff_time = datetime.now(UTC) - timedelta(hours=self.retention_hours)
            purged_count = 0
            purged_size = 0

            for pdf_file in self.output_dir.glob("*.pdf"):
                # Check file modification time
                file_mtime = datetime.fromtimestamp(
                    pdf_file.stat().st_mtime, tz=UTC
                )
                
                if file_mtime < cutoff_time:
                    file_size = pdf_file.stat().st_size
                    pdf_file.unlink()
                    purged_count += 1
                    purged_size += file_size
                    logger.info(f"Purged old PDF: {pdf_file.name}")

            result = {
                "purged": purged_count,
                "total_size_mb": round(purged_size / (1024 * 1024), 2),
                "cutoff_time": cutoff_time.isoformat(),
            }

            logger.info(
                f"Purge complete: {purged_count} files, {result['total_size_mb']}MB freed"
            )
            return result

        except Exception as e:
            logger.exception(f"Failed to purge old PDFs: {e}")
            return {"error": str(e), "purged": 0}

    def get_pdf_info(self, pdf_path: str) -> Optional[Dict[str, Any]]:
        """
        Get information about a PDF file.

        Args:
            pdf_path: Path to PDF file

        Returns:
            Dict with PDF metadata or None if file doesn't exist
        """
        path = Path(pdf_path)
        
        if not path.exists():
            return None

        stat = path.stat()
        
        return {
            "filename": path.name,
            "path": str(path),
            "size_bytes": stat.st_size,
            "size_mb": round(stat.st_size / (1024 * 1024), 2),
            "created_at": datetime.fromtimestamp(stat.st_ctime, tz=UTC).isoformat(),
            "modified_at": datetime.fromtimestamp(stat.st_mtime, tz=UTC).isoformat(),
        }

    def list_pdfs(self) -> List[Dict[str, Any]]:
        """
        List all PDF files in output directory.

        Returns:
            List of PDF file information dicts
        """
        pdfs = []
        
        for pdf_file in sorted(
            self.output_dir.glob("*.pdf"),
            key=lambda p: p.stat().st_mtime,
            reverse=True,
        ):
            info = self.get_pdf_info(str(pdf_file))
            if info:
                pdfs.append(info)
        
        return pdfs
