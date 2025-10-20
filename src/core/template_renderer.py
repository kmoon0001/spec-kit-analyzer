"""Template Renderer - Professional report template rendering

This module provides template rendering capabilities for generating
professional compliance reports with proper styling and formatting.
"""

import logging
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


class TemplateRenderer:
    """Professional template renderer for compliance reports"""

    def __init__(self, templates_dir: Path | None = None):
        self.templates_dir = templates_dir or Path("src/resources/report_templates")
        self.templates: dict[str, str] = {}
        self._load_templates()

    def _load_templates(self) -> None:
        """Load templates from the templates directory"""
        if not self.templates_dir.exists():
            logger.warning("Templates directory not found: %s", self.templates_dir)
            self._create_default_template()
            return

        try:
            for template_file in self.templates_dir.glob("*.html"):
                template_id = template_file.stem
                with open(template_file, encoding="utf-8") as f:
                    self.templates[template_id] = f.read()
                logger.debug("Loaded template: %s", template_id)

            if not self.templates:
                self._create_default_template()

            logger.info("Loaded %s report templates", len(self.templates))

        except (FileNotFoundError, PermissionError, OSError) as e:
            logger.exception("Error loading templates: %s", e)
            self._create_default_template()

    def _create_default_template(self) -> None:
        """Create a default template"""
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
            </div>
            <div class="content">
                {{ content }}
            </div>
        </body>
        </html>
        """

        self.templates["default"] = default_template.strip()
        logger.info("Created default report template")

    def render_template(self, template_id: str, context: dict[str, Any]) -> str:
        """Render a template with the given context"""
        if template_id not in self.templates:
            logger.warning("Template not found: %s, using default", template_id)
            template_id = "default"

        template_content = self.templates.get(
            template_id, self.templates.get("default", "")
        )

        try:
            # Simple template rendering (basic variable substitution)
            rendered = template_content
            for key, value in context.items():
                placeholder = f"{{{{ {key} }}}}"
                rendered = rendered.replace(placeholder, str(value))

            return rendered

        except Exception as e:
            logger.exception("Error rendering template %s: {e}", template_id)
            return (
                f"<html><body><h1>Error rendering report</h1><p>{e!s}</p></body></html>"
            )

    def get_available_templates(self) -> list[str]:
        """Get list of available template IDs"""
        return list(self.templates.keys())

    def validate_template(self, template_content: str) -> tuple[bool, str | None]:
        """Validate template content"""
        try:
            # Basic validation - check for required placeholders
            if "{{ title }}" not in template_content:
                return False, "Template must contain {{ title }} placeholder"

            # Check for basic HTML structure
            if "<html>" not in template_content.lower():
                return False, "Template must contain valid HTML structure"

            return True, None

        except (ValueError, TypeError, AttributeError) as e:
            return False, f"Template validation error: {e}"
