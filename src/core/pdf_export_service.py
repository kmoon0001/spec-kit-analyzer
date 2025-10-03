"""
PDF Export Service for Compliance Reports

Converts HTML compliance reports to professional PDF documents with proper formatting,
headers, footers, and medical document styling.
"""

import logging
import os
import tempfile
from datetime import datetime
from typing import Dict, Optional, Any
from pathlib import Path

# PDF generation imports with fallback
try:
    from weasyprint import HTML, CSS
    from weasyprint.text.fonts import FontConfiguration
    PDF_AVAILABLE = True
except ImportError:
    try:
        import pdfkit
        PDF_AVAILABLE = True
        WEASYPRINT_AVAILABLE = False
    except ImportError:
        PDF_AVAILABLE = False
        WEASYPRINT_AVAILABLE = False

logger = logging.getLogger(__name__)


class PDFExportService:
    """
    Service for exporting compliance reports to PDF format.
    
    Supports multiple PDF generation backends:
    - WeasyPrint (preferred) - Better CSS support and medical document formatting
    - wkhtmltopdf (fallback) - Requires system installation
    """
    
    def __init__(self):
        self.pdf_available = PDF_AVAILABLE
        self.use_weasyprint = PDF_AVAILABLE and 'weasyprint' in globals()
        
        if not self.pdf_available:
            logger.warning("PDF export not available. Install weasyprint or pdfkit for PDF functionality.")
    
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
            styled_html = self._add_pdf_styling(html_content, metadata)
            
            if self.use_weasyprint:
                return self._export_with_weasyprint(styled_html, output_path, metadata)
            else:
                return self._export_with_pdfkit(styled_html, output_path, metadata)
                
        except Exception as e:
            logger.error(f"PDF export failed: {e}")
            return False
    
    def _add_pdf_styling(self, html_content: str, metadata: Optional[Dict[str, Any]] = None) -> str:
        """Add PDF-specific CSS styling for professional medical documents."""
        
        # Professional medical document CSS
        pdf_css = """
        <style>
        @page {
            size: A4;
            margin: 1in 0.75in 1in 0.75in;
            @top-left {
                content: "Therapy Compliance Analysis Report";
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
        
        # Add disclaimer footer
        disclaimer = """
        <div class="disclaimer">
            <strong>Important Disclaimer:</strong> This AI-generated report is for informational purposes only and does not constitute professional medical, legal, or compliance advice. All findings should be reviewed by qualified healthcare professionals. Patient health information has been automatically redacted to protect privacy.
        </div>
        
        <div class="footer-info">
            <p>Generated by Therapy Compliance Analyzer | Local AI Processing | HIPAA Compliant</p>
        </div>
        """
        
        # Inject styling and structure
        if '<head>' in html_content:
            html_content = html_content.replace('<head>', f'<head>{pdf_css}')
        else:
            html_content = f'<html><head>{pdf_css}</head><body>' + html_content + '</body></html>'
        
        # Add header after body tag
        if '<body>' in html_content:
            html_content = html_content.replace('<body>', f'<body>{pdf_header}')
        
        # Add disclaimer before closing body tag
        if '</body>' in html_content:
            html_content = html_content.replace('</body>', f'{disclaimer}</body>')
        
        return html_content
    
    def _export_with_weasyprint(self, html_content: str, output_path: str, metadata: Optional[Dict[str, Any]] = None) -> bool:
        """Export using WeasyPrint (preferred method)."""
        try:
            # Configure fonts
            font_config = FontConfiguration()
            
            # Create HTML document
            html_doc = HTML(string=html_content)
            
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
    
    def get_export_info(self) -> Dict[str, Any]:
        """Get information about PDF export capabilities."""
        return {
            "pdf_available": self.pdf_available,
            "backend": "weasyprint" if self.use_weasyprint else "pdfkit" if PDF_AVAILABLE else "none",
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