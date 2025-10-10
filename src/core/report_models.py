"""Report Models and Data Structures
import json

This module contains all the data models, enums, and protocols used by the reporting system.
Separated from the main engine for better maintainability and testing.
"""

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Protocol


class ReportType(Enum):
    """Types of reports that can be generated"""

    PERFORMANCE_ANALYSIS = "performance_analysis"
    COMPLIANCE_ANALYSIS = "compliance_analysis"
    DASHBOARD = "dashboard"
    EXECUTIVE_SUMMARY = "executive_summary"
    TREND_ANALYSIS = "trend_analysis"
    COMPARISON = "comparison"


class ReportFormat(Enum):
    """Supported report export formats"""

    HTML = "html"
    PDF = "pdf"
    EXCEL = "excel"
    JSON = "json"
    CSV = "csv"


class ReportStatus(Enum):
    """Report generation status"""

    PENDING = "pending"
    GENERATING = "generating"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass
class TimeRange:
    """Time range specification for reports"""

    start_time: datetime
    end_time: datetime

    def __post_init__(self):
        if self.start_time >= self.end_time:
            raise ValueError("Start time must be before end time")

    @classmethod
    def last_hours(cls, hours: int) -> "TimeRange":
        """Create time range for last N hours"""
        end_time = datetime.now()
        start_time = end_time - timedelta(hours=hours)
        return cls(start_time, end_time)

    @classmethod
    def last_days(cls, days: int) -> "TimeRange":
        """Create time range for last N days"""
        end_time = datetime.now()
        start_time = end_time - timedelta(days=days)
        return cls(start_time, end_time)


@dataclass
class ReportConfig:
    """Configuration for report generation"""

    report_type: ReportType
    title: str
    description: str = ""
    time_range: TimeRange | None = None
    template_id: str | None = None
    export_formats: list[ReportFormat] = field(default_factory=lambda: [ReportFormat.HTML])
    filters: dict[str, Any] = field(default_factory=dict)
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class ReportSection:
    """Individual section within a report"""

    id: str
    title: str
    content: str = ""
    data: dict[str, Any] = field(default_factory=dict)
    template_id: str | None = None


@dataclass
class Report:
    """Generated report structure"""

    id: str
    config: ReportConfig
    status: ReportStatus = ReportStatus.PENDING
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    sections: list[ReportSection] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)
    error_message: str | None = None
    file_paths: dict[ReportFormat, str] = field(default_factory=dict)

    def add_section(self, section: ReportSection) -> None:
        """Add a section to the report"""
        self.sections.append(section)

    def get_section(self, section_id: str) -> ReportSection | None:
        """Get a section by ID"""
        return next((s for s in self.sections if s.id == section_id), None)

    def to_dict(self) -> dict[str, Any]:
        """Convert report to dictionary for serialization"""
        return {
            "id": self.id,
            "config": {
                "report_type": self.config.report_type.value,
                "title": self.config.title,
                "description": self.config.description,
                "template_id": self.config.template_id,
                "export_formats": [f.value for f in self.config.export_formats],
                "filters": self.config.filters,
                "metadata": self.config.metadata,
            },
            "status": self.status.value,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "sections": [
                {
                    "id": section.id,
                    "title": section.title,
                    "content": section.content,
                    "data": section.data,
                    "template_id": section.template_id,
                }
                for section in self.sections
            ],
            "metadata": self.metadata,
            "error_message": self.error_message,
            "file_paths": {fmt.value: path for fmt, path in self.file_paths.items()},
        }


class DataProvider(Protocol):
    """Protocol for data providers that supply data to reports"""

    def get_data(self, report_type: ReportType, filters: dict[str, Any]) -> dict[str, Any]:
        """Get data for the specified report type and filters"""
        ...

    def supports_report_type(self, report_type: ReportType) -> bool:
        """Check if this provider supports the given report type"""
        ...


class TemplateRenderer(Protocol):
    """Protocol for template rendering engines"""

    def render_template(self, template_id: str, context: dict[str, Any]) -> str:
        """Render a template with the given context"""
        ...

    def get_available_templates(self) -> list[str]:
        """Get list of available template IDs"""
        ...


class ReportExporter(Protocol):
    """Protocol for report export functionality"""

    def export_report(self, report: Report, format: ReportFormat, output_path: str) -> bool:
        """Export a report to the specified format and path"""
        ...

    def supports_format(self, format: ReportFormat) -> bool:
        """Check if this exporter supports the given format"""
        ...
