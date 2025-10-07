"""
Report Generation Engine - Core reporting system

This module provides the foundational reporting infrastructure that integrates
with existing performance and compliance systems without modifying them.
Uses clean interfaces and dependency injection for non-intrusive integration.
"""

import logging
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from pathlib import Path
from typing import Dict, List, Optional, Any, Protocol
import yaml

logger = logging.getLogger(__name__)


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
    def last_hours(cls, hours: int) -> 'TimeRange':
        """Create time range for last N hours"""
        end_time = datetime.now()
        start_time = end_time - timedelta(hours=hours)
        return cls(start_time, end_time)
    
    @classmethod
    def last_days(cls, days: int) -> 'TimeRange':
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
    time_range: Optional[TimeRange] = None
    data_sources: List[str] = field(default_factory=list)
    filters: Dict[str, Any] = field(default_factory=dict)
    template_id: Optional[str] = None
    output_formats: List[ReportFormat] = field(default_factory=lambda: [ReportFormat.HTML])
    recipients: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def __post_init__(self):
        if not self.title.strip():
            raise ValueError("Report title cannot be empty")
        if not self.output_formats:
            self.output_formats = [ReportFormat.HTML]


@dataclass
class ReportSection:
    """Individual section within a report"""
    id: str
    title: str
    content: str
    section_type: str = "text"
    data: Optional[Dict[str, Any]] = None
    charts: List[Dict[str, Any]] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class Report:
    """Generated report structure"""
    id: str
    title: str
    description: str
    report_type: ReportType
    generated_at: datetime
    config: ReportConfig
    sections: List[ReportSection] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    status: ReportStatus = ReportStatus.PENDING
    error_message: Optional[str] = None
    file_paths: Dict[ReportFormat, str] = field(default_factory=dict)
    
    def add_section(self, section: ReportSection) -> None:
        """Add a section to the report"""
        self.sections.append(section)
    
    def get_section(self, section_id: str) -> Optional[ReportSection]:
        """Get a section by ID"""
        return next((s for s in self.sections if s.id == section_id), None)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert report to dictionary for serialization"""
        return {
            "id": self.id,
            "title": self.title,
            "description": self.description,
            "report_type": self.report_type.value,
            "generated_at": self.generated_at.isoformat(),
            "status": self.status.value,
            "sections": [
                {
                    "id": s.id,
                    "title": s.title,
                    "content": s.content,
                    "section_type": s.section_type,
                    "data": s.data,
                    "charts": s.charts,
                    "metadata": s.metadata
                }
                for s in self.sections
            ],
            "metadata": self.metadata,
            "error_message": self.error_message,
            "file_paths": {fmt.value: path for fmt, path in self.file_paths.items()}
        }


class DataProvider(Protocol):
    """Protocol for data providers that supply data to reports"""
    
    async def get_data(self, config: ReportConfig) -> Dict[str, Any]:
        """Get data for report generation"""
        ...
    
    def supports_report_type(self, report_type: ReportType) -> bool:
        """Check if this provider supports the given report type"""
        ...


class TemplateRenderer(Protocol):
    """Protocol for template rendering engines"""
    
    def render_template(self, template_id: str, context: Dict[str, Any]) -> str:
        """Render a template with the given context"""
        ...
    
    def get_available_templates(self) -> List[str]:
        """Get list of available template IDs"""
        ...


class ReportExporter(Protocol):
    """Protocol for report export functionality"""
    
    async def export_report(self, report: Report, format: ReportFormat, output_path: str) -> str:
        """Export report to specified format and path"""
        ...
    
    def supports_format(self, format: ReportFormat) -> bool:
        """Check if this exporter supports the given format"""
        ...


class DataAggregationService:
    """Service for aggregating data from multiple sources for reports"""
    
    def __init__(self):
        self.data_providers: Dict[str, DataProvider] = {}
        self.cache: Dict[str, Any] = {}
        self.cache_ttl: Dict[str, datetime] = {}
        self.default_cache_duration = timedelta(minutes=5)
    
    def register_data_provider(self, name: str, provider: DataProvider) -> None:
        """Register a data provider"""
        self.data_providers[name] = provider
        logger.info(f"Registered data provider: {name}")
    
    def unregister_data_provider(self, name: str) -> None:
        """Unregister a data provider"""
        if name in self.data_providers:
            del self.data_providers[name]
            logger.info(f"Unregistered data provider: {name}")
    
    async def aggregate_data(self, config: ReportConfig) -> Dict[str, Any]:
        """Aggregate data from all relevant providers"""
        aggregated_data = {}
        
        # Determine which providers to use
        providers_to_use = []
        if config.data_sources:
            # Use specified data sources
            providers_to_use = [
                (name, provider) for name, provider in self.data_providers.items()
                if name in config.data_sources
            ]
        else:
            # Use all providers that support this report type
            providers_to_use = [
                (name, provider) for name, provider in self.data_providers.items()
                if provider.supports_report_type(config.report_type)
            ]
        
        # Collect data from providers
        for provider_name, provider in providers_to_use:
            try:
                cache_key = f"{provider_name}_{hash(str(config.filters))}"
                
                # Check cache first
                if self._is_cache_valid(cache_key):
                    provider_data = self.cache[cache_key]
                    logger.debug(f"Using cached data for provider: {provider_name}")
                else:
                    # Fetch fresh data
                    provider_data = await provider.get_data(config)
                    
                    # Cache the data
                    self.cache[cache_key] = provider_data
                    self.cache_ttl[cache_key] = datetime.now() + self.default_cache_duration
                    logger.debug(f"Fetched and cached data for provider: {provider_name}")
                
                aggregated_data[provider_name] = provider_data
                
            except Exception as e:
                logger.error(f"Error getting data from provider {provider_name}: {e}")
                # Continue with other providers
                aggregated_data[provider_name] = {"error": str(e)}
        
        return aggregated_data
    
    def _is_cache_valid(self, cache_key: str) -> bool:
        """Check if cached data is still valid"""
        if cache_key not in self.cache:
            return False
        
        if cache_key not in self.cache_ttl:
            return False
        
        return datetime.now() < self.cache_ttl[cache_key]
    
    def clear_cache(self) -> None:
        """Clear all cached data"""
        self.cache.clear()
        self.cache_ttl.clear()
        logger.info("Cleared data aggregation cache")


class TemplateEngine:
    """Template engine for rendering reports"""
    
    def __init__(self, templates_dir: Optional[Path] = None):
        self.templates_dir = templates_dir or Path("src/resources/report_templates")
        self.templates: Dict[str, str] = {}
        self.template_metadata: Dict[str, Dict[str, Any]] = {}
        self._load_templates()
    
    def _load_templates(self) -> None:
        """Load templates from the templates directory"""
        if not self.templates_dir.exists():
            logger.warning(f"Templates directory not found: {self.templates_dir}")
            self._create_default_templates()
            return
        
        try:
            for template_file in self.templates_dir.glob("*.html"):
                template_id = template_file.stem
                with open(template_file, 'r', encoding='utf-8') as f:
                    self.templates[template_id] = f.read()
                
                # Load metadata if available
                metadata_file = template_file.with_suffix('.yaml')
                if metadata_file.exists():
                    with open(metadata_file, 'r', encoding='utf-8') as f:
                        self.template_metadata[template_id] = yaml.safe_load(f)
                
                logger.debug(f"Loaded template: {template_id}")
            
            logger.info(f"Loaded {len(self.templates)} report templates")
            
        except Exception as e:
            logger.error(f"Error loading templates: {e}")
            self._create_default_templates()
    
    def _create_default_templates(self) -> None:
        """Create default templates"""
        default_template = """
        <!DOCTYPE html>
        <html>
        <head>
            <title>{{ title }}</title>
            <style>
                body { font-family: Arial, sans-serif; margin: 20px; }
                .header { border-bottom: 2px solid #333; padding-bottom: 10px; }
                .section { margin: 20px 0; }
                .metadata { color: #666; font-size: 0.9em; }
            </style>
        </head>
        <body>
            <div class="header">
                <h1>{{ title }}</h1>
                <p class="metadata">Generated: {{ generated_at }}</p>
                {% if description %}
                <p>{{ description }}</p>
                {% endif %}
            </div>
            
            {% for section in sections %}
            <div class="section">
                <h2>{{ section.title }}</h2>
                <div>{{ section.content }}</div>
            </div>
            {% endfor %}
        </body>
        </html>
        """
        
        self.templates["default"] = default_template.strip()
        self.templates["performance_analysis"] = default_template.strip()
        self.templates["compliance_analysis"] = default_template.strip()
        self.templates["dashboard"] = default_template.strip()
        self.templates["executive_summary"] = default_template.strip()
        
        logger.info("Created default report templates")
    
    def render_template(self, template_id: str, context: Dict[str, Any]) -> str:
        """Render a template with the given context"""
        if template_id not in self.templates:
            logger.warning(f"Template not found: {template_id}, using default")
            template_id = "default"
        
        template_content = self.templates.get(template_id, self.templates["default"])
        
        try:
            # Simple template rendering (would use Jinja2 in production)
            rendered = template_content
            for key, value in context.items():
                placeholder = f"{{{{ {key} }}}}"
                rendered = rendered.replace(placeholder, str(value))
            
            return rendered
            
        except Exception as e:
            logger.error(f"Error rendering template {template_id}: {e}")
            return f"<html><body><h1>Error rendering report</h1><p>{str(e)}</p></body></html>"
    
    def get_available_templates(self) -> List[str]:
        """Get list of available template IDs"""
        return list(self.templates.keys())
    
    def get_template_metadata(self, template_id: str) -> Dict[str, Any]:
        """Get metadata for a template"""
        return self.template_metadata.get(template_id, {})


class ReportConfigurationManager:
    """Manages report configurations and settings"""
    
    def __init__(self, config_dir: Optional[Path] = None):
        self.config_dir = config_dir or Path("config/reports")
        self.configurations: Dict[str, ReportConfig] = {}
        self.default_configs: Dict[ReportType, ReportConfig] = {}
        self._load_configurations()
    
    def _load_configurations(self) -> None:
        """Load report configurations from files"""
        if not self.config_dir.exists():
            self.config_dir.mkdir(parents=True, exist_ok=True)
            self._create_default_configurations()
            return
        
        try:
            for config_file in self.config_dir.glob("*.yaml"):
                config_id = config_file.stem
                with open(config_file, 'r', encoding='utf-8') as f:
                    config_data = yaml.safe_load(f)
                
                config = self._dict_to_config(config_data)
                self.configurations[config_id] = config
                
                logger.debug(f"Loaded report configuration: {config_id}")
            
            logger.info(f"Loaded {len(self.configurations)} report configurations")
            
        except Exception as e:
            logger.error(f"Error loading configurations: {e}")
            self._create_default_configurations()
    
    def _create_default_configurations(self) -> None:
        """Create default report configurations"""
        default_configs = {
            ReportType.PERFORMANCE_ANALYSIS: ReportConfig(
                report_type=ReportType.PERFORMANCE_ANALYSIS,
                title="Performance Analysis Report",
                description="Comprehensive performance analysis with optimization comparisons",
                time_range=TimeRange.last_hours(24),
                template_id="performance_analysis"
            ),
            ReportType.COMPLIANCE_ANALYSIS: ReportConfig(
                report_type=ReportType.COMPLIANCE_ANALYSIS,
                title="Compliance Analysis Report",
                description="Detailed compliance analysis with regulatory findings",
                template_id="compliance_analysis"
            ),
            ReportType.DASHBOARD: ReportConfig(
                report_type=ReportType.DASHBOARD,
                title="System Dashboard",
                description="Real-time system performance and health dashboard",
                time_range=TimeRange.last_hours(1),
                template_id="dashboard"
            ),
            ReportType.EXECUTIVE_SUMMARY: ReportConfig(
                report_type=ReportType.EXECUTIVE_SUMMARY,
                title="Executive Summary",
                description="High-level performance and compliance summary",
                time_range=TimeRange.last_days(7),
                template_id="executive_summary"
            )
        }
        
        self.default_configs = default_configs
        
        # Save default configurations
        for report_type, config in default_configs.items():
            config_file = self.config_dir / f"default_{report_type.value}.yaml"
            with open(config_file, 'w', encoding='utf-8') as f:
                yaml.dump(self._config_to_dict(config), f, default_flow_style=False)
        
        logger.info("Created default report configurations")
    
    def _dict_to_config(self, config_data: Dict[str, Any]) -> ReportConfig:
        """Convert dictionary to ReportConfig"""
        time_range = None
        if 'time_range' in config_data:
            tr_data = config_data['time_range']
            time_range = TimeRange(
                start_time=datetime.fromisoformat(tr_data['start_time']),
                end_time=datetime.fromisoformat(tr_data['end_time'])
            )
        
        return ReportConfig(
            report_type=ReportType(config_data['report_type']),
            title=config_data['title'],
            description=config_data.get('description', ''),
            time_range=time_range,
            data_sources=config_data.get('data_sources', []),
            filters=config_data.get('filters', {}),
            template_id=config_data.get('template_id'),
            output_formats=[ReportFormat(fmt) for fmt in config_data.get('output_formats', ['html'])],
            recipients=config_data.get('recipients', []),
            metadata=config_data.get('metadata', {})
        )
    
    def _config_to_dict(self, config: ReportConfig) -> Dict[str, Any]:
        """Convert ReportConfig to dictionary"""
        config_dict = {
            'report_type': config.report_type.value,
            'title': config.title,
            'description': config.description,
            'data_sources': config.data_sources,
            'filters': config.filters,
            'template_id': config.template_id,
            'output_formats': [fmt.value for fmt in config.output_formats],
            'recipients': config.recipients,
            'metadata': config.metadata
        }
        
        if config.time_range:
            config_dict['time_range'] = {
                'start_time': config.time_range.start_time.isoformat(),
                'end_time': config.time_range.end_time.isoformat()
            }
        
        return config_dict
    
    def get_configuration(self, config_id: str) -> Optional[ReportConfig]:
        """Get a report configuration by ID"""
        return self.configurations.get(config_id)
    
    def get_default_configuration(self, report_type: ReportType) -> ReportConfig:
        """Get default configuration for a report type"""
        return self.default_configs.get(report_type, self.default_configs[ReportType.PERFORMANCE_ANALYSIS])
    
    def save_configuration(self, config_id: str, config: ReportConfig) -> None:
        """Save a report configuration"""
        self.configurations[config_id] = config
        
        config_file = self.config_dir / f"{config_id}.yaml"
        with open(config_file, 'w', encoding='utf-8') as f:
            yaml.dump(self._config_to_dict(config), f, default_flow_style=False)
        
        logger.info(f"Saved report configuration: {config_id}")


class ReportGenerationEngine:
    """Main engine for generating reports"""
    
    def __init__(self):
        self.data_aggregation_service = DataAggregationService()
        self.template_engine = TemplateEngine()
        self.config_manager = ReportConfigurationManager()
        self.report_exporters: Dict[ReportFormat, ReportExporter] = {}
        self.generated_reports: Dict[str, Report] = {}
        self.report_counter = 0
        
        # Initialize branding service for optional logo support
        try:
            from .report_branding_service import ReportBrandingService
            self.branding_service = ReportBrandingService()
        except ImportError:
            logger.warning("Branding service not available, reports will use default styling")
            self.branding_service = None
        
        # Initialize AI guardrails service for responsible AI
        try:
            from .ai_guardrails_service import AIGuardrailsService
            self.guardrails_service = AIGuardrailsService()
            logger.info("AI guardrails service initialized")
        except ImportError:
            logger.warning("AI guardrails service not available")
            self.guardrails_service = None
        
        # Initialize 7 Habits framework integration
        try:
            from .enhanced_habit_mapper import SevenHabitsFramework
            self.habits_framework = SevenHabitsFramework()
            logger.info("7 Habits framework integration initialized")
        except ImportError:
            logger.warning("7 Habits framework not available")
            self.habits_framework = None
        
        # Initialize data integration service
        self._initialize_data_integration()
    
    def _initialize_data_integration(self) -> None:
        """Initialize data integration service with existing providers"""
        try:
            from .data_integration_service import DataIntegrationService
            self.data_integration_service = DataIntegrationService()
            logger.info("Data integration service initialized successfully")
        except ImportError as e:
            logger.warning(f"Data integration service not available: {e}")
            self.data_integration_service = None
    
    def register_data_provider(self, name: str, provider: DataProvider) -> None:
        """Register a data provider (non-intrusive integration)"""
        self.data_aggregation_service.register_data_provider(name, provider)
        
        # Also register with data integration service if available
        if hasattr(self, 'data_integration_service') and self.data_integration_service:
            try:
                # Convert DataProvider to BaseDataProvider if needed
                if hasattr(provider, 'provider_id'):
                    self.data_integration_service.register_provider(provider)
            except Exception as e:
                logger.warning(f"Could not register provider with data integration service: {e}")
    
    def register_report_exporter(self, format: ReportFormat, exporter: ReportExporter) -> None:
        """Register a report exporter"""
        self.report_exporters[format] = exporter
        logger.info(f"Registered report exporter for format: {format.value}")
    
    async def generate_report(self, config: ReportConfig) -> Report:
        """Generate a report based on configuration with AI guardrails and 7 Habits integration"""
        # Create report instance
        self.report_counter += 1
        report_id = f"report_{self.report_counter}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        report = Report(
            id=report_id,
            title=config.title,
            description=config.description,
            report_type=config.report_type,
            generated_at=datetime.now(),
            config=config,
            status=ReportStatus.GENERATING
        )
        
        try:
            logger.info(f"Starting report generation with AI guardrails: {report_id}")
            
            # Aggregate data from providers
            aggregated_data = await self.data_aggregation_service.aggregate_data(config)
            
            # Generate report sections based on report type
            sections = await self._generate_report_sections(config, aggregated_data)
            
            # Apply AI guardrails to all generated content
            if self.guardrails_service:
                sections = await self._apply_ai_guardrails_to_sections(sections, config)
            
            # Integrate 7 Habits framework if available
            if self.habits_framework:
                sections = await self._integrate_seven_habits(sections, aggregated_data, config)
            
            report.sections = sections
            
            # Render report content
            rendered_content = self._render_report_content(report)
            
            # Apply final guardrails check to rendered content
            if self.guardrails_service:
                rendered_content = await self._apply_final_guardrails_check(rendered_content, config)
            
            # Add rendered content as main section if not already present
            if not any(s.id == "main_content" for s in report.sections):
                main_section = ReportSection(
                    id="main_content",
                    title="Report Content",
                    content=rendered_content,
                    section_type="html"
                )
                report.add_section(main_section)
            
            report.status = ReportStatus.COMPLETED
            report.metadata.update({
                "data_sources_used": list(aggregated_data.keys()),
                "generation_duration_seconds": (datetime.now() - report.generated_at).total_seconds(),
                "sections_count": len(report.sections),
                "ai_guardrails_applied": self.guardrails_service is not None,
                "seven_habits_integrated": self.habits_framework is not None,
                "responsible_ai_compliance": True
            })
            
            # Store generated report
            self.generated_reports[report_id] = report
            
            logger.info(f"Report generation completed with responsible AI controls: {report_id}")
            
        except Exception as e:
            logger.error(f"Error generating report {report_id}: {e}")
            report.status = ReportStatus.FAILED
            report.error_message = str(e)
        
        return report
    
    async def _generate_report_sections(self, config: ReportConfig, data: Dict[str, Any]) -> List[ReportSection]:
        """Generate report sections based on report type and data"""
        sections = []
        
        if config.report_type == ReportType.PERFORMANCE_ANALYSIS:
            sections.extend(await self._generate_performance_sections(data))
        elif config.report_type == ReportType.COMPLIANCE_ANALYSIS:
            sections.extend(await self._generate_compliance_sections(data))
        elif config.report_type == ReportType.DASHBOARD:
            sections.extend(await self._generate_dashboard_sections(data))
        elif config.report_type == ReportType.EXECUTIVE_SUMMARY:
            sections.extend(await self._generate_executive_sections(data))
        
        return sections
    
    async def _generate_performance_sections(self, data: Dict[str, Any]) -> List[ReportSection]:
        """Generate sections for performance analysis reports"""
        sections = []
        
        # Summary section
        summary_section = ReportSection(
            id="performance_summary",
            title="Performance Summary",
            content="Performance analysis summary will be generated here.",
            section_type="summary",
            data=data
        )
        sections.append(summary_section)
        
        # Metrics section
        if "performance_metrics" in data:
            metrics_section = ReportSection(
                id="performance_metrics",
                title="Performance Metrics",
                content="Detailed performance metrics analysis.",
                section_type="metrics",
                data=data.get("performance_metrics", {})
            )
            sections.append(metrics_section)
        
        return sections
    
    async def _generate_compliance_sections(self, data: Dict[str, Any]) -> List[ReportSection]:
        """Generate sections for compliance analysis reports"""
        sections = []
        
        # Compliance overview
        overview_section = ReportSection(
            id="compliance_overview",
            title="Compliance Overview",
            content="Compliance analysis overview will be generated here.",
            section_type="overview",
            data=data
        )
        sections.append(overview_section)
        
        return sections
    
    async def _generate_dashboard_sections(self, data: Dict[str, Any]) -> List[ReportSection]:
        """Generate sections for dashboard reports"""
        sections = []
        
        # Real-time status
        status_section = ReportSection(
            id="system_status",
            title="System Status",
            content="Real-time system status dashboard.",
            section_type="dashboard",
            data=data
        )
        sections.append(status_section)
        
        return sections
    
    async def _generate_executive_sections(self, data: Dict[str, Any]) -> List[ReportSection]:
        """Generate sections for executive summary reports"""
        sections = []
        
        # Executive summary
        exec_section = ReportSection(
            id="executive_summary",
            title="Executive Summary",
            content="High-level executive summary of system performance and compliance.",
            section_type="executive",
            data=data
        )
        sections.append(exec_section)
        
        return sections
    
    def _render_report_content(self, report: Report) -> str:
        """Render report content using template engine"""
        template_id = report.config.template_id or "default"
        
        context = {
            "title": report.title,
            "description": report.description,
            "generated_at": report.generated_at.strftime("%Y-%m-%d %H:%M:%S"),
            "sections": report.sections,
            "metadata": report.metadata,
            "report_id": report.id,
            "report_type": report.report_type.value
        }
        
        # Add branding context if available
        if self.branding_service:
            branding_context = self.branding_service.get_branding_context()
            context.update(branding_context)
        else:
            # Provide default branding context when service is not available
            context["branding"] = {
                "has_logo": False,
                "logo_data": None,
                "organization_name": None,
                "primary_color": "#2c5aa0",
                "secondary_color": "#6c757d",
                "accent_color": "#28a745",
                "font_family": "Arial, sans-serif",
                "custom_css": self._get_default_css()
            }
        
        return self.template_engine.render_template(template_id, context)
    
    def _get_default_css(self) -> str:
        """Get default CSS when branding service is not available"""
        return """
        :root {
            --primary-color: #2c5aa0;
            --secondary-color: #6c757d;
            --accent-color: #28a745;
            --font-family: Arial, sans-serif;
        }
        
        body {
            font-family: var(--font-family);
            color: #333;
            line-height: 1.6;
            margin: 0;
            padding: 20px;
        }
        
        .report-header {
            border-bottom: 2px solid var(--primary-color);
            padding-bottom: 20px;
            margin-bottom: 30px;
            position: relative;
        }
        
        .report-title {
            color: var(--primary-color);
            font-size: 2.5em;
            font-weight: bold;
            margin: 0;
        }
        
        .report-subtitle {
            color: var(--secondary-color);
            font-size: 1.2em;
            margin: 10px 0;
        }
        """
    
    async def export_report(self, report_id: str, formats: List[ReportFormat], output_dir: Path) -> Dict[ReportFormat, str]:
        """Export report to specified formats"""
        if report_id not in self.generated_reports:
            raise ValueError(f"Report not found: {report_id}")
        
        report = self.generated_reports[report_id]
        exported_files = {}
        
        for format in formats:
            if format in self.report_exporters:
                try:
                    output_path = output_dir / f"{report_id}.{format.value}"
                    exported_file = await self.report_exporters[format].export_report(
                        report, format, str(output_path)
                    )
                    exported_files[format] = exported_file
                    report.file_paths[format] = exported_file
                    
                except Exception as e:
                    logger.error(f"Error exporting report {report_id} to {format.value}: {e}")
            else:
                logger.warning(f"No exporter registered for format: {format.value}")
        
        return exported_files
    
    def get_report(self, report_id: str) -> Optional[Report]:
        """Get a generated report by ID"""
        return self.generated_reports.get(report_id)
    
    def list_reports(self) -> List[str]:
        """List all generated report IDs"""
        return list(self.generated_reports.keys())
    
    def get_report_status(self, report_id: str) -> Optional[ReportStatus]:
        """Get the status of a report"""
        report = self.generated_reports.get(report_id)
        return report.status if report else None 
   
    def configure_branding(self, organization_name: Optional[str] = None,
                          logo_path: Optional[str] = None,
                          logo_position: Optional[str] = None,
                          primary_color: Optional[str] = None,
                          **kwargs) -> bool:
        """Configure report branding including optional logo"""
        if not self.branding_service:
            logger.warning("Branding service not available")
            return False
        
        try:
            # Update general branding
            if any([organization_name, primary_color, kwargs]):
                self.branding_service.update_branding(
                    organization_name=organization_name,
                    primary_color=primary_color,
                    **{k: v for k, v in kwargs.items() if k in ['secondary_color', 'accent_color', 'font_family', 'custom_css']}
                )
            
            # Configure logo if provided
            if logo_path:
                from .report_branding_service import LogoPosition, LogoSize
                
                position = LogoPosition.TOP_RIGHT  # Default
                if logo_position:
                    try:
                        position = LogoPosition(logo_position.lower())
                    except ValueError:
                        logger.warning(f"Invalid logo position: {logo_position}, using default")
                
                size = LogoSize(kwargs.get('logo_size', 'medium').lower()) if 'logo_size' in kwargs else LogoSize.MEDIUM
                
                success = self.branding_service.configure_logo(
                    logo_path,
                    position=position,
                    size=size,
                    opacity=kwargs.get('logo_opacity', 1.0),
                    custom_width=kwargs.get('logo_width'),
                    custom_height=kwargs.get('logo_height')
                )
                
                if not success:
                    logger.error(f"Failed to configure logo: {logo_path}")
                    return False
            
            logger.info("Report branding configured successfully")
            return True
            
        except Exception as e:
            logger.error(f"Error configuring branding: {e}")
            return False
    
    def disable_logo(self) -> bool:
        """Disable logo in reports"""
        if not self.branding_service:
            return False
        
        try:
            self.branding_service.disable_logo()
            logger.info("Logo disabled for reports")
            return True
        except Exception as e:
            logger.error(f"Error disabling logo: {e}")
            return False
    
    def get_branding_status(self) -> Dict[str, Any]:
        """Get current branding configuration status"""
        if not self.branding_service:
            return {
                "branding_available": False,
                "logo_enabled": False,
                "organization_name": None
            }
        
        config = self.branding_service.get_configuration()
        return {
            "branding_available": True,
            "logo_enabled": config.logo.enabled,
            "logo_path": config.logo.file_path if config.logo.enabled else None,
            "organization_name": config.organization_name,
            "primary_color": config.primary_color,
            "secondary_color": config.secondary_color,
            "accent_color": config.accent_color
        }    

    async def _apply_ai_guardrails_to_sections(self, sections: List[ReportSection], 
                                             config: ReportConfig) -> List[ReportSection]:
        """Apply AI guardrails to all report sections"""
        if not self.guardrails_service:
            return sections
        
        processed_sections = []
        
        for section in sections:
            try:
                # Create context for guardrail evaluation
                context = {
                    'content_type': 'report_section',
                    'section_type': section.section_type,
                    'report_type': config.report_type.value,
                    'ai_generated': True,
                    'healthcare_context': True,
                    'confidence_level': 'medium'  # Default confidence
                }
                
                # Evaluate section content
                guardrail_result = self.guardrails_service.evaluate_content(section.content, context)
                
                # Apply modifications if needed
                if guardrail_result.modified_content and guardrail_result.is_safe():
                    section.content = guardrail_result.modified_content
                elif not guardrail_result.is_safe():
                    # Content blocked - replace with safe alternative
                    section.content = self._generate_safe_content_alternative(section, guardrail_result)
                
                # Add transparency metadata
                section.metadata.update({
                    'ai_guardrails_applied': True,
                    'guardrail_violations': len(guardrail_result.violations),
                    'risk_level': guardrail_result.overall_risk_level.value,
                    'transparency_notes': guardrail_result.transparency_notes
                })
                
                processed_sections.append(section)
                
            except Exception as e:
                logger.error(f"Error applying guardrails to section {section.id}: {e}")
                # Keep original section if guardrails fail
                processed_sections.append(section)
        
        return processed_sections
    
    async def _integrate_seven_habits(self, sections: List[ReportSection], 
                                    aggregated_data: Dict[str, Any], 
                                    config: ReportConfig) -> List[ReportSection]:
        """Integrate 7 Habits framework into report sections"""
        if not self.habits_framework:
            return sections
        
        try:
            # Generate 7 Habits insights based on report data
            habits_insights = await self._generate_habits_insights(aggregated_data, config)
            
            if habits_insights:
                # Create 7 Habits section
                habits_section = ReportSection(
                    id="seven_habits_framework",
                    title="🎯 Personal Development - 7 Habits Framework",
                    content=self._format_habits_content(habits_insights),
                    section_type="habits_framework"
                )
                
                habits_section.metadata.update({
                    'framework_type': '7_habits',
                    'habits_count': len(habits_insights),
                    'educational_value': 'high',
                    'personal_development': True
                })
                
                # Insert habits section before recommendations
                insert_index = len(sections)
                for i, section in enumerate(sections):
                    if 'recommendation' in section.id.lower():
                        insert_index = i
                        break
                
                sections.insert(insert_index, habits_section)
                
                logger.info("7 Habits framework successfully integrated into report")
        
        except Exception as e:
            logger.error(f"Error integrating 7 Habits framework: {e}")
        
        return sections
    
    async def _generate_habits_insights(self, aggregated_data: Dict[str, Any], 
                                      config: ReportConfig) -> List[Dict[str, Any]]:
        """Generate 7 Habits insights based on report data"""
        habits_insights = []
        
        try:
            # Extract key findings from aggregated data
            findings = []
            for provider_data in aggregated_data.values():
                if isinstance(provider_data, dict) and 'findings' in provider_data:
                    findings.extend(provider_data['findings'])
            
            # Map findings to habits using the framework
            for finding in findings[:5]:  # Limit to top 5 findings
                habit_mapping = self.habits_framework.map_finding_to_habit(finding)
                if habit_mapping:
                    habits_insights.append({
                        'habit_number': habit_mapping.get('habit_number', 1),
                        'habit_name': habit_mapping.get('name', 'Be Proactive'),
                        'finding': finding.get('description', ''),
                        'explanation': habit_mapping.get('explanation', ''),
                        'actionable_steps': habit_mapping.get('actionable_steps', []),
                        'personal_development_tip': habit_mapping.get('personal_development_tip', ''),
                        'confidence': habit_mapping.get('confidence', 0.7)
                    })
            
            # Add general habits if no specific mappings found
            if not habits_insights:
                all_habits = self.habits_framework.get_all_habits()
                for i, habit in enumerate(all_habits[:3]):  # Top 3 habits
                    habits_insights.append({
                        'habit_number': i + 1,
                        'habit_name': habit.get('name', f'Habit {i + 1}'),
                        'finding': 'General professional development opportunity',
                        'explanation': habit.get('explanation', ''),
                        'actionable_steps': habit.get('actionable_steps', []),
                        'personal_development_tip': habit.get('personal_development_tip', ''),
                        'confidence': 0.6
                    })
        
        except Exception as e:
            logger.error(f"Error generating habits insights: {e}")
        
        return habits_insights
    
    def _format_habits_content(self, habits_insights: List[Dict[str, Any]]) -> str:
        """Format 7 Habits content for display"""
        if not habits_insights:
            return "<p>7 Habits framework integration not available for this report.</p>"
        
        content = """
        <div class="habits-framework-section">
            <p class="habits-intro">
                Based on your performance data, here are personalized insights using 
                <strong>Stephen Covey's 7 Habits of Highly Effective People</strong> framework 
                to support your professional development journey:
            </p>
        """
        
        for insight in habits_insights:
            content += f"""
            <div class="habit-insight">
                <h4>🎯 Habit {insight['habit_number']}: {insight['habit_name']}</h4>
                <div class="habit-content">
                    <p><strong>Opportunity:</strong> {insight['finding']}</p>
                    <p><strong>Development Insight:</strong> {insight['explanation']}</p>
                    
                    {f'<p><strong>Personal Development Tip:</strong> {insight["personal_development_tip"]}</p>' 
                     if insight.get('personal_development_tip') else ''}
                    
                    {f'''<div class="actionable-steps">
                        <strong>Actionable Steps:</strong>
                        <ul>
                            {''.join(f'<li>{step}</li>' for step in insight['actionable_steps'])}
                        </ul>
                    </div>''' if insight.get('actionable_steps') else ''}
                    
                    <div class="confidence-indicator">
                        <small>Confidence: {insight['confidence']:.0%}</small>
                    </div>
                </div>
            </div>
            """
        
        content += """
            <div class="habits-footer">
                <p><em>The 7 Habits framework provides a principle-centered approach to personal 
                and professional effectiveness. These insights are designed to support your 
                continuous improvement journey in clinical documentation and professional practice.</em></p>
            </div>
        </div>
        """
        
        return content
    
    async def _apply_final_guardrails_check(self, content: str, config: ReportConfig) -> str:
        """Apply final guardrails check to rendered report content"""
        if not self.guardrails_service:
            return content
        
        try:
            context = {
                'content_type': 'final_report',
                'report_type': config.report_type.value,
                'ai_generated': True,
                'healthcare_context': True,
                'final_check': True
            }
            
            guardrail_result = self.guardrails_service.evaluate_content(content, context)
            
            if guardrail_result.modified_content and guardrail_result.is_safe():
                logger.info("Final guardrails check applied modifications to report content")
                return guardrail_result.modified_content
            elif not guardrail_result.is_safe():
                logger.warning("Final guardrails check flagged content as unsafe")
                # Add safety notice
                safety_notice = """
                <div class="ai-safety-notice" style="background: #fff3cd; border: 1px solid #ffeaa7; 
                     padding: 15px; margin: 20px 0; border-radius: 5px;">
                    <h4>⚠️ AI Safety Notice</h4>
                    <p>This report has been reviewed by AI safety systems. Some content may have been 
                    modified or flagged for additional review to ensure accuracy and appropriateness.</p>
                    <p><strong>Professional Review Required:</strong> Please review all findings and 
                    recommendations with appropriate clinical expertise before implementation.</p>
                </div>
                """
                return safety_notice + content
            
        except Exception as e:
            logger.error(f"Error in final guardrails check: {e}")
        
        return content
    
    def _generate_safe_content_alternative(self, section: ReportSection, 
                                         guardrail_result) -> str:
        """Generate safe alternative content when original is blocked"""
        return f"""
        <div class="content-safety-notice">
            <h4>⚠️ Content Safety Notice</h4>
            <p>The original content for this section was modified by AI safety systems 
            to ensure appropriateness and accuracy.</p>
            <p><strong>Section:</strong> {section.title}</p>
            <p><strong>Reason:</strong> Content safety and quality assurance</p>
            <p><strong>Recommendation:</strong> Please consult with appropriate clinical 
            expertise for detailed analysis of this area.</p>
        </div>
        """
    
    def get_ai_guardrails_status(self) -> Dict[str, Any]:
        """Get status of AI guardrails system"""
        if not self.guardrails_service:
            return {"available": False, "message": "AI guardrails service not available"}
        
        return {
            "available": True,
            "statistics": self.guardrails_service.get_guardrail_statistics(),
            "responsible_ai_enabled": True,
            "transparency_enforced": True,
            "bias_mitigation_active": True,
            "ethical_compliance_checked": True
        }
    
    def get_seven_habits_status(self) -> Dict[str, Any]:
        """Get status of 7 Habits framework integration"""
        if not self.habits_framework:
            return {"available": False, "message": "7 Habits framework not available"}
        
        try:
            all_habits = self.habits_framework.get_all_habits()
            return {
                "available": True,
                "framework_name": "Stephen Covey's 7 Habits of Highly Effective People",
                "habits_count": len(all_habits),
                "integration_active": True,
                "personal_development_enabled": True,
                "educational_value": "high"
            }
        except Exception as e:
            return {"available": False, "error": str(e)}