"""Report Branding Service - Optional logo and branding management

This module provides optional branding features for reports, including logo management.
When no logo is configured, reports maintain their professional appearance without
any placeholders or visual gaps.
"""

import base64
import logging
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any

import yaml
from PIL import Image

logger = logging.getLogger(__name__)


class LogoPosition(Enum):
    """Logo positioning options"""

    TOP_LEFT = "top_left"
    TOP_CENTER = "top_center"
    TOP_RIGHT = "top_right"
    HEADER_LEFT = "header_left"
    HEADER_RIGHT = "header_right"


class LogoSize(Enum):
    """Logo size presets"""

    SMALL = "small"      # 100px max dimension
    MEDIUM = "medium"    # 200px max dimension
    LARGE = "large"      # 300px max dimension
    CUSTOM = "custom"    # User-defined dimensions


@dataclass
class LogoConfiguration:
    """Configuration for logo display"""

    enabled: bool = False
    file_path: str | None = None
    position: LogoPosition = LogoPosition.TOP_RIGHT
    size: LogoSize = LogoSize.MEDIUM
    custom_width: int | None = None
    custom_height: int | None = None
    opacity: float = 1.0  # 0.0 to 1.0
    margin_top: int = 10
    margin_right: int = 10
    margin_bottom: int = 10
    margin_left: int = 10

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for serialization"""
        return {
            "enabled": self.enabled,
            "file_path": self.file_path,
            "position": self.position.value,
            "size": self.size.value,
            "custom_width": self.custom_width,
            "custom_height": self.custom_height,
            "opacity": self.opacity,
            "margin_top": self.margin_top,
            "margin_right": self.margin_right,
            "margin_bottom": self.margin_bottom,
            "margin_left": self.margin_left,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "LogoConfiguration":
        """Create from dictionary"""
        return cls(
            enabled=data.get("enabled", False),
            file_path=data.get("file_path"),
            position=LogoPosition(data.get("position", "top_right")),
            size=LogoSize(data.get("size", "medium")),
            custom_width=data.get("custom_width"),
            custom_height=data.get("custom_height"),
            opacity=data.get("opacity", 1.0),
            margin_top=data.get("margin_top", 10),
            margin_right=data.get("margin_right", 10),
            margin_bottom=data.get("margin_bottom", 10),
            margin_left=data.get("margin_left", 10),
        )


@dataclass
class BrandingConfiguration:
    """Complete branding configuration"""

    organization_name: str | None = None
    logo: LogoConfiguration = field(default_factory=LogoConfiguration)
    primary_color: str = "#2c5aa0"
    secondary_color: str = "#6c757d"
    accent_color: str = "#28a745"
    font_family: str = "Arial, sans-serif"
    custom_css: str | None = None

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for serialization"""
        return {
            "organization_name": self.organization_name,
            "logo": self.logo.to_dict(),
            "primary_color": self.primary_color,
            "secondary_color": self.secondary_color,
            "accent_color": self.accent_color,
            "font_family": self.font_family,
            "custom_css": self.custom_css,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "BrandingConfiguration":
        """Create from dictionary"""
        return cls(
            organization_name=data.get("organization_name"),
            logo=LogoConfiguration.from_dict(data.get("logo", {})),
            primary_color=data.get("primary_color", "#2c5aa0"),
            secondary_color=data.get("secondary_color", "#6c757d"),
            accent_color=data.get("accent_color", "#28a745"),
            font_family=data.get("font_family", "Arial, sans-serif"),
            custom_css=data.get("custom_css"),
        )


class LogoProcessor:
    """Processes and optimizes logos for report use"""

    SUPPORTED_FORMATS = {".png", ".jpg", ".jpeg", ".gif", ".bmp", ".svg"}
    MAX_FILE_SIZE = 5 * 1024 * 1024  # 5MB

    def __init__(self):
        self.size_presets = {
            LogoSize.SMALL: (100, 100),
            LogoSize.MEDIUM: (200, 200),
            LogoSize.LARGE: (300, 300),
        }

    def validate_logo_file(self, file_path: str) -> tuple[bool, str | None]:
        """Validate logo file format and size"""
        try:
            path = Path(file_path)

            # Check if file exists
            if not path.exists():
                return False, f"Logo file not found: {file_path}"

            # Check file extension
            if path.suffix.lower() not in self.SUPPORTED_FORMATS:
                return False, f"Unsupported file format. Supported: {', '.join(self.SUPPORTED_FORMATS)}"

            # Check file size
            if path.stat().st_size > self.MAX_FILE_SIZE:
                return False, f"Logo file too large. Maximum size: {self.MAX_FILE_SIZE // (1024*1024)}MB"

            # Try to open as image (except SVG)
            if path.suffix.lower() != ".svg":
                try:
                    with Image.open(path) as img:
                        # Basic image validation
                        img.verify()
                except Exception as e:
                    return False, f"Invalid image file: {e!s}"

            return True, None

        except Exception as e:
            return False, f"Error validating logo file: {e!s}"

    def process_logo(self, config: LogoConfiguration) -> dict[str, Any] | None:
        """Process logo according to configuration"""
        if not config.enabled or not config.file_path:
            return None

        try:
            # Validate file
            is_valid, error_msg = self.validate_logo_file(config.file_path)
            if not is_valid:
                logger.error("Logo validation failed: %s", error_msg)
                return None

            path = Path(config.file_path)

            # Handle SVG files differently
            if path.suffix.lower() == ".svg":
                return self._process_svg_logo(path, config)
            return self._process_raster_logo(path, config)

        except Exception as e:
            logger.exception("Error processing logo: %s", e)
            return None

    def _process_raster_logo(self, path: Path, config: LogoConfiguration) -> dict[str, Any]:
        """Process raster image logo (PNG, JPG, etc.)"""
        with Image.open(path) as img:
            # Convert to RGBA for transparency support
            if img.mode != "RGBA":
                img = img.convert("RGBA")

            # Determine target size
            if config.size == LogoSize.CUSTOM and config.custom_width and config.custom_height:
                target_size = (config.custom_width, config.custom_height)
            else:
                target_size = self.size_presets[config.size]

            # Resize maintaining aspect ratio
            img.thumbnail(target_size, Image.Resampling.LANCZOS)

            # Apply opacity if needed
            if config.opacity < 1.0:
                # Create alpha channel with opacity
                alpha = img.split()[-1]
                alpha = alpha.point(lambda p: int(p * config.opacity))
                img.putalpha(alpha)

            # Convert to base64 for embedding
            import io
            buffer = io.BytesIO()
            img.save(buffer, format="PNG", optimize=True)
            img_data = base64.b64encode(buffer.getvalue()).decode()

            return {
                "format": "png",
                "data": f"data:image/png;base64,{img_data}",
                "width": img.width,
                "height": img.height,
                "original_path": str(path),
            }

    def _process_svg_logo(self, path: Path, config: LogoConfiguration) -> dict[str, Any]:
        """Process SVG logo"""
        with open(path, encoding="utf-8") as f:
            svg_content = f.read()

        # Apply opacity to SVG if needed
        if config.opacity < 1.0:
            # Simple opacity application - wrap in group with opacity
            svg_content = svg_content.replace(
                "<svg",
                f'<svg style="opacity: {config.opacity}"',
            )

        # Encode SVG for embedding
        svg_data = base64.b64encode(svg_content.encode()).decode()

        return {
            "format": "svg",
            "data": f"data:image/svg+xml;base64,{svg_data}",
            "content": svg_content,
            "original_path": str(path),
        }


class ReportBrandingService:
    """Main service for managing report branding"""

    def __init__(self, config_path: Path | None = None):
        self.config_path = config_path or Path("config/branding.yaml")
        self.logo_processor = LogoProcessor()
        self.branding_config = BrandingConfiguration()
        self._load_configuration()

    def _load_configuration(self) -> None:
        """Load branding configuration from file"""
        try:
            if self.config_path.exists():
                with open(self.config_path, encoding="utf-8") as f:
                    config_data = yaml.safe_load(f)

                self.branding_config = BrandingConfiguration.from_dict(config_data)
                logger.info("Loaded branding configuration")
            else:
                logger.info("No branding configuration found, using defaults")
                self._save_configuration()

        except Exception as e:
            logger.exception("Error loading branding configuration: %s", e)
            self.branding_config = BrandingConfiguration()

    def _save_configuration(self) -> None:
        """Save branding configuration to file"""
        try:
            self.config_path.parent.mkdir(parents=True, exist_ok=True)

            with open(self.config_path, "w", encoding="utf-8") as f:
                yaml.dump(self.branding_config.to_dict(), f, default_flow_style=False)

            logger.info("Saved branding configuration")

        except Exception as e:
            logger.exception("Error saving branding configuration: %s", e)

    def configure_logo(self, file_path: str, position: LogoPosition = LogoPosition.TOP_RIGHT,
                      size: LogoSize = LogoSize.MEDIUM, **kwargs) -> bool:
        """Configure logo settings"""
        try:
            # Validate logo file
            is_valid, error_msg = self.logo_processor.validate_logo_file(file_path)
            if not is_valid:
                logger.error("Logo configuration failed: %s", error_msg)
                return False

            # Update logo configuration
            self.branding_config.logo = LogoConfiguration(
                enabled=True,
                file_path=file_path,
                position=position,
                size=size,
                custom_width=kwargs.get("custom_width"),
                custom_height=kwargs.get("custom_height"),
                opacity=kwargs.get("opacity", 1.0),
                margin_top=kwargs.get("margin_top", 10),
                margin_right=kwargs.get("margin_right", 10),
                margin_bottom=kwargs.get("margin_bottom", 10),
                margin_left=kwargs.get("margin_left", 10),
            )

            self._save_configuration()
            logger.info("Logo configured: %s", file_path)
            return True

        except Exception as e:
            logger.exception("Error configuring logo: %s", e)
            return False

    def disable_logo(self) -> None:
        """Disable logo display"""
        self.branding_config.logo.enabled = False
        self._save_configuration()
        logger.info("Logo disabled")

    def update_branding(self, organization_name: str | None = None,
                       primary_color: str | None = None,
                       secondary_color: str | None = None,
                       accent_color: str | None = None,
                       font_family: str | None = None,
                       custom_css: str | None = None) -> None:
        """Update branding configuration"""
        if organization_name is not None:
            self.branding_config.organization_name = organization_name
        if primary_color is not None:
            self.branding_config.primary_color = primary_color
        if secondary_color is not None:
            self.branding_config.secondary_color = secondary_color
        if accent_color is not None:
            self.branding_config.accent_color = accent_color
        if font_family is not None:
            self.branding_config.font_family = font_family
        if custom_css is not None:
            self.branding_config.custom_css = custom_css

        self._save_configuration()
        logger.info("Branding configuration updated")

    def get_logo_data(self) -> dict[str, Any] | None:
        """Get processed logo data for report embedding"""
        if not self.branding_config.logo.enabled:
            return None

        return self.logo_processor.process_logo(self.branding_config.logo)

    def generate_report_css(self) -> str:
        """Generate CSS for report styling with optional logo"""
        css = f"""
        :root {{
            --primary-color: {self.branding_config.primary_color};
            --secondary-color: {self.branding_config.secondary_color};
            --accent-color: {self.branding_config.accent_color};
            --font-family: {self.branding_config.font_family};
        }}

        body {{
            font-family: var(--font-family);
            color: #333;
            line-height: 1.6;
            margin: 0;
            padding: 20px;
        }}

        .report-header {{
            border-bottom: 2px solid var(--primary-color);
            padding-bottom: 20px;
            margin-bottom: 30px;
            position: relative;
        }}

        .report-title {{
            color: var(--primary-color);
            font-size: 2.5em;
            font-weight: bold;
            margin: 0;
        }}

        .report-subtitle {{
            color: var(--secondary-color);
            font-size: 1.2em;
            margin: 10px 0;
        }}
        """

        # Add logo CSS only if logo is enabled
        logo_data = self.get_logo_data()
        if logo_data:
            logo_css = self._generate_logo_css(logo_data)
            css += logo_css

        # Add custom CSS if provided
        if self.branding_config.custom_css:
            css += f"\n\n/* Custom CSS */\n{self.branding_config.custom_css}"

        return css

    def _generate_logo_css(self, logo_data: dict[str, Any]) -> str:
        """Generate CSS for logo positioning"""
        config = self.branding_config.logo

        # Base logo styles
        logo_css = f"""

        .report-logo {{
            position: absolute;
            opacity: {config.opacity};
            z-index: 10;
        }}

        .report-logo img {{
            max-width: 100%;
            height: auto;
            display: block;
        }}
        """

        # Position-specific styles
        if config.position == LogoPosition.TOP_RIGHT:
            logo_css += f"""
            .report-logo {{
                top: {config.margin_top}px;
                right: {config.margin_right}px;
            }}
            """
        elif config.position == LogoPosition.TOP_LEFT:
            logo_css += f"""
            .report-logo {{
                top: {config.margin_top}px;
                left: {config.margin_left}px;
            }}
            """
        elif config.position == LogoPosition.TOP_CENTER:
            logo_css += f"""
            .report-logo {{
                top: {config.margin_top}px;
                left: 50%;
                transform: translateX(-50%);
            }}
            """
        elif config.position == LogoPosition.HEADER_LEFT:
            logo_css += f"""
            .report-logo {{
                top: 50%;
                left: {config.margin_left}px;
                transform: translateY(-50%);
            }}
            """
        elif config.position == LogoPosition.HEADER_RIGHT:
            logo_css += f"""
            .report-logo {{
                top: 50%;
                right: {config.margin_right}px;
                transform: translateY(-50%);
            }}
            """

        return logo_css

    def get_branding_context(self) -> dict[str, Any]:
        """Get branding context for template rendering"""
        context = {
            "branding": {
                "organization_name": self.branding_config.organization_name,
                "primary_color": self.branding_config.primary_color,
                "secondary_color": self.branding_config.secondary_color,
                "accent_color": self.branding_config.accent_color,
                "font_family": self.branding_config.font_family,
                "has_logo": self.branding_config.logo.enabled,
                "logo_data": self.get_logo_data() if self.branding_config.logo.enabled else None,
                "custom_css": self.generate_report_css(),
            },
        }

        return context

    def get_configuration(self) -> BrandingConfiguration:
        """Get current branding configuration"""
        return self.branding_config

    def reset_to_defaults(self) -> None:
        """Reset branding to default configuration"""
        self.branding_config = BrandingConfiguration()
        self._save_configuration()
        logger.info("Branding configuration reset to defaults")
