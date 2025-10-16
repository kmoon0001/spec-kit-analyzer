"""Advanced Template System - Professional report template management

This module provides a comprehensive template system with advanced rendering,
component libraries, validation, and version management for professional reports.
"""

import json
import logging
import re
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any

import yaml
from jinja2.exceptions import TemplateError

logger = logging.getLogger(__name__)


class TemplateType(Enum):
    """Types of report templates"""

    PERFORMANCE_ANALYSIS = "performance_analysis"
    COMPLIANCE_ANALYSIS = "compliance_analysis"
    DASHBOARD = "dashboard"
    EXECUTIVE_SUMMARY = "executive_summary"
    TREND_ANALYSIS = "trend_analysis"
    COMPARISON = "comparison"
    CUSTOM = "custom"


class ComponentType(Enum):
    """Types of template components"""

    CHART = "chart"
    TABLE = "table"
    METRIC_CARD = "metric_card"
    ALERT_PANEL = "alert_panel"
    TREND_INDICATOR = "trend_indicator"
    PROGRESS_BAR = "progress_bar"
    TEXT_BLOCK = "text_block"
    IMAGE = "image"
    CUSTOM = "custom"


class RenderFormat(Enum):
    """Supported rendering formats"""

    HTML = "html"
    PDF = "pdf"
    MARKDOWN = "markdown"
    PLAIN_TEXT = "plain_text"


@dataclass
class ComponentDefinition:
    """Definition of a reusable template component"""

    id: str
    name: str
    component_type: ComponentType
    template_content: str
    required_props: list[str] = field(default_factory=list)
    default_props: dict[str, Any] = field(default_factory=dict)
    css_classes: list[str] = field(default_factory=list)
    javascript_code: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)
    MARKDOWN = "markdown"
    PLAIN_TEXT = "plain_text"


