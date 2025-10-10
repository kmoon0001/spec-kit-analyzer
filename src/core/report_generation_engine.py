"""Report Generation Engine - Refactored Main Engine

This is the simplified main engine that coordinates the separated components.
All functionality is preserved while improving maintainability.
"""

import logging
from datetime import datetime
from typing import Any

from .report_config_manager import ReportConfigurationManager
from .report_data_service import DataAggregationService
from .report_models import Report, ReportConfig, ReportExporter, ReportFormat, ReportSection, ReportStatus
from .report_template_engine import TemplateEngine

logger = logging.getLogger(__name__)


class ReportGenerationEngine:
    """Main engine for generating reports - refactored for maintainability"""

    def __init__(self):
        # Core services
        self.data_aggregation_service = DataAggregationService()
        self.template_engine = TemplateEngine()
        self.config_manager = ReportConfigurationManager()

        # Report management
        self.report_exporters: dict[ReportFormat, ReportExporter] = {}
        self.generated_reports: dict[str, Report] = {}
        self.report_counter = 0

        # Optional services (preserve existing functionality)
        self._initialize_optional_services()

    def _initialize_optional_services(self) -> None:
        """Initialize optional services without breaking if they're not available"""
        # Initialize branding service for optional logo support
        try:
            from .report_branding_service import ReportBrandingService
            self.branding_service = ReportBrandingService()
            logger.info("Branding service initialized")
        except ImportError:
            logger.debug("Branding service not available, reports will use default styling")
            self.branding_service = None

        # Initialize AI guardrails service for responsible AI
        try:
            from .ai_guardrails_service import AIGuardrailsService
            self.guardrails_service = AIGuardrailsService()
            logger.info("AI guardrails service initialized")
        except ImportError:
            logger.debug("AI guardrails service not available")
            self.guardrails_service = None

        # Initialize 7 Habits framework integration
        try:
            from .enhanced_habit_mapper import SevenHabitsFramework
            self.habits_framework = SevenHabitsFramework()
            logger.info("7 Habits framework integration initialized")
        except ImportError:
            logger.debug("7 Habits framework not available")
            self.habits_framework = None

        # Initialize data integration service
        try:
            from .data_integration_service import DataIntegrationService
            self.data_integration_service = DataIntegrationService()
            logger.info("Data integration service initialized")
        except ImportError:
            logger.debug("Data integration service not available")
            self.data_integration_service = None

    def register_data_provider(self, name: str, provider) -> None:
        """Register a data provider (preserves existing functionality)"""
        self.data_aggregation_service.register_data_provider(name, provider)

        # Also register with data integration service if available
        if hasattr(self, "data_integration_service") and self.data_integration_service:
            try:
                if hasattr(provider, "provider_id"):
                    self.data_integration_service.register_provider(provider)
            except (ImportError, ModuleNotFoundError, AttributeError) as e:
                logger.warning("Could not register provider with data integration service: %s", e)

    def register_report_exporter(self, format: ReportFormat, exporter: ReportExporter) -> None:
        """Register a report exporter"""
        self.report_exporters[format] = exporter
        logger.info("Registered report exporter for format: %s", format.value)

    async def generate_report(self, config: ReportConfig) -> Report:
        """Generate a report based on configuration (preserves all existing functionality)"""
        # Create report instance
        self.report_counter += 1
        report_id = f"report_{self.report_counter}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

        report = Report(
            id=report_id,
            config=config,
            status=ReportStatus.GENERATING,
            created_at=datetime.now(),
            updated_at=datetime.now(),
        )

        self.generated_reports[report_id] = report

        try:
            # Get data from providers
            aggregated_data = self.data_aggregation_service.get_aggregated_data(
                config.report_type, config.filters,
            )

            # Generate report sections
            sections = await self._generate_report_sections(config, aggregated_data)

            # Apply AI guardrails if available
            if self.guardrails_service:
                sections = await self._apply_ai_guardrails(sections)

            # Add 7 Habits insights if available
            if self.habits_framework:
                habits_section = await self._generate_habits_insights(config, aggregated_data)
                if habits_section:
                    sections.append(habits_section)

            # Add sections to report
            for section in sections:
                report.add_section(section)

            # Update report status
            report.status = ReportStatus.COMPLETED
            report.updated_at = datetime.now()

            logger.info("Successfully generated report: %s", report_id)

        except Exception as e:
            logger.exception("Error generating report %s: {e}", report_id)
            report.status = ReportStatus.FAILED
            report.error_message = str(e)
            report.updated_at = datetime.now()

        return report

    async def _generate_report_sections(self, config: ReportConfig, data: dict[str, Any]) -> list[ReportSection]:
        """Generate report sections based on configuration and data"""
        sections = []

        # Executive summary section
        summary_section = ReportSection(
            id="executive_summary",
            title="Executive Summary",
            content=self._generate_executive_summary(config, data),
        )
        sections.append(summary_section)

        # Data analysis sections
        for provider_name, provider_data in data.items():
            if isinstance(provider_data, dict) and "error" not in provider_data:
                section = ReportSection(
                    id=f"analysis_{provider_name}",
                    title=f"{provider_name.replace('_', ' ').title()} Analysis",
                    content=self._format_provider_data(provider_data),
                    data=provider_data,
                )
                sections.append(section)

        return sections

    def _generate_executive_summary(self, config: ReportConfig, data: dict[str, Any]) -> str:
        """Generate executive summary content"""
        summary = f"""
        <h3>Report Overview</h3>
        <p><strong>Report Type:</strong> {config.report_type.value.replace('_', ' ').title()}</p>
        <p><strong>Generated:</strong> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
        <p><strong>Data Sources:</strong> {len(data)} providers</p>

        <h3>Key Findings</h3>
        <ul>
        """

        # Add key findings from data
        for provider_name, provider_data in data.items():
            if isinstance(provider_data, dict) and "error" not in provider_data:
                summary += f"<li>Data from {provider_name.replace('_', ' ').title()}: {len(provider_data)} items</li>"

        summary += "</ul>"
        return summary

    def _format_provider_data(self, data: dict[str, Any]) -> str:
        """Format provider data for display"""
        if not data:
            return "<p>No data available</p>"

        content = "<div class='data-section'>"

        # Create a simple table for data display
        if isinstance(data, dict):
            content += "<table class='data-table'>"
            content += "<thead><tr><th>Metric</th><th>Value</th></tr></thead><tbody>"

            for key, value in data.items():
                content += f"<tr><td>{key.replace('_', ' ').title()}</td><td>{value}</td></tr>"

            content += "</tbody></table>"

        content += "</div>"
        return content

    async def _apply_ai_guardrails(self, sections: list[ReportSection]) -> list[ReportSection]:
        """Apply AI guardrails to report sections"""
        if not self.guardrails_service:
            return sections

        filtered_sections = []
        for section in sections:
            try:
                # Check content with guardrails
                guardrail_result = await self.guardrails_service.check_content(section.content)

                if guardrail_result.get("approved", True):
                    filtered_sections.append(section)
                else:
                    # Generate safe alternative content
                    safe_content = self._generate_safe_content_alternative(section, guardrail_result)
                    section.content = safe_content
                    filtered_sections.append(section)

            except (requests.RequestException, ConnectionError, TimeoutError, HTTPError) as e:
                logger.warning("Error applying guardrails to section %s: {e}", section.id)
                filtered_sections.append(section)  # Include original on error

        return filtered_sections

    async def _generate_habits_insights(self, config: ReportConfig, data: dict[str, Any]) -> ReportSection | None:
        """Generate 7 Habits insights section"""
        if not self.habits_framework:
            return None

        try:
            habits_insights = await self.habits_framework.generate_insights(config.report_type, data)

            if habits_insights:
                content = self._format_habits_content(habits_insights)
                return ReportSection(
                    id="seven_habits_insights",
                    title="7 Habits Framework Insights",
                    content=content,
                    data={"habits_insights": habits_insights},
                )
        except Exception as e:
            logger.warning("Error generating 7 Habits insights: %s", e)

        return None

    def _format_habits_content(self, habits_insights: list[dict[str, Any]]) -> str:
        """Format 7 Habits content for display"""
        if not habits_insights:
            return "<p>No habits insights available</p>"

        content = "<div class='habits-section'>"
        content += "<p>Based on the 7 Habits of Highly Effective People framework:</p>"

        for insight in habits_insights:
            habit_name = insight.get("habit", "Unknown Habit")
            recommendation = insight.get("recommendation", "No recommendation available")

            content += f"""
            <div class='habit-insight'>
                <h4>{habit_name}</h4>
                <p>{recommendation}</p>
            </div>
            """

        content += "</div>"
        return content

    def _generate_safe_content_alternative(self, section: ReportSection, guardrail_result) -> str:
        """Generate safe alternative content when original is blocked"""
        return f"""
        <div class='safe-content-notice'>
            <h4>Content Review Notice</h4>
            <p>The original content for this section has been reviewed and replaced with this summary for compliance reasons.</p>
            <p><strong>Section:</strong> {section.title}</p>
            <p><strong>Reason:</strong> {guardrail_result.get('reason', 'Content policy compliance')}</p>
        </div>
        """

    def render_report_html(self, report: Report) -> str:
        """Render report as HTML using template engine"""
        context = {
            "title": report.config.title,
            "description": report.config.description,
            "generated_at": report.created_at.strftime("%Y-%m-%d %H:%M:%S"),
            "sections": [
                {
                    "title": section.title,
                    "content": section.content,
                }
                for section in report.sections
            ],
        }

        # Add branding if available
        if self.branding_service:
            branding_context = self.branding_service.get_branding_context()
            context.update(branding_context)

        template_id = report.config.template_id or "default"
        return self.template_engine.render_template(template_id, context)

    async def export_report(self, report_id: str, formats: list[ReportFormat]) -> dict[ReportFormat, str]:
        """Export report in specified formats"""
        report = self.generated_reports.get(report_id)
        if not report:
            raise ValueError(f"Report not found: {report_id}")

        exported_files = {}

        for format in formats:
            if format in self.report_exporters:
                try:
                    output_path = f"reports/{report_id}.{format.value}"
                    success = self.report_exporters[format].export_report(report, format, output_path)
                    if success:
                        exported_files[format] = output_path
                        report.file_paths[format] = output_path
                except (FileNotFoundError, PermissionError, OSError, IOError) as e:
                    logger.exception("Error exporting report %s to {format.value}: {e}", report_id)
            else:
                logger.warning("No exporter registered for format: %s", format.value)

        return exported_files

    def get_report(self, report_id: str) -> Report | None:
        """Get a generated report by ID"""
        return self.generated_reports.get(report_id)

    def list_reports(self) -> list[str]:
        """List all generated report IDs"""
        return list(self.generated_reports.keys())

    def get_report_status(self, report_id: str) -> ReportStatus | None:
        """Get the status of a report"""
        report = self.generated_reports.get(report_id)
        return report.status if report else None

    # Preserve all existing branding methods
    def configure_branding(self, organization_name: str | None = None,
                          logo_path: str | None = None,
                          logo_position: str | None = None,
                          primary_color: str | None = None,
                          secondary_color: str | None = None) -> bool:
        """Configure branding for reports (preserves existing functionality)"""
        if not self.branding_service:
            logger.warning("Branding service not available")
            return False

        try:
            return self.branding_service.configure_branding(
                organization_name=organization_name,
                logo_path=logo_path,
                logo_position=logo_position,
                primary_color=primary_color,
                secondary_color=secondary_color,
            )
        except (FileNotFoundError, PermissionError, OSError, IOError) as e:
            logger.exception("Error configuring branding: %s", e)
            return False

    def disable_logo(self) -> bool:
        """Disable logo in reports"""
        if not self.branding_service:
            return False

        try:
            return self.branding_service.disable_logo()
        except Exception as e:
            logger.exception("Error disabling logo: %s", e)
            return False

    def get_branding_status(self) -> dict[str, Any]:
        """Get current branding configuration status"""
        if not self.branding_service:
            return {"status": "unavailable", "message": "Branding service not initialized"}

        try:
            return self.branding_service.get_status()
        except Exception as e:
            return {"status": "error", "message": str(e)}

    def get_ai_guardrails_status(self) -> dict[str, Any]:
        """Get status of AI guardrails system"""
        if not self.guardrails_service:
            return {"status": "unavailable", "message": "AI guardrails service not initialized"}

        try:
            return self.guardrails_service.get_status()
        except Exception as e:
            return {"status": "error", "message": str(e)}

    def get_seven_habits_status(self) -> dict[str, Any]:
        """Get status of 7 Habits framework integration"""
        if not self.habits_framework:
            return {"status": "unavailable", "message": "7 Habits framework not initialized"}

        try:
            return self.habits_framework.get_status()
        except Exception as e:
            return {"status": "error", "message": str(e)}
