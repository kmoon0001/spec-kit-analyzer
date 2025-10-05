"""
PDF Export Service for Compliance Reports

Converts HTML compliance reports to professional PDF documents with proper formatting,
headers, footers, and medical document styling.
"""

import logging
import os
from datetime import datetime, timedelta
from typing import Dict, Optional, Any
from pathlib import Path

# Initialize logger first
logger = logging.getLogger(__name__)

# PDF generation imports with fallback
try:
    from weasyprint import HTML
    from weasyprint.text.fonts import FontConfiguration
    WEASYPRINT_AVAILABLE = True
except (ImportError, OSError) as e:
    logger.warning(f"WeasyPrint not available: {e}. WeasyPrint is the preferred PDF generation backend.")
    WEASYPRINT_AVAILABLE = False

try:
    import pdfkit
    PDFKIT_AVAILABLE = True
except ImportError:
    logger.warning("pdfkit not available. This is a fallback PDF generation backend.")
    PDFKIT_AVAILABLE = False

PDF_AVAILABLE = WEASYPRINT_AVAILABLE or PDFKIT_AVAILABLE


class PDFExportService:
    """
    Service for exporting compliance reports to PDF format.
    
    Supports multiple PDF generation backends:
    - WeasyPrint (preferred) - Better CSS support and medical document formatting
    - wkhtmltopdf (fallback) - Requires system installation
    """
    
    def __init__(self, output_dir: str = "temp/reports", retention_hours: int = 24, enable_auto_purge: bool = True):
        self.pdf_available = PDF_AVAILABLE
        self.use_weasyprint = WEASYPRINT_AVAILABLE
        self.output_dir = Path(output_dir)
        self.retention_hours = retention_hours
        self.enable_auto_purge = enable_auto_purge
        
        # Create output directory if it doesn't exist
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        if not self.pdf_available:
            logger.warning("PDF export not available. Install weasyprint or pdfkit for PDF functionality.")
    
    def _sanitize_filename(self, filename: str) -> str:
        """Sanitize filename for safe file system usage."""
        if not filename:
            return "document"
        
        # Remove extension
        name = Path(filename).stem
        
        # Replace spaces with underscores
        name = name.replace(" ", "_")
        
        # Remove special characters, keep only alphanumeric and underscores
        import re
        name = re.sub(r'[^a-zA-Z0-9_]', '', name)
        
        # Truncate if too long
        if len(name) > 50:
            name = name[:50]
        
        return name or "document"
    
    def export_to_pdf(
        self, 
        html_content: str, 
        document_name: str = None,
        filename: str = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Export HTML report to PDF with comprehensive result information.
        
        Args:
            html_content: HTML content of the compliance report
            filename: Optional filename (will be sanitized)
            metadata: Optional metadata for PDF properties
            
        Returns:
            Dict with export results including success status, file path, etc.
        """
        if not self.pdf_available:
            return {
                "success": False,
                "error": "PDF export not available. Please install weasyprint or pdfkit.",
                "pdf_path": None,
                "file_size": 0
            }
        
        try:
            # Generate filename - always use compliance_report pattern unless explicit filename provided
            if not filename:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                filename = f"compliance_report_{timestamp}.pdf"
            
            # Sanitize filename
            safe_name = self._sanitize_filename(filename)
            output_path = self.output_dir / f"{safe_name}.pdf"
            
            # Ensure unique filename
            counter = 1
            while output_path.exists():
                output_path = self.output_dir / f"{safe_name}_{counter}.pdf"
                counter += 1
            
            # Add PDF-specific styling
            styled_html = self._add_pdf_styling(html_content, metadata, document_name)
            
            success = False
            if self.use_weasyprint:
                success = self._export_with_weasyprint(styled_html, str(output_path), metadata)
            elif PDFKIT_AVAILABLE:
                success = self._export_with_pdfkit(styled_html, str(output_path), metadata)
            
            if success:
                file_size = output_path.stat().st_size if output_path.exists() else 0
                
                # Calculate purge time if auto-purge is enabled
                purge_at = None
                if self.enable_auto_purge:
                    from datetime import timezone
                    purge_at = (datetime.now(timezone.utc) + timedelta(hours=self.retention_hours)).isoformat()
                
                return {
                    "success": True,
                    "pdf_path": str(output_path),
                    "file_size": file_size,
                    "filename": output_path.name,
                    "generated_at": datetime.now().isoformat(),
                    "purge_at": purge_at
                }
            else:
                return {
                    "success": False,
                    "error": "PDF generation failed. No suitable backend was available or it failed.",
                    "pdf_path": None,
                    "file_size": 0
                }
                
        except Exception as e:
            logger.error(f"PDF export failed: {e}")
            return {
                "success": False,
                "error": str(e),
                "pdf_path": None,
                "file_size": 0
            }
    
    def export_report_to_pdf(
        self, 
        html_content: str, 
        output_path: str, 
        metadata: Optional[Dict[str, Any]] = None
    ) -> bool:
        """
        Export HTML report to PDF with professional medical document formatting.
        
        Args:
            html_content: HTML content of the compliance report
            output_path: Path where PDF should be saved
            metadata: Optional metadata for PDF properties
            
        Returns:
            bool: True if export successful, False otherwise
        """
        if not self.pdf_available:
            logger.error("PDF export not available. Please install weasyprint or pdfkit.")
            return False
        
        try:
            # Ensure output directory exists
            os.makedirs(os.path.dirname(output_path), exist_ok=True)
            
            # Add PDF-specific styling
            styled_html = self._add_pdf_styling(html_content, metadata, None)
            
            if self.use_weasyprint:
                return self._export_with_weasyprint(styled_html, output_path, metadata)
            else:
                return self._export_with_pdfkit(styled_html, output_path, metadata)
                
        except Exception as e:
            logger.error(f"PDF export failed: {e}")
            return False
    
    def _add_pdf_styling(self, html_content: str, metadata: Optional[Dict[str, Any]] = None, document_name: str = None) -> str:
        """Add PDF-specific CSS styling for professional medical documents."""
        
        # Professional medical document CSS
        pdf_css = """
        <style>
        @page {
            size: A4;
            margin: 1in 0.75in 1in 0.75in;
            @top-left {
                content: "CONFIDENTIAL - Therapy Compliance Analysis Report";
                font-size: 10px;
                color: #666;
                font-family: Arial, sans-serif;
            }
            @top-right {
                content: "Page " counter(page) " of " counter(pages);
                font-size: 10px;
                color: #666;
                font-family: Arial, sans-serif;
            }
            @bottom-center {
                content: "Generated on """ + datetime.now().strftime("%B %d, %Y at %I:%M %p") + """";
                font-size: 9px;
                color: #888;
                font-family: Arial, sans-serif;
            }
        }
        
        body {
            font-family: 'Times New Roman', Times, serif;
            font-size: 11pt;
            line-height: 1.4;
            color: #333;
            margin: 0;
            padding: 0;
        }
        
        .pdf-header {
            text-align: center;
            border-bottom: 2px solid #1e40af;
            padding-bottom: 20px;
            margin-bottom: 30px;
        }
        
        .pdf-header h1 {
            color: #1e40af;
            font-size: 24pt;
            margin: 0 0 10px 0;
            font-weight: bold;
        }
        
        .pdf-header .subtitle {
            color: #666;
            font-size: 12pt;
            font-style: italic;
        }
        
        .executive-summary {
            background-color: #f8fafc;
            border: 1px solid #e2e8f0;
            border-radius: 8px;
            padding: 20px;
            margin: 20px 0;
            page-break-inside: avoid;
        }
        
        .score-dashboard {
            display: flex;
            justify-content: space-around;
            margin: 15px 0;
            text-align: center;
        }
        
        .score-item {
            flex: 1;
            padding: 10px;
        }
        
        .score-value {
            font-size: 18pt;
            font-weight: bold;
            display: block;
            color: #1e40af;
        }
        
        .score-label {
            font-size: 9pt;
            color: #666;
            margin-top: 5px;
        }
        
        .finding {
            margin: 15px 0;
            padding: 15px;
            border-radius: 6px;
            border-left: 4px solid #cbd5e1;
            page-break-inside: avoid;
            background-color: #fafafa;
        }
        
        .finding.high {
            border-left-color: #ef4444;
            background-color: #fef2f2;
        }
        
        .finding.medium {
            border-left-color: #f59e0b;
            background-color: #fffbeb;
        }
        
        .finding.low {
            border-left-color: #10b981;
            background-color: #f0fdf4;
        }
        
        .severity {
            font-weight: bold;
            padding: 3px 8px;
            border-radius: 3px;
            font-size: 9pt;
            color: white;
        }
        
        .severity.high { background-color: #ef4444; }
        .severity.medium { background-color: #f59e0b; }
        .severity.low { background-color: #10b981; }
        
        .risk-high { color: #ef4444; font-weight: bold; }
        .risk-medium { color: #f59e0b; font-weight: bold; }
        .risk-low { color: #10b981; font-weight: bold; }
        
        .confidence-indicator {
            display: inline-block;
            padding: 2px 6px;
            border-radius: 3px;
            font-size: 8pt;
            font-weight: bold;
        }
        
        .suggestion {
            background-color: #f1f5f9;
            padding: 10px;
            border-radius: 4px;
            margin-top: 8px;
            border-left: 3px solid #0ea5e9;
            font-style: italic;
        }
        
        .evidence {
            font-style: italic;
            color: #64748b;
            margin-top: 8px;
            font-size: 10pt;
        }
        
        h1, h2, h3 {
            color: #1e40af;
            page-break-after: avoid;
        }
        
        h1 { font-size: 18pt; margin: 25px 0 15px 0; }
        h2 { font-size: 14pt; margin: 20px 0 10px 0; border-bottom: 1px solid #e2e8f0; padding-bottom: 5px; }
        h3 { font-size: 12pt; margin: 15px 0 8px 0; }
        
        .page-break {
            page-break-before: always;
        }
        
        .no-break {
            page-break-inside: avoid;
        }
        
        table {
            width: 100%;
            border-collapse: collapse;
            margin: 15px 0;
            font-size: 10pt;
        }
        
        th, td {
            border: 1px solid #e2e8f0;
            padding: 8px;
            text-align: left;
            vertical-align: top;
        }
        
        th {
            background-color: #f1f5f9;
            font-weight: bold;
            color: #1e40af;
        }
        
        .disclaimer {
            background-color: #f9fafb;
            border: 1px solid #d1d5db;
            border-radius: 6px;
            padding: 15px;
            margin: 20px 0;
            font-size: 9pt;
            color: #374151;
            page-break-inside: avoid;
        }
        
        .footer-info {
            margin-top: 30px;
            padding-top: 15px;
            border-top: 1px solid #e2e8f0;
            font-size: 9pt;
            color: #666;
            text-align: center;
        }
        
        /* Remove interactive elements for PDF */
        a[href^="chat://"], a[href^="highlight://"] {
            color: #1e40af;
            text-decoration: none;
            font-weight: normal;
        }
        
        a[href^="chat://"]:after {
            content: " (AI Chat)";
            font-size: 8pt;
            color: #666;
        }
        
        a[href^="highlight://"]:after {
            content: " (See Document)";
            font-size: 8pt;
            color: #666;
        }
        </style>
        """
        
        # Add PDF header
        pdf_header = f"""
        <div class="pdf-header">
            <h1>Clinical Compliance Analysis Report</h1>
            <div class="subtitle">Medicare & Regulatory Compliance Assessment</div>
            {f'<div class="subtitle">Document: {metadata.get("document_name", "Unknown")}</div>' if metadata else ''}
        </div>
        """
        
        # Add metadata section if provided
        metadata_section = ""
        if metadata:
            metadata_section = f"""
            <div class="report-metadata">
                <h2>Report Metadata</h2>
                <table>
                    <tr><th>Document</th><td>{metadata.get("Document", document_name or "Unknown")}</td></tr>
                    <tr><th>Document Type</th><td>{metadata.get("Document Type", "Progress Note")}</td></tr>
                    <tr><th>Analysis Date</th><td>{metadata.get("Analysis Date", "Unknown")}</td></tr>
                    <tr><th>Discipline</th><td>{metadata.get("Discipline", "Unknown")}</td></tr>
                    <tr><th>Compliance Score</th><td>{metadata.get("Compliance Score", "N/A")}</td></tr>
                </table>
            </div>
            """
        
        # Add disclaimer footer
        disclaimer = """
        <div class="disclaimer">
            <strong>Important Disclaimer:</strong> This AI-generated report is for informational purposes only and does not constitute professional medical, legal, or compliance advice. All findings should be reviewed by qualified healthcare professionals. Patient health information has been automatically redacted to protect privacy.
        </div>
        
        <div class="footer-info">
            <p>Generated by Therapy Compliance Analyzer | AI-assisted technology | HIPAA Protected | Local AI Processing</p>
        </div>
        """
        
        # Inject styling and structure
        if '<head>' in html_content:
            html_content = html_content.replace('<head>', f'<head>{pdf_css}')
        else:
            html_content = f'<html><head>{pdf_css}</head><body>' + html_content + '</body></html>'
        
        # Add header after body tag
        if '<body>' in html_content:
            html_content = html_content.replace('<body>', f'<body>{pdf_header}{metadata_section}')
        
        # Add disclaimer before closing body tag
        if '</body>' in html_content:
            html_content = html_content.replace('</body>', f'{disclaimer}</body>')
        
        return html_content
    
    def _export_with_weasyprint(self, html_content: str, output_path: str, metadata: Optional[Dict[str, Any]] = None) -> bool:
        """Export using WeasyPrint (preferred method)."""
        try:
            # Create HTML document
            html_doc = HTML(string=html_content)
            
            # Configure fonts
            font_config = FontConfiguration()
            
            # Generate PDF
            html_doc.write_pdf(
                output_path,
                font_config=font_config,
                optimize_images=True
            )
            
            logger.info(f"PDF exported successfully using WeasyPrint: {output_path}")
            return True
            
        except Exception as e:
            logger.error(f"WeasyPrint export failed: {e}")
            return False
    
    def _export_with_pdfkit(self, html_content: str, output_path: str, metadata: Optional[Dict[str, Any]] = None) -> bool:
        """Export using pdfkit/wkhtmltopdf (fallback method)."""
        try:
            options = {
                'page-size': 'A4',
                'margin-top': '1in',
                'margin-right': '0.75in',
                'margin-bottom': '1in',
                'margin-left': '0.75in',
                'encoding': "UTF-8",
                'no-outline': None,
                'enable-local-file-access': None,
                'print-media-type': None,
            }
            
            # Add header and footer
            if metadata:
                options['header-left'] = 'Therapy Compliance Analysis Report'
                options['header-right'] = '[page] of [topage]'
                options['header-font-size'] = '9'
                options['footer-center'] = f'Generated on {datetime.now().strftime("%B %d, %Y at %I:%M %p")}'
                options['footer-font-size'] = '8'
            
            pdfkit.from_string(html_content, output_path, options=options)
            
            logger.info(f"PDF exported successfully using pdfkit: {output_path}")
            return True
            
        except Exception as e:
            logger.error(f"pdfkit export failed: {e}")
            return False
    
    def enhance_html_for_pdf(self, html_content: str, metadata: Optional[Dict[str, Any]] = None) -> str:
        """Enhance HTML content for PDF export with metadata and styling."""
        return self._add_pdf_styling(html_content, metadata, None)
    
    def _enhance_html_for_pdf(self, html_content: str, metadata: Optional[Dict[str, Any]] = None) -> str:
        """Private method for HTML enhancement (for backward compatibility with tests)."""
        return self._add_pdf_styling(html_content, metadata, None)
    
    def purge_old_pdfs(self) -> Dict[str, Any]:
        """Remove old PDF files based on retention policy."""
        if not self.enable_auto_purge:
            return {
                "success": True,
                "purged": 0,
                "message": "Auto-purge disabled"
            }
        
        try:
            cutoff_time = datetime.now() - timedelta(hours=self.retention_hours)
            purged_count = 0
            
            for pdf_file in self.output_dir.glob("*.pdf"):
                if pdf_file.stat().st_mtime < cutoff_time.timestamp():
                    pdf_file.unlink()
                    purged_count += 1
            
            return {
                "success": True,
                "purged": purged_count,
                "message": f"Purged {purged_count} old PDF files"
            }
            
        except Exception as e:
            logger.error(f"PDF purge failed: {e}")
            return {
                "success": False,
                "purged": 0,
                "error": str(e)
            }
    
    def get_pdf_info(self, pdf_path: str) -> Optional[Dict[str, Any]]:
        """Get information about a specific PDF file."""
        try:
            path = Path(pdf_path)
            if not path.exists():
                return None
            
            stat = path.stat()
            return {
                "path": str(path),
                "filename": path.name,
                "size": stat.st_size,
                "size_bytes": stat.st_size,  # For backward compatibility
                "created_at": datetime.fromtimestamp(stat.st_ctime),
                "modified_at": datetime.fromtimestamp(stat.st_mtime)
            }
            
        except Exception as e:
            logger.error(f"Failed to get PDF info: {e}")
            return None
    
    def list_pdfs(self) -> list:
        """List all PDF files in the output directory."""
        try:
            pdf_files = []
            for pdf_file in self.output_dir.glob("*.pdf"):
                info = self.get_pdf_info(str(pdf_file))
                if info:
                    pdf_files.append(info)
            
            # Sort by modification time, newest first
            pdf_files.sort(key=lambda x: x["modified_at"], reverse=True)
            return pdf_files
            
        except Exception as e:
            logger.error(f"Failed to list PDFs: {e}")
            return []
    
    @property
    def pdf_css(self) -> str:
        """Get the CSS styling used for PDF generation."""
        return """
        @page {
            size: Letter;
            margin: 1in 0.75in 1in 0.75in;
            @top-left {
                content: "CONFIDENTIAL - Therapy Compliance Report";
                font-size: 9px;
                color: #666;
            }
            @top-right {
                content: "Page " counter(page) " of " counter(pages);
                font-size: 9px;
                color: #666;
            }
            @bottom-center {
                content: "CONFIDENTIAL";
                font-size: 8px;
                color: #999;
            }
            @bottom-right {
                content: "Generated: " date();
                font-size: 8px;
                color: #999;
            }
        }
        
        .risk-high { color: #dc2626; font-weight: bold; }
        .risk-medium { color: #f59e0b; font-weight: bold; }
        .risk-low { color: #16a34a; font-weight: bold; }
        
        .confidence-high { border-left: 3px solid #16a34a; }
        .confidence-medium { border-left: 3px solid #f59e0b; }
        .confidence-low { border-left: 3px solid #dc2626; }
        
        .high-confidence { background-color: #f0fdf4; border: 1px solid #16a34a; }
        .medium-confidence { background-color: #fffbeb; border: 1px solid #f59e0b; }
        .low-confidence { background-color: #fef2f2; border: 1px solid #dc2626; }
        
        .disputed { 
            background-color: #fee2e2; 
            text-decoration: line-through; 
            opacity: 0.7; 
        }
        """
    
    def get_export_info(self) -> Dict[str, Any]:
        """Get information about PDF export capabilities."""
        return {
            "pdf_available": self.pdf_available,
            "backend": "weasyprint" if self.use_weasyprint else "pdfkit" if PDF_AVAILABLE else "none",
            "output_dir": str(self.output_dir),
            "retention_hours": self.retention_hours,
            "auto_purge_enabled": self.enable_auto_purge,
            "features": {
                "professional_formatting": True,
                "headers_footers": True,
                "medical_styling": True,
                "page_breaks": True,
                "interactive_elements_converted": True,
            } if self.pdf_available else {}
        }


# Global service instance
pdf_export_service = PDFExportService()


def export_compliance_report_to_pdf(
    html_content: str, 
    output_path: str, 
    document_name: Optional[str] = None
) -> bool:
    """
    Convenience function to export compliance report to PDF.
    
    Args:
        html_content: HTML content of the compliance report
        output_path: Path where PDF should be saved
        document_name: Name of the original document being analyzed
        
    Returns:
        bool: True if export successful, False otherwise
    """
    metadata = {"document_name": document_name} if document_name else None
    return pdf_export_service.export_report_to_pdf(html_content, output_path, metadata)