@dataclass
class TemplateMetadata:
    """Metadata for template management"""

    template_id: str
    name: str
    description: str
    template_type: TemplateType
    version: str
    author: str
    created_at: datetime
    updated_at: datetime
    supported_formats: list[RenderFormat] = field(default_factory=list)
    required_data_fields: list[str] = field(default_factory=list)
    optional_data_fields: list[str] = field(default_factory=list)
    tags: list[str] = field(default_factory=list)
    compatibility_version: str = "1.0"

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for serialization"""
        return {
            "template_id": self.template_id,
            "name": self.name,
            "description": self.description,
            "template_type": self.template_type.value,
            "version": self.version,
            "author": self.author,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "supported_formats": [fmt.value for fmt in self.supported_formats],
            "required_data_fields": self.required_data_fields,
            "optional_data_fields": self.optional_data_fields,
            "tags": self.tags,
            "compatibility_version": self.compatibility_version,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "TemplateMetadata":
        """Create from dictionary"""
        return cls(
            template_id=data["template_id"],
            name=data["name"],
            description=data["description"],
            template_type=TemplateType(data["template_type"]),
            version=data["version"],
            author=data["author"],
            created_at=datetime.fromisoformat(data["created_at"]),
            updated_at=datetime.fromisoformat(data["updated_at"]),
            supported_formats=[RenderFormat(fmt) for fmt in data.get("supported_formats", [])],
            required_data_fields=data.get("required_data_fields", []),
            optional_data_fields=data.get("optional_data_fields", []),
            tags=data.get("tags", []),
            compatibility_version=data.get("compatibility_version", "1.0"),
        )


class ComponentLibrary:
    """Library of reusable report components"""

    def __init__(self, components_dir: Path | None = None):
        self.components_dir = components_dir or Path("src/resources/report_components")
        self.components: dict[str, ComponentDefinition] = {}
        self.validator = TemplateValidator()
        self._load_components()

    def _load_components(self) -> None:
        """Load components from the components directory"""
        if not self.components_dir.exists():
            self.components_dir.mkdir(parents=True, exist_ok=True)
            self._create_default_components()
            return

        try:
            for component_file in self.components_dir.glob("*.yaml"):
                component_id = component_file.stem
                with open(component_file, encoding="utf-8") as f:
                    component_data = yaml.safe_load(f)

                component = self._dict_to_component(component_data)

                # Validate component
                issues = self.validator.validate_component(component)
                if issues:
                    logger.warning("Component %s has validation issues: {issues}", component_id)

                self.components[component_id] = component
                logger.debug("Loaded component: %s", component_id)

            logger.info("Loaded %s report components", len(self.components))

        except (FileNotFoundError, PermissionError, OSError) as e:
            logger.exception("Error loading components: %s", e)
            self._create_default_components()

    def _create_default_components(self) -> None:
        """Create default components"""
        default_components = {
            "metric_card": ComponentDefinition(
                id="metric_card",
                name="Metric Card",
                component_type=ComponentType.METRIC_CARD,
                template_content="""
                <div class="metric-card {{ css_class }}">
                    <div class="metric-header">
                        <h3>{{ title }}</h3>
                        {% if trend %}
                        <span class="trend {{ trend.direction }}">
                            {{ trend.value }}{{ trend.unit }}
                        </span>
                        {% endif %}
                    </div>
                    <div class="metric-value">
                        <span class="value">{{ value }}</span>
                        <span class="unit">{{ unit }}</span>
                    </div>
                    {% if description %}
                    <div class="metric-description">{{ description }}</div>
                    {% endif %}
                </div>
                """.strip(),
                required_props=["title", "value"],
                default_props={"unit": "", "css_class": ""},
                css_classes=["metric-card", "card"],
            ),
            "progress_bar": ComponentDefinition(
                id="progress_bar",
                name="Progress Bar",
                component_type=ComponentType.PROGRESS_BAR,
                template_content="""
                <div class="progress-container">
                    {% if label %}
                    <div class="progress-label">{{ label }}</div>
                    {% endif %}
                    <div class="progress-bar">
                        <div class="progress-fill" style="width: {{ percentage }}%">
                            {% if show_percentage %}
                            <span class="progress-text">{{ percentage }}%</span>
                            {% endif %}
                        </div>
                    </div>
                    {% if description %}
                    <div class="progress-description">{{ description }}</div>
                    {% endif %}
                </div>
                """.strip(),
                required_props=["percentage"],
                default_props={"show_percentage": True},
                css_classes=["progress-container"],
            ),
        }

        # Save default components
        for comp_id, component in default_components.items():
            self.components[comp_id] = component
            self._save_component(comp_id, component)

        logger.info("Created default report components")

    def _dict_to_component(self, data: dict[str, Any]) -> ComponentDefinition:
        """Convert dictionary to ComponentDefinition"""
        return ComponentDefinition(
            id=data["id"],
            name=data["name"],
            component_type=ComponentType(data["component_type"]),
            template_content=data["template_content"],
            required_props=data.get("required_props", []),
            default_props=data.get("default_props", {}),
            css_classes=data.get("css_classes", []),
            javascript_code=data.get("javascript_code"),
            metadata=data.get("metadata", {}),
        )

    def _save_component(self, comp_id: str, component: ComponentDefinition) -> None:
        """Save component to file"""
        component_file = self.components_dir / f"{comp_id}.yaml"
        component_dict = {
            "id": component.id,
            "name": component.name,
            "component_type": component.component_type.value,
            "template_content": component.template_content,
            "required_props": component.required_props,
            "default_props": component.default_props,
            "css_classes": component.css_classes,
            "javascript_code": component.javascript_code,
            "metadata": component.metadata,
        }
        with open(component_file, "w", encoding="utf-8") as f:
            yaml.dump(component_dict, f, default_flow_style=False)

    def get_component(self, component_id: str) -> ComponentDefinition | None:
        """Get a component by ID"""
        return self.components.get(component_id)

    def list_components(self, component_type: ComponentType | None = None) -> list[str]:
        """List available components, optionally filtered by type"""
        if component_type:
            return [comp_id for comp_id, comp in self.components.items() if comp.component_type == component_type]
        return list(self.components.keys())

    def register_component(self, component: ComponentDefinition) -> None:
        """Register a new component"""
        # Validate component
        issues = self.validator.validate_component(component)
        if issues:
            raise ValueError(f"Component validation failed: {issues}")

        self.components[component.id] = component
        self._save_component(component.id, component)
        logger.info("Registered component: %s", component.id)

    def render_component(self, component_id: str, props: dict[str, Any]) -> str:
        """Render a component with given props"""
        component = self.get_component(component_id)
        if not component:
            raise ValueError(f"Component not found: {component_id}")

        # Merge default props with provided props
        render_props = {**component.default_props, **props}

        # Check required props
        missing_props = set(component.required_props) - set(render_props.keys())
        if missing_props:
            raise ValueError(f"Missing required props for component {component_id}: {missing_props}")

        # Simple template rendering (basic variable substitution)
        try:
            rendered = component.template_content
            for key, value in render_props.items():
                placeholder = f"{{{{ {key} }}}}"
                rendered = rendered.replace(placeholder, str(value))

            return rendered
        except Exception:
            logger.exception("Error rendering component %s: {e}", component_id)
            return f"<div class='component-error'>Error rendering component: {component_id}</div>"


class TemplateValidator:
    """Validates template content and structure"""

    def __init__(self) -> None:
        self.validation_rules: dict[str, Any] = {
            "max_template_size": 1024 * 1024,  # 1MB
            "forbidden_tags": ["script", "iframe", "object", "embed"],
        }

    def validate_template(self, template_content: str, metadata: TemplateMetadata) -> list[str]:
        """Validate template content and return list of issues"""
        issues = []

        # Check template size
        if len(template_content) > self.validation_rules["max_template_size"]:
            issues.append("Template exceeds maximum size limit")

        # Check for forbidden tags
        for tag in self.validation_rules["forbidden_tags"]:
            if f"<{tag}" in template_content.lower():
                issues.append(f"Forbidden tag found: {tag}")

        # Check required data availability
        template_vars = self._extract_template_variables(template_content)
        missing_required = set(metadata.required_data_fields) - set(template_vars)
        if missing_required:
            issues.append(f"Required data not used in template: {missing_required}")

        return issues

    def _extract_template_variables(self, template_content: str) -> list[str]:
        """Extract variable names from template content"""
        # Simple regex to find template variables
        pattern = r"\{\{\s*([a-zA-Z_][a-zA-Z0-9_\.]*)\s*\}\}"
        matches = re.findall(pattern, template_content)
        return [match.split(".")[0] for match in matches]

    def validate_component(self, component: ComponentDefinition) -> list[str]:
        """Validate component definition"""
        issues = []

        # Validate template content
        template_metadata = TemplateMetadata(
            template_id=component.id,
            name=component.name,
            description="Component template",
            template_type=TemplateType.CUSTOM,
            version="1.0",
            author="system",
            created_at=datetime.now(),
            updated_at=datetime.now(),
            required_data_fields=component.required_props,
        )

        template_issues = self.validate_template(component.template_content, template_metadata)
        issues.extend(template_issues)

        # Check required props are defined
        if not component.required_props:
            issues.append("Component should define required props")

        return issues


class AdvancedTemplateRenderer:
    """Advanced template renderer with Jinja2 support"""

    def __init__(self, component_library: ComponentLibrary):
        from jinja2 import Environment, FileSystemLoader, select_autoescape

        self.component_library = component_library
        self.validator = TemplateValidator()
        self.jinja_env = Environment(
            loader=FileSystemLoader("src/resources/templates"), autoescape=select_autoescape(["html", "xml"])
        )
        self._register_custom_filters()
        self._register_custom_functions()

    def _register_custom_filters(self) -> None:
        """Register custom Jinja2 filters"""

        def format_number(value: int | float, precision: int = 2) -> str:
            """Format number with specified precision"""
            try:
                return f"{float(value):.{precision}f}"
            except (ValueError, TypeError):
                return str(value)

        def format_percentage(value: int | float, precision: int = 1) -> str:
            """Format value as percentage"""
            try:
                return f"{float(value):.{precision}f}%"
            except (ValueError, TypeError):
                return str(value)

        def format_datetime(value: str | datetime, format_str: str = "%Y-%m-%d %H:%M:%S") -> str:
            """Format datetime value"""
            try:
                if isinstance(value, str):
                    dt = datetime.fromisoformat(value.replace("Z", "+00:00"))
                else:
                    dt = value
                return dt.strftime(format_str)
            except (ValueError, TypeError):
                return str(value)

        # Register filters
        self.jinja_env.filters["format_number"] = format_number
        self.jinja_env.filters["format_percentage"] = format_percentage
        self.jinja_env.filters["format_datetime"] = format_datetime

    def _register_custom_functions(self) -> None:
        """Register custom Jinja2 global functions"""

        def get_chart_config(chart_type: str, data: dict[str, Any]) -> str:
            """Generate chart configuration JSON"""
            # Basic chart configuration generator
            config = {
                "type": chart_type,
                "data": data,
                "options": {
                    "responsive": True,
                    "maintainAspectRatio": False,
                },
            }
            return json.dumps(config)

        # Register global functions
        self.jinja_env.globals["render_component"] = self.component_library.render_component
        self.jinja_env.globals["get_chart_config"] = get_chart_config

    def render_template(
        self, template_id: str, context: dict[str, Any], format: RenderFormat = RenderFormat.HTML
    ) -> str:
        """Render template with advanced features"""
        try:
            # Load template
            template = self.jinja_env.get_template(f"{template_id}.html")

            # Add format-specific context
            enhanced_context = {
                **context,
                "render_format": format.value,
                "generated_at": datetime.now(),
                "template_id": template_id,
            }

            # Render template
            rendered = template.render(**enhanced_context)

            # Post-process based on format
            if format == RenderFormat.PLAIN_TEXT:
                rendered = self._html_to_text(rendered)
            elif format == RenderFormat.MARKDOWN:
                rendered = self._html_to_markdown(rendered)

            return rendered

        except TemplateError as e:
            logger.exception("Template rendering error for %s: {e}", template_id)
            return self._render_error_template(template_id, str(e))
        except Exception as e:
            logger.exception("Unexpected error rendering template %s: {e}", template_id)
            return self._render_error_template(template_id, str(e))

    def _html_to_text(self, html_content: str) -> str:
        """Convert HTML to plain text"""
        # Simple HTML to text conversion
        text = re.sub(r"<[^>]+>", "", html_content)
        text = re.sub(r"\s+", " ", text)
        return text.strip()

    def _html_to_markdown(self, html_content: str) -> str:
        """Convert HTML to Markdown"""
        # Basic HTML to Markdown conversion

        # Convert headers
        html_content = re.sub(r"<h1[^>]*>(.*?)</h1>", r"# \1\n", html_content)
        html_content = re.sub(r"<h2[^>]*>(.*?)</h2>", r"## \1\n", html_content)
        html_content = re.sub(r"<h3[^>]*>(.*?)</h3>", r"### \1\n", html_content)

        # Convert paragraphs
        html_content = re.sub(r"<p[^>]*>(.*?)</p>", r"\1\n\n", html_content)

        # Convert lists
        html_content = re.sub(r"<li[^>]*>(.*?)</li>", r"- \1\n", html_content)

        # Remove remaining HTML tags
        html_content = re.sub(r"<[^>]+>", "", html_content)

        return html_content.strip()

    def _render_error_template(self, template_id: str, error_message: str) -> str:
        """Render error template when main template fails"""
        return f"""
        <div class="template-error">
            <h2>Template Rendering Error</h2>
            <p><strong>Template:</strong> {template_id}</p>
            <p><strong>Error:</strong> {error_message}</p>
            <p>Please check the template configuration and try again.</p>
        </div>
        """

    def validate_template_file(self, template_path: Path) -> list[str]:
        """Validate a template file"""
        try:
            with open(template_path, encoding="utf-8") as f:
                content = f.read()

            # Create dummy metadata for validation
            metadata = TemplateMetadata(
                template_id=template_path.stem,
                name=template_path.stem,
                description="Template validation",
                template_type=TemplateType.CUSTOM,
                version="1.0",
                author="system",
                created_at=datetime.now(),
                updated_at=datetime.now(),
            )

            return self.validator.validate_template(content, metadata)

        except (FileNotFoundError, PermissionError, OSError) as e:
            return [f"Error reading template file: {e}"]


class TemplateLibrary:
    """Library for managing and versioning report templates"""

    def __init__(self, templates_dir: str | None = None, metadata_dir: str | None = None):
        from pathlib import Path
        
        self.templates_dir = Path(templates_dir or "src/resources/templates")
        self.metadata_dir = Path(metadata_dir or "src/resources/templates/metadata")
        self.templates: dict[str, TemplateMetadata] = {}
        self.renderer = AdvancedTemplateRenderer(ComponentLibrary())
        self._load_templates()

    def _load_templates(self) -> None:
        """Load templates and their metadata"""
        try:
            # Load metadata files
            for metadata_file in self.metadata_dir.glob("*.yaml"):
                template_id = metadata_file.stem
                with open(metadata_file, encoding="utf-8") as f:
                    metadata_data = yaml.safe_load(f)

                metadata = TemplateMetadata.from_dict(metadata_data)
                self.templates[template_id] = metadata
                logger.debug("Loaded template metadata: %s", template_id)

            # Check for template files without metadata
            for template_file in self.templates_dir.glob("*.html"):
                template_id = template_file.stem
                if template_id not in self.templates:
                    # Create default metadata
                    metadata = TemplateMetadata(
                        template_id=template_id,
                        name=template_id.replace("_", " ").title(),
                        description=f"Template: {template_id}",
                        template_type=TemplateType.CUSTOM,
                        version="1.0",
                        author="system",
                        created_at=datetime.now(),
                        updated_at=datetime.now(),
                        supported_formats=[RenderFormat.HTML],
                    )
                    self.templates[template_id] = metadata
                    self._save_metadata(template_id, metadata)

            logger.info("Loaded %s report templates", len(self.templates))

        except Exception as e:
            logger.exception("Error loading templates: %s", e)
            self._create_default_templates()

    def _create_default_templates(self) -> None:
        """Create default report templates"""
        default_templates: list[tuple[str, TemplateMetadata, str]] = [
            (
                "performance_analysis",
                TemplateMetadata(
                    template_id="performance_analysis",
                    name="Performance Analysis Report",
                    description="Comprehensive performance analysis with metrics and trends",
                    template_type=TemplateType.PERFORMANCE_ANALYSIS,
                    version="1.0",
                    author="system",
                    created_at=datetime.now(),
                    updated_at=datetime.now(),
                    supported_formats=[RenderFormat.HTML, RenderFormat.PDF],
                    required_data_fields=["performance_metrics", "optimization_results"],
                    tags=["performance", "analysis", "metrics"],
                ),
                """
