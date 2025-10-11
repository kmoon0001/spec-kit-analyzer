"""Report Configuration Manager

This module handles report configurations, settings, and default configurations.
Separated from the main engine for better maintainability and testing.
"""

import logging
from pathlib import Path

import yaml

from .report_models import ReportConfig, ReportFormat, ReportType, TimeRange

logger = logging.getLogger(__name__)


class ReportConfigurationManager:
    """Manages report configurations and settings"""

    def __init__(self, config_dir: Path | None = None):
        self.config_dir = config_dir or Path("config/reports")
        self.configurations: dict[str, ReportConfig] = {}
        self.default_configs: dict[ReportType, ReportConfig] = {}
        self._load_configurations()

    def _load_configurations(self) -> None:
        """Load report configurations from files"""
        if not self.config_dir.exists():
            logger.info("Config directory not found: %s, creating defaults", self.config_dir)
            self.config_dir.mkdir(parents=True, exist_ok=True)
            self._create_default_configurations()
            return

        try:
            for config_file in self.config_dir.glob("*.yaml"):
                config_id = config_file.stem
                with open(config_file, encoding="utf-8") as f:
                    config_data = yaml.safe_load(f)
                    self.configurations[config_id] = self._dict_to_config(config_data)
                logger.debug("Loaded configuration: %s", config_id)
        except (FileNotFoundError, PermissionError, OSError) as e:
            logger.exception("Error loading configurations: %s", e)
            self._create_default_configurations()

    def _create_default_configurations(self) -> None:
        """Create default report configurations"""
        default_configs = {
            ReportType.PERFORMANCE_ANALYSIS: ReportConfig(
                report_type=ReportType.PERFORMANCE_ANALYSIS,
                title="Performance Analysis Report",
                description="Comprehensive analysis of system performance metrics",
                time_range=TimeRange.last_days(7),
                export_formats=[ReportFormat.HTML, ReportFormat.PDF],
            ),
            ReportType.COMPLIANCE_ANALYSIS: ReportConfig(
                report_type=ReportType.COMPLIANCE_ANALYSIS,
                title="Compliance Analysis Report",
                description="Analysis of compliance with regulatory requirements",
                time_range=TimeRange.last_days(30),
                export_formats=[ReportFormat.HTML, ReportFormat.PDF],
            ),
            ReportType.DASHBOARD: ReportConfig(
                report_type=ReportType.DASHBOARD,
                title="Dashboard Report",
                description="Executive dashboard with key metrics",
                export_formats=[ReportFormat.HTML],
            ),
        }

        self.default_configs = default_configs

        # Save default configurations to files
        for report_type, config in default_configs.items():
            config_file = self.config_dir / f"default_{report_type.value}.yaml"
            config_dict = self._config_to_dict(config)
            with open(config_file, "w", encoding="utf-8") as f:
                yaml.dump(config_dict, f, default_flow_style=False)
            self.configurations[f"default_{report_type.value}"] = config

        logger.info("Created default report configurations")

    def _dict_to_config(self, config_data: dict[str, any]) -> ReportConfig:
        """Convert dictionary to ReportConfig"""
        time_range = None
        if "time_range" in config_data and config_data["time_range"]:
            tr_data = config_data["time_range"]
            if "last_days" in tr_data:
                time_range = TimeRange.last_days(tr_data["last_days"])
            elif "last_hours" in tr_data:
                time_range = TimeRange.last_hours(tr_data["last_hours"])

        export_formats = [ReportFormat(fmt) for fmt in config_data.get("export_formats", ["html"])]

        return ReportConfig(
            report_type=ReportType(config_data["report_type"]),
            title=config_data["title"],
            description=config_data.get("description", ""),
            time_range=time_range,
            template_id=config_data.get("template_id"),
            export_formats=export_formats,
            filters=config_data.get("filters", {}),
            metadata=config_data.get("metadata", {}),
        )

    def _config_to_dict(self, config: ReportConfig) -> dict[str, any]:
        """Convert ReportConfig to dictionary"""
        config_dict = {
            "report_type": config.report_type.value,
            "title": config.title,
            "description": config.description,
            "template_id": config.template_id,
            "export_formats": [fmt.value for fmt in config.export_formats],
            "filters": config.filters,
            "metadata": config.metadata,
        }

        if config.time_range:
            # For simplicity, store as relative time ranges
            now = config.time_range.end_time
            hours_diff = (now - config.time_range.start_time).total_seconds() / 3600
            if hours_diff <= 24:
                config_dict["time_range"] = {"last_hours": int(hours_diff)}
            else:
                config_dict["time_range"] = {"last_days": int(hours_diff / 24)}

        return config_dict

    def get_configuration(self, config_id: str) -> ReportConfig | None:
        """Get a report configuration by ID"""
        return self.configurations.get(config_id)

    def get_default_configuration(self, report_type: ReportType) -> ReportConfig:
        """Get default configuration for a report type"""
        return self.default_configs.get(report_type, self.default_configs[ReportType.PERFORMANCE_ANALYSIS])

    def save_configuration(self, config_id: str, config: ReportConfig) -> None:
        """Save a report configuration"""
        self.configurations[config_id] = config

        # Save to file
        config_file = self.config_dir / f"{config_id}.yaml"
        config_dict = self._config_to_dict(config)
        try:
            with open(config_file, "w", encoding="utf-8") as f:
                yaml.dump(config_dict, f, default_flow_style=False)
            logger.info("Saved configuration: %s", config_id)
        except (FileNotFoundError, PermissionError, OSError):
            logger.exception("Error saving configuration %s: {e}", config_id)

    def delete_configuration(self, config_id: str) -> bool:
        """Delete a report configuration"""
        if config_id in self.configurations:
            del self.configurations[config_id]

            # Delete file
            config_file = self.config_dir / f"{config_id}.yaml"
            try:
                if config_file.exists():
                    config_file.unlink()
                logger.info("Deleted configuration: %s", config_id)
                return True
            except (FileNotFoundError, PermissionError, OSError):
                logger.exception("Error deleting configuration file %s: {e}", config_id)
        return False

    def list_configurations(self) -> dict[str, str]:
        """List all available configurations with their titles"""
        return {config_id: config.title for config_id, config in self.configurations.items()}

    def reload_configurations(self) -> None:
        """Reload all configurations from disk"""
        self.configurations.clear()
        self.default_configs.clear()
        self._load_configurations()
        logger.info("Reloaded all configurations")
