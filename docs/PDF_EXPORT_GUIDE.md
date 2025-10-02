# PDF Export Feature - Implementation Guide

## Overview

The PDF Export feature converts HTML compliance reports into professional, audit-ready PDF documents with proper formatting, headers, footers, and HIPAA-compliant disclaimers.

## Features

### ✅ Professional Formatting
- Letter-size pages with proper margins
- Custom headers with report title and date
- Page numbers in footer
- HIPAA confidentiality disclaimer
- Professional typography and styling

### ✅ Metadata Integration
- Document name and analysis date
- Compliance score and findings count
- Document type and discipline
- Analyst information

### ✅ Security & Compliance
- HIPAA-compliant disclaimers
- Confidentiality notices
- AI transparency statements
- Secure file handling

### ✅ Auto-Purge Functionality
- Configurable retention period (default: 24 hours)
- Automatic cleanup of old reports
- Manual purge trigger available
- Purge statistics and logging

## Installation

### Dependencies

Add to `requirements.txt`:
```
weasyprint>=60.0
```

### System Requirements

WeasyPrint requires system libraries:

**Windows:**
```bash
# Install GTK3 runtime
# Download from: https://github.com/tschoonj/GTK-for-Windows-Runtime-Environment-Installer
```

**Linux (Ubuntu/Debian):**
```bash
sudo apt-get install python3-dev python3-pip python3-cffi libcairo2 libpango-1.0-0 libpangocairo-1.0-0 libgdk-pixbuf2.0-0 libffi-dev shared-mime-info
```

**macOS:**
```bash
brew install python3 cairo pango gdk-pixbuf libffi
```

## API Usage

### Export Report to PDF

```http
POST /api/analysis/export-pdf/{task_id}
Authorization: Bearer <token>
```

**Response:**
```json
{
  "task_id": "abc123",
  "pdf_info": {
    "success": true,
    "pdf_path": "temp/reports/compliance_report_document_20250101_120000.pdf",
    "filename": "compliance_report_document_20250101_120000.pdf",
    "file_size": 524288,
    "file_size_mb": 0.5,
    "generated_at": "2025-01-01T12:00:00Z",
    "purge_at": "2025-01-02T12:00:00Z"
  },
  "message": "PDF exported successfully"
}
```

### List Exported PDFs

```http
GET /api/analysis/pdfs
Authorization: Bearer <token>
```

**Response:**
```json
{
  "pdfs": [
    {
      "filename": "compliance_report_document_20250101_120000.pdf",
      "path": "temp/reports/compliance_report_document_20250101_120000.pdf",
      "size_bytes": 524288,
      "size_mb": 0.5,
      "created_at": "2025-01-01T12:00:00Z",
      "modified_at": "2025-01-01T12:00:00Z"
    }
  ],
  "count": 1
}
```

### Purge Old PDFs

```http
POST /api/analysis/purge-old-pdfs
Authorization: Bearer <token>
```

**Response:**
```json
{
  "message": "Purge completed",
  "statistics": {
    "purged": 5,
    "total_size_mb": 2.5,
    "cutoff_time": "2024-12-31T12:00:00Z"
  }
}
```

## Python Usage

### Basic Export

```python
from src.core.pdf_export_service import PDFExportService
from src.core.report_generator import ReportGenerator

# Generate HTML report
report_gen = ReportGenerator()
report_data = report_gen.generate_report(
    analysis_result=analysis_result,
    document_name="patient_note.pdf"
)

# Export to PDF
pdf_service = PDFExportService()
pdf_result = pdf_service.export_to_pdf(
    html_content=report_data["report_html"],
    document_name="patient_note.pdf",
    metadata={
        "Document": "patient_note.pdf",
        "Analysis Date": "2025-01-01",
        "Compliance Score": 85,
        "Total Findings": 3
    }
)

if pdf_result["success"]:
    print(f"PDF generated: {pdf_result['pdf_path']}")
else:
    print(f"Error: {pdf_result['error']}")
```

### Custom Configuration

```python
from src.core.pdf_export_service import PDFExportService

# Custom retention and output directory
pdf_service = PDFExportService(
    output_dir="custom/pdf/directory",
    retention_hours=48,  # 48 hours retention
    enable_auto_purge=True
)
```

### Manual Purge

```python
# Purge old PDFs manually
result = pdf_service.purge_old_pdfs()
print(f"Purged {result['purged']} files, freed {result['total_size_mb']}MB")
```

### List PDFs

```python
# Get all PDFs
pdfs = pdf_service.list_pdfs()
for pdf in pdfs:
    print(f"{pdf['filename']}: {pdf['size_mb']}MB")
```

## Configuration

### Environment Variables

