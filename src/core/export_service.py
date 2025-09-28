"""
Data Export Service - Safe, configurable export functionality.
Supports multiple formats with optional features that can be enabled/disabled.
"""
import logging
import json
import csv
from typing import Dict, Any, List, Optional, Union
from datetime import datetime
from pathlib import Path
import io

logger = logging.getLogger(__name__)

# Optional dependencies with graceful fallback
try:
    import pandas as pd
    PANDAS_AVAILABLE = True
except ImportError:
    logger.info("Pandas not available - Excel export disabled")
    PANDAS_AVAILABLE = False

class ExportService:
    """
    Configurable data export service supporting multiple formats.
    Features can be enabled/disabled based on requirements and dependencies.
    """
    
    def __init__(self, 
                 enable_excel: bool = True,
                 enable_csv: bool = True,
                 enable_json: bool = True,
                 max_file_size_mb: int = 100):
        
        self.enable_excel = enable_excel and PANDAS_AVAILABLE
        self.enable_csv = enable_csv
        self.enable_json = enable_json
        self.max_file_size_mb = max_file_size_mb
        
        logger.info(f"Export service initialized - Excel: {self.enable_excel}, "
                   f"CSV: {self.enable_csv}, JSON: {self.enable_json}")
    
    def get_available_formats(self) -> List[str]:
        """Get list of available export formats."""
        formats = []
        if self.enable_json:
            formats.append("json")
        if self.enable_csv:
            formats.append("csv")
        if self.enable_excel:
            formats.append("excel")
        return formats
    
    def export_compliance_data(self, 
                             reports_data: List[Dict[str, Any]], 
                             format_type: str,
                             output_path: str,
                             include_findings: bool = True) -> bool:
        """
        Export compliance data in specified format.
        
        Args:
            reports_data: List of report dictionaries
            format_type: Export format (json, csv, excel)
            output_path: Path where file should be saved
            include_findings: Whether to include detailed findings
            
        Returns:
            True if export successful, False otherwise
        """
        try:
            if not reports_data:
                logger.warning("No data to export")
                return False
            
            # Prepare data for export
            export_data = self._prepare_export_data(reports_data, include_findings)
            
            # Check file size estimate
            if not self._check_size_limit(export_data):
                logger.error("Export data exceeds size limit")
                return False
            
            # Export based on format
            if format_type.lower() == "json" and self.enable_json:
                return self._export_json(export_data, output_path)
            elif format_type.lower() == "csv" and self.enable_csv:
                return self._export_csv(export_data, output_path, include_findings)
            elif format_type.lower() == "excel" and self.enable_excel:
                return self._export_excel(export_data, output_path, include_findings)
            else:
                logger.error(f"Unsupported or disabled export format: {format_type}")
                return False
                
        except Exception as e:
            logger.error(f"Export failed: {e}")
            return False
    
    def _prepare_export_data(self, 
                           reports_data: List[Dict[str, Any]], 
                           include_findings: bool) -> Dict[str, Any]:
        """Prepare data for export with metadata."""
        
        # Basic report data
        reports_summary = []
        all_findings = []
        
        for report in reports_data:
            # Basic report info
            report_summary = {
                'document_name': report.get('document_name', 'Unknown'),
                'analysis_date': report.get('analysis_date', ''),
                'document_type': report.get('document_type', 'Unknown'),
                'compliance_score': report.get('compliance_score', 0),
                'total_findings': len(report.get('findings', []))
            }
            reports_summary.append(report_summary)
            
            # Detailed findings if requested
            if include_findings:
                findings = report.get('findings', [])
                for finding in findings:
                    finding_data = {
                        'document_name': report.get('document_name', 'Unknown'),
                        'analysis_date': report.get('analysis_date', ''),
                        'rule_id': finding.get('rule_id', 'Unknown'),
                        'risk_level': finding.get('risk', 'Unknown'),
                        'problematic_text': finding.get('problematic_text', '')[:200],  # Truncate long text
                        'recommendation': finding.get('personalized_tip', '')[:200]
                    }
                    all_findings.append(finding_data)
        
        return {
            'metadata': {
                'export_timestamp': datetime.now().isoformat(),
                'total_reports': len(reports_data),
                'total_findings': len(all_findings),
                'export_version': '1.0'
            },
            'reports': reports_summary,
            'findings': all_findings if include_findings else []
        }
    
    def _check_size_limit(self, data: Dict[str, Any]) -> bool:
        """Check if export data is within size limits."""
        try:
            # Rough size estimate
            json_str = json.dumps(data)
            size_mb = len(json_str.encode('utf-8')) / (1024 * 1024)
            
            if size_mb > self.max_file_size_mb:
                logger.warning(f"Export size ({size_mb:.1f}MB) exceeds limit ({self.max_file_size_mb}MB)")
                return False
            
            return True
            
        except Exception as e:
            logger.error(f"Error checking size limit: {e}")
            return True  # Allow export if size check fails
    
    def _export_json(self, data: Dict[str, Any], output_path: str) -> bool:
        """Export data as JSON file."""
        try:
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False, default=str)
            
            logger.info(f"JSON export completed: {output_path}")
            return True
            
        except Exception as e:
            logger.error(f"JSON export failed: {e}")
            return False
    
    def _export_csv(self, data: Dict[str, Any], output_path: str, include_findings: bool) -> bool:
        """Export data as CSV file(s)."""
        try:
            base_path = Path(output_path)
            base_name = base_path.stem
            base_dir = base_path.parent
            
            # Export reports summary
            reports_path = base_dir / f"{base_name}_reports.csv"
            with open(reports_path, 'w', newline='', encoding='utf-8') as f:
                if data['reports']:
                    writer = csv.DictWriter(f, fieldnames=data['reports'][0].keys())
                    writer.writeheader()
                    writer.writerows(data['reports'])
            
            # Export findings if included
            if include_findings and data['findings']:
                findings_path = base_dir / f"{base_name}_findings.csv"
                with open(findings_path, 'w', newline='', encoding='utf-8') as f:
                    writer = csv.DictWriter(f, fieldnames=data['findings'][0].keys())
                    writer.writeheader()
                    writer.writerows(data['findings'])
            
            logger.info(f"CSV export completed: {reports_path}")
            return True
            
        except Exception as e:
            logger.error(f"CSV export failed: {e}")
            return False
    
    def _export_excel(self, data: Dict[str, Any], output_path: str, include_findings: bool) -> bool:
        """Export data as Excel file with multiple sheets."""
        if not self.enable_excel:
            logger.error("Excel export not available")
            return False
        
        try:
            with pd.ExcelWriter(output_path, engine='openpyxl') as writer:
                # Reports sheet
                if data['reports']:
                    reports_df = pd.DataFrame(data['reports'])
                    reports_df.to_excel(writer, sheet_name='Reports', index=False)
                
                # Findings sheet
                if include_findings and data['findings']:
                    findings_df = pd.DataFrame(data['findings'])
                    findings_df.to_excel(writer, sheet_name='Findings', index=False)
                
                # Metadata sheet
                metadata_df = pd.DataFrame([data['metadata']])
                metadata_df.to_excel(writer, sheet_name='Metadata', index=False)
            
            logger.info(f"Excel export completed: {output_path}")
            return True
            
        except Exception as e:
            logger.error(f"Excel export failed: {e}")
            return False
    
    def export_analytics_summary(self, 
                               analytics_data: Dict[str, Any], 
                               output_path: str,
                               format_type: str = "json") -> bool:
        """
        Export analytics summary data.
        
        Args:
            analytics_data: Analytics results from analytics service
            output_path: Output file path
            format_type: Export format
            
        Returns:
            True if successful, False otherwise
        """
        try:
            if format_type.lower() == "json" and self.enable_json:
                with open(output_path, 'w', encoding='utf-8') as f:
                    json.dump(analytics_data, f, indent=2, default=str)
                return True
            
            elif format_type.lower() == "csv" and self.enable_csv:
                # Export key metrics as CSV
                metrics = analytics_data.get('metrics', {})
                if metrics:
                    with open(output_path, 'w', newline='', encoding='utf-8') as f:
                        writer = csv.writer(f)
                        writer.writerow(['Metric', 'Value'])
                        for key, value in metrics.items():
                            writer.writerow([key, value])
                return True
            
            else:
                logger.error(f"Unsupported format for analytics export: {format_type}")
                return False
                
        except Exception as e:
            logger.error(f"Analytics export failed: {e}")
            return False
    
    def create_export_summary(self, reports_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Create a summary of exportable data for user preview."""
        try:
            total_reports = len(reports_data)
            total_findings = sum(len(r.get('findings', [])) for r in reports_data)
            
            # Date range
            dates = [r.get('analysis_date') for r in reports_data if r.get('analysis_date')]
            date_range = "Unknown"
            if dates:
                try:
                    parsed_dates = [datetime.fromisoformat(d.replace('Z', '+00:00')) for d in dates if isinstance(d, str)]
                    if parsed_dates:
                        min_date = min(parsed_dates).strftime('%Y-%m-%d')
                        max_date = max(parsed_dates).strftime('%Y-%m-%d')
                        date_range = f"{min_date} to {max_date}"
                except Exception:
                    pass
            
            # Document types
            doc_types = {}
            for report in reports_data:
                doc_type = report.get('document_type', 'Unknown')
                doc_types[doc_type] = doc_types.get(doc_type, 0) + 1
            
            return {
                'total_reports': total_reports,
                'total_findings': total_findings,
                'date_range': date_range,
                'document_types': doc_types,
                'available_formats': self.get_available_formats(),
                'estimated_size_mb': self._estimate_export_size(reports_data)
            }
            
        except Exception as e:
            logger.error(f"Error creating export summary: {e}")
            return {}
    
    def _estimate_export_size(self, reports_data: List[Dict[str, Any]]) -> float:
        """Estimate export file size in MB."""
        try:
            # Sample a few reports to estimate size
            sample_size = min(10, len(reports_data))
            if sample_size == 0:
                return 0.0
            
            sample_data = self._prepare_export_data(reports_data[:sample_size], True)
            sample_json = json.dumps(sample_data)
            sample_size_mb = len(sample_json.encode('utf-8')) / (1024 * 1024)
            
            # Extrapolate to full dataset
            scale_factor = len(reports_data) / sample_size
            estimated_size = sample_size_mb * scale_factor
            
            return round(estimated_size, 2)
            
        except Exception as e:
            logger.error(f"Error estimating export size: {e}")
            return 0.0

# Global export service instance
export_service = ExportService()

def get_export_service(enable_excel: bool = True, 
                      enable_csv: bool = True, 
                      enable_json: bool = True) -> ExportService:
    """Get export service with specified configuration."""
    return ExportService(
        enable_excel=enable_excel,
        enable_csv=enable_csv,
        enable_json=enable_json
    )

# Configuration
EXPORT_CONFIG = {
    "enable_excel": True,
    "enable_csv": True,
    "enable_json": True,
    "max_file_size_mb": 100,
    "default_format": "json"
}

def is_export_format_available(format_type: str) -> bool:
    """Check if specific export format is available."""
    if format_type.lower() == "excel":
        return EXPORT_CONFIG.get("enable_excel", False) and PANDAS_AVAILABLE
    elif format_type.lower() == "csv":
        return EXPORT_CONFIG.get("enable_csv", True)
    elif format_type.lower() == "json":
        return EXPORT_CONFIG.get("enable_json", True)
    return False