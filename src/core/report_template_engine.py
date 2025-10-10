"""Report Template Engine

This module handles template loading, rendering, and management for reports.
Separated from the main engine for better maintainability and testing.
"""

import logging
from pathlib import Path
from typing import Any

import yaml

logger = logging.getLogger(__name__)


class TemplateEngine:
    """Template engine for rendering reports"""

    def __init__(self, templates_dir: Path | None = None):
        self.templates_dir = templates_dir or Path("src/resources/report_templates")
        self.templates: dict[str, str] = {}
        self.template_metadata: dict[str, dict[str, Any]] = {}
        self._load_templates()

    def _load_templates(self) -> None:
        """Load templates from the templates directory"""
        if not self.templates_dir.exists():
            logger.warning("Templates directory not found: %s", self.templates_dir)
            self.templates_dir.mkdir(parents=True, exist_ok=True)
            self._create_default_templates()
            return

        try:
            for template_file in self.templates_dir.glob("*.html"):
                template_id = template_file.stem
                self.templates[template_id] = template_file.read_text(encoding="utf-8")

                # Load metadata if available
                metadata_file = template_file.with_suffix(".yaml")
                if metadata_file.exists():
                    with open(metadata_file, encoding="utf-8") as f:
                        self.template_metadata[template_id] = yaml.safe_load(f)

                logger.debug("Loaded template: %s", template_id)
        except (FileNotFoundError, PermissionError, OSError) as e:
            logger.exception("Error loading templates: %s", e)
            self._create_default_templates()

    def _create_default_templates(self) -> None:
        """Create default templates"""
        default_template = """
<!DOCTYPE html>
<!DOCTYPE html>
<!DOCTYPE html>
<html>
<head>
    <title>{{ title }}</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 20px; }
        .header { background: #f0f0f0; padding: 20px; border-radius: 5px; }
        .section { margin: 20px 0; padding: 15px; border-left: 3px solid #007acc; }
        .data-table { width: 100%; border-collapse: collapse; margin: 10px 0; }
        .data-table th, .data-table td { border: 1px solid #ddd; padding: 8px; text-align: left; }
        .data-table th { background-color: #f2f2f2; }
    </style>
</head>
<body>
    <div class="header">
        <h1>{{ title }}</h1>
        <p>{{ description }}</p>
        <p><strong>Generated:</strong> {{ generated_at }}</p>
    </div>

    {% for section in sections %}
    <div class="section">
        <h2>{{ section.title }}</h2>
        <div>{{ section.content | safe }}</div>
    </div>
    {% endfor %}
</body>
</html>
        """

        # Save default template
        default_path = self.templates_dir / "default.html"
        default_path.write_text(default_template.strip(), encoding="utf-8")
        self.templates["default"] = default_template.strip()

        logger.info("Created default report templates")

    def render_template(self, template_id: str, context: dict[str, Any]) -> str:
        """Render a template with the given context"""
        if template_id not in self.templates:
            logger.warning("Template not found: %s, using default", template_id)
            template_id = "default"

        if template_id not in self.templates:
            return f"<html><body><h1>Template Error</h1><p>Template '{template_id}' not found</p></body></html>"

        template_content = self.templates[template_id]

        try:
            # Simple template rendering (can be enhanced with Jinja2 if needed)
            rendered = template_content
            for key, value in context.items():
                placeholder = f"{{{{ {key} }}}}"
                rendered = rendered.replace(placeholder, str(value))

            return rendered
        except Exception as e:
            logger.exception("Error rendering template %s: {e}", template_id)
            return f"<html><body><h1>Error rendering report</h1><p>{e!s}</p></body></html>"

    def get_available_templates(self) -> list[str]:
        """Get list of available template IDs"""
        return list(self.templates.keys())

    def get_template_metadata(self, template_id: str) -> dict[str, Any]:
        """Get metadata for a template"""
        return self.template_metadata.get(template_id, {})

    def reload_templates(self) -> None:
        """Reload all templates from disk"""
        self.templates.clear()
        self.template_metadata.clear()
        self._load_templates()
        logger.info("Reloaded all templates")

    def add_template(self, template_id: str, content: str, metadata: dict[str, Any] | None = None) -> None:
        """Add a new template programmatically"""
        self.templates[template_id] = content
        if metadata:
            self.template_metadata[template_id] = metadata
        logger.info("Added template: %s", template_id)

    def remove_template(self, template_id: str) -> bool:
        """Remove a template"""
        if template_id in self.templates:
            del self.templates[template_id]
            if template_id in self.template_metadata:
                del self.template_metadata[template_id]
            logger.info("Removed template: %s", template_id)
            return True
        return False