```bash
# PDF output directory (optional)
PDF_OUTPUT_DIR=temp/reports

# Retention period in hours (optional)
PDF_RETENTION_HOURS=24

# Enable auto-purge (optional)
PDF_AUTO_PURGE=true
```

### YAML Configuration

Add to `config.yaml`:
```yaml
pdf_export:
  output_dir: temp/reports
  retention_hours: 24
  enable_auto_purge: true
```

## PDF Styling

### Custom CSS

The PDF service includes comprehensive CSS for professional formatting:

- **Page Setup**: Letter size, 1-inch margins
- **Headers**: Report title and generation date
- **Footers**: Page numbers and confidentiality notice
- **Risk Levels**: Color-coded (High=Red, Medium=Orange, Low=Green)
- **Confidence Indicators**: Background colors for confidence levels
- **Tables**: Professional styling with alternating row colors
- **Typography**: Clean, readable fonts

### Customization

To customize PDF styling, modify `src/core/pdf_export_service.py`:

```python
def _load_pdf_styles(self) -> str:
    """Load custom CSS styles for PDF rendering."""
    return """
    @page {
        size: Letter;
        margin: 1in 0.75in;
        /* Add custom page settings */
    }
    
    /* Add custom styles */
    """
```

## Scheduled Maintenance

### Auto-Purge Job

Add to APScheduler configuration:

```python
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from src.core.pdf_export_service import PDFExportService

scheduler = AsyncIOScheduler()

def purge_old_pdfs():
    """Scheduled job to purge old PDFs."""
    pdf_service = PDFExportService()
    result = pdf_service.purge_old_pdfs()
    logger.info(f"Auto-purge: {result['purged']} files removed")

# Run daily at 2 AM
scheduler.add_job(purge_old_pdfs, 'cron', hour=2)
scheduler.start()
```

## Security Considerations

### HIPAA Compliance

- ✅ PDFs include confidentiality disclaimers
- ✅ Auto-purge prevents long-term storage
- ✅ Secure file handling with proper permissions
- ✅ No PHI in filenames
- ✅ Audit logging of PDF generation

### File Security

```python
# Set restrictive file permissions (Unix/Linux)
import os
import stat

pdf_path = "temp/reports/report.pdf"
os.chmod(pdf_path, stat.S_IRUSR | stat.S_IWUSR)  # Owner read/write only
```

## Troubleshooting

### WeasyPrint Installation Issues

**Error: "cairo library not found"**
```bash
# Install system dependencies first
# See Installation section above
```

**Error: "Failed to load font"**
```bash
# Install additional fonts
sudo apt-get install fonts-liberation  # Linux
```

### PDF Generation Failures

**Check logs:**
```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

**Common issues:**
- Invalid HTML structure
- Missing CSS resources
- Insufficient disk space
- Permission errors

### Performance Optimization

**For large reports:**
```python
# Reduce image quality
# Simplify CSS
# Remove unnecessary content
```

## Testing

### Unit Tests

```bash
# Run PDF export tests
pytest tests/unit/test_pdf_export_service.py -v

# Run with coverage
pytest tests/unit/test_pdf_export_service.py --cov=src.core.pdf_export_service
```

### Integration Tests

```bash
# Test full workflow
pytest tests/integration/test_pdf_workflow.py -v
```

## Best Practices

### 1. Always Include Metadata
```python
metadata = {
    "Document": document_name,
    "Analysis Date": datetime.now().isoformat(),
    "Compliance Score": score,
    "Total Findings": len(findings),
}
```

### 2. Handle Errors Gracefully
```python
pdf_result = pdf_service.export_to_pdf(html, doc_name, metadata)
if not pdf_result["success"]:
    logger.error(f"PDF export failed: {pdf_result['error']}")
    # Fallback to HTML report
```

### 3. Monitor Disk Usage
```python
# Check available space before export
import shutil
stats = shutil.disk_usage(pdf_service.output_dir)
if stats.free < 100 * 1024 * 1024:  # Less than 100MB
    logger.warning("Low disk space for PDF export")
```

### 4. Regular Purging
```python
# Schedule regular purges
# Don't rely solely on auto-purge
```

## Future Enhancements

- [ ] Digital signature support
- [ ] Watermarking
- [ ] Custom templates
- [ ] Batch export
- [ ] Email delivery
- [ ] Cloud storage integration
- [ ] PDF/A compliance for archiving
- [ ] Compression options

## Support

For issues or questions:
- Check logs in `logs/pdf_export.log`
- Review WeasyPrint documentation: https://weasyprint.org/
- File issues in project repository

## License

This feature is part of the Therapy Compliance Analyzer and follows the same license terms.