<!DOCTYPE html>
<!DOCTYPE html>
<!DOCTYPE html>
<html>
<head>
    <title>{{ title }}</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 20px; }
        .header { border-bottom: 2px solid #333; padding-bottom: 10px; margin-bottom: 20px; }
        .section { margin: 20px 0; }
        .metric-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(250px, 1fr)); gap: 20px; }
        .metric-card { border: 1px solid #ddd; padding: 15px; border-radius: 5px; }
        .metric-value { font-size: 2em; font-weight: bold; color: #2c5aa0; }
        .trend-up { color: #28a745; }
        .trend-down { color: #dc3545; }
    </style>
</head>
<body>
    <div class="header">
        <h1>{{ title }}</h1>
        <p>Generated: {{ generated_at | format_datetime }}</p>
        {% if description %}
        <p>{{ description }}</p>
        {% endif %}
    </div>

    <div class="section">
        <h2>Performance Summary</h2>
        <div class="metric-grid">
            {{ render_component('metric_card',
                title='Response Time',
                value=performance_metrics.avg_response_time | format_number,
                unit='ms',
                trend={'direction': 'up' if performance_metrics.response_time_trend > 0 else 'down',
                       'value': performance_metrics.response_time_trend | format_percentage}) }}

            {{ render_component('metric_card',
                title='Memory Usage',
                value=performance_metrics.avg_memory_usage | format_number,
                unit='MB') }}
        </div>
    </div>

    {% if optimization_results %}
    <div class="section">
        <h2>Optimization Results</h2>
        {% for optimization in optimization_results %}
        <div class="optimization-result">
            <h3>{{ optimization.name }}</h3>
            <p>Improvement: {{ optimization.improvement_percent | format_percentage }}</p>
        </div>
        {% endfor %}
    </div>
    {% endif %}
</body>
</html>
                """.strip(),
            ),
        ]

        # Create default templates
        for template_id, metadata, content in default_templates:
            self.templates[template_id] = metadata

            # Save template file
            template_file = self.templates_dir / f"{template_id}.html"
            with open(template_file, "w", encoding="utf-8") as f:
                f.write(content)

            # Save metadata
            self._save_metadata(template_id, metadata)

        logger.info("Created default report templates")

    def _save_metadata(self, template_id: str, metadata: TemplateMetadata) -> None:
        """Save template metadata to file"""
        metadata_file = self.metadata_dir / f"{template_id}.yaml"
        with open(metadata_file, "w", encoding="utf-8") as f:
            yaml.dump(metadata.to_dict(), f, default_flow_style=False)

    def get_template(self, template_id: str) -> TemplateMetadata | None:
        """Get template metadata by ID"""
        return self.templates.get(template_id)

    def list_templates(self, template_type: TemplateType | None = None) -> list[str]:
        """List available templates, optionally filtered by type"""
        if template_type:
            return [tid for tid, tmpl in self.templates.items() if tmpl.template_type == template_type]
        return list(self.templates.keys())

    def register_template(self, metadata: TemplateMetadata, content: str) -> None:
        """Register a new template"""
        # Validate template content
        issues = self.renderer.validator.validate_template(content, metadata)
        if issues:
            raise ValueError(f"Template validation failed: {issues}")

        # Save template file
        template_file = self.templates_dir / f"{metadata.template_id}.html"
        with open(template_file, "w", encoding="utf-8") as f:
            f.write(content)

        # Save metadata
        self.templates[metadata.template_id] = metadata
        self._save_metadata(metadata.template_id, metadata)

        logger.info("Registered template: %s", metadata.template_id)
