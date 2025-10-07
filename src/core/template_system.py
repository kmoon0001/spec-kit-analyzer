"""
Advanced Template System and Rendering Engine

This module provides comprehensive template management, rendering, and component
library functionality for the reporting system.
"""

import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Dict, List, Optional, Any, Union, Callable
import json
import yaml
import re

logger = logging.getLogger(__name__)


class TemplateType(Enum):
    """Types of templates supported"""
    REPORT = "report"
    SECTION = "section"
    COMPONENT = "component"
    CHART = "chart"
    DASHBOARD = "dashboard"
    EMAIL = "email"


class ComponentType(Enum):
    """Types of reusable components"""
    CHART = "chart"
    TABLE = "table"
    METRIC_CARD = "metric_card"
    ALERT_PANEL = "alert_panel"
    TREND_INDICATOR = "trend_indicator"
    PROGRESS_BAR = "progress_bar"
    STATUS_BADGE = "status_badge"
    TIMELINE = "timeline"


@dataclass
class TemplateMetadata:
    """Metadata for templates"""
    id: str
    name: str
    description: str
    template_type: TemplateType
    version: str = "1.0.0"
    author: str = ""
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    tags: List[str] = field(default_factory=list)
    required_data: List[str] = field(default_factory=list)
    optional_data: List[str] = field(default_factory=list)
    supported_formats: List[str] = field(default_factory=lambda: ["html"])
    dependencies: List[str] = field(default_factory=list)
    custom_properties: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ComponentDefinition:
    """Definition of a reusable component"""
    id: str
    name: str
    component_type: ComponentType
    template_content: str
    default_props: Dict[str, Any] = field(default_factory=dict)
    required_props: List[str] = field(default_factory=list)
    css_classes: List[str] = field(default_factory=list)
    javascript_code: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class RenderContext:
    """Context for template rendering"""
    data: Dict[str, Any]
    components: Dict[str, Any] = field(default_factory=dict)
    filters: Dict[str, Callable] = field(default_factory=dict)
    globals: Dict[str, Any] = field(default_factory=dict)
    template_vars: Dict[str, Any] = field(default_factory=dict)

c
lass TemplateValidator:
    """Validates templates for correctness and compatibility"""
    
    def __init__(self):
        self.validation_rules = {
            'required_blocks': ['content'],
            'forbidden_tags': ['script', 'iframe', 'object', 'embed'],
            'max_template_size': 1024 * 1024,  # 1MB
            'allowed_extensions': ['.html', '.jinja2', '.j2']
        }
    
    def validate_template(self, template_content: str, metadata: TemplateMetadata) -> List[str]:
        """Validate template content and return list of issues"""
        issues = []
        
        # Check template size
        if len(template_content) > self.validation_rules['max_template_size']:
            issues.append(f"Template size exceeds maximum allowed size")
        
        # Check for forbidden tags
        for tag in self.validation_rules['forbidden_tags']:
            if f'<{tag}' in template_content.lower():
                issues.append(f"Forbidden tag found: {tag}")
        
        # Check required data availability
        template_vars = self._extract_template_variables(template_content)
        missing_required = set(metadata.required_data) - set(template_vars)
        if missing_required:
            issues.append(f"Required data not used in template: {missing_required}")
        
        return issues
    
    def _extract_template_variables(self, template_content: str) -> List[str]:
        """Extract variable names from template content"""
        # Simple regex to find template variables
        pattern = r'\{\{\s*([a-zA-Z_][a-zA-Z0-9_\.]*)\s*\}\}'
        matches = re.findall(pattern, template_content)
        return [match.split('.')[0] for match in matches]
    
    def validate_component(self, component: ComponentDefinition) -> List[str]:
        """Validate component definition"""
        issues = []
        
        # Validate template content
        template_issues = self.validate_template(
            component.template_content,
            TemplateMetadata(
                id=component.id,
                name=component.name,
                description="Component template",
                template_type=TemplateType.COMPONENT,
                required_data=component.required_props
            )
        )
        issues.extend(template_issues)
        
        # Check required props are defined
        if not component.required_props:
            issues.append("Component should define required props")
        
        return issues


class ComponentLibrary:
    """Library of reusable report components"""
    
    def __init__(self, components_dir: Optional[Path] = None):
        self.components_dir = components_dir or Path("src/resources/report_components")
        self.components: Dict[str, ComponentDefinition] = {}
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
                with open(component_file, 'r', encoding='utf-8') as f:
                    component_data = yaml.safe_load(f)
                
                component = self._dict_to_component(component_data)
                
                # Validate component
                issues = self.validator.validate_component(component)
                if issues:
                    logger.warning(f"Component {component_id} has validation issues: {issues}")
                
                self.components[component_id] = component
                logger.debug(f"Loaded component: {component_id}")
            
            logger.info(f"Loaded {len(self.components)} report components")
            
        except Exception as e:
            logger.error(f"Error loading components: {e}")
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
                css_classes=["metric-card", "card"]
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
                css_classes=["progress-container"]
            )
        }
        
        # Save default components
        for comp_id, component in default_components.items():
            self.components[comp_id] = component
            self._save_component(comp_id, component)
        
        logger.info("Created default report components")
    
    def _dict_to_component(self, data: Dict[str, Any]) -> ComponentDefinition:
        """Convert dictionary to ComponentDefinition"""
        return ComponentDefinition(
            id=data['id'],
            name=data['name'],
            component_type=ComponentType(data['component_type']),
            template_content=data['template_content'],
            required_props=data.get('required_props', []),
            default_props=data.get('default_props', {}),
            css_classes=data.get('css_classes', []),
            javascript_code=data.get('javascript_code'),
            metadata=data.get('metadata', {})
        )
    
    def _save_component(self, comp_id: str, component: ComponentDefinition) -> None:
        """Save component to file"""
        component_file = self.components_dir / f"{comp_id}.yaml"
        component_dict = {
            'id': component.id,
            'name': component.name,
            'component_type': component.component_type.value,
            'template_content': component.template_content,
            'required_props': component.required_props,
            'default_props': component.default_props,
            'css_classes': component.css_classes,
            'javascript_code': component.javascript_code,
            'metadata': component.metadata
        }
        with open(component_file, 'w', encoding='utf-8') as f:
            yaml.dump(component_dict, f, default_flow_style=False)
    
    def get_component(self, component_id: str) -> Optional[ComponentDefinition]:
        """Get a component by ID"""
        return self.components.get(component_id)
    
    def list_components(self, component_type: Optional[ComponentType] = None) -> List[str]:
        """List available components, optionally filtered by type"""
        if component_type:
            return [
                comp_id for comp_id, comp in self.components.items()
                if comp.component_type == component_type
            ]
        return list(self.components.keys())
    
    def register_component(self, component: ComponentDefinition) -> None:
        """Register a new component"""
        # Validate component
        issues = self.validator.validate_component(component)
        if issues:
            raise ValueError(f"Component validation failed: {issues}")
        
        self.components[component.id] = component
        self._save_component(component.id, component)
        logger.info(f"Registered component: {component.id}")
    
    def render_component(self, component_id: str, props: Dict[str, Any]) -> str:
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
        except Exception as e:
            logger.error(f"Error rendering component {component_id}: {e}")
            return f"<div class='component-error'>Error rendering component: {component_id}</div>"