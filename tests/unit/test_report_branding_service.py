"""
Tests for Report Branding Service

This module provides comprehensive tests for the optional logo and branding system,
ensuring that reports work perfectly both with and without logos configured.
"""

import pytest
import tempfile
import shutil
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
from PIL import Image
import yaml

from src.core.report_branding_service import (
    ReportBrandingService,
    LogoProcessor,
    LogoConfiguration,
    BrandingConfiguration,
    LogoPosition,
    LogoSize
)


class TestLogoConfiguration:
    """Test LogoConfiguration functionality"""
    
    def test_default_configuration(self):
        """Test default logo configuration"""
        config = LogoConfiguration()
        
        assert config.enabled is False
        assert config.file_path is None
        assert config.position == LogoPosition.TOP_RIGHT
        assert config.size == LogoSize.MEDIUM
        assert config.opacity == 1.0
    
    def test_configuration_serialization(self):
        """Test configuration to/from dict conversion"""
        config = LogoConfiguration(
            enabled=True,
            file_path="/path/to/logo.png",
            position=LogoPosition.TOP_LEFT,
            size=LogoSize.LARGE,
            opacity=0.8
        )
        
        config_dict = config.to_dict()
        restored_config = LogoConfiguration.from_dict(config_dict)
        
        assert restored_config.enabled == config.enabled
        assert restored_config.file_path == config.file_path
        assert restored_config.position == config.position
        assert restored_config.size == config.size
        assert restored_config.opacity == config.opacity


class TestBrandingConfiguration:
    """Test BrandingConfiguration functionality"""
    
    def test_default_branding(self):
        """Test default branding configuration"""
        config = BrandingConfiguration()
        
        assert config.organization_name is None
        assert config.logo.enabled is False
        assert config.primary_color == "#2c5aa0"
        assert config.font_family == "Arial, sans-serif"
    
    def test_branding_serialization(self):
        """Test branding configuration serialization"""
        config = BrandingConfiguration(
            organization_name="Test Org",
            primary_color="#123456",
            secondary_color="#789abc"
        )
        
        config_dict = config.to_dict()
        restored_config = BrandingConfiguration.from_dict(config_dict)
        
        assert restored_config.organization_name == config.organization_name
        assert restored_config.primary_color == config.primary_color
        assert restored_config.secondary_color == config.secondary_color


class TestLogoProcessor:
    """Test LogoProcessor functionality"""
    
    @pytest.fixture
    def processor(self):
        """Create a logo processor for testing"""
        return LogoProcessor()
    
    @pytest.fixture
    def temp_dir(self):
        """Create temporary directory for test files"""
        temp_dir = tempfile.mkdtemp()
        yield Path(temp_dir)
        shutil.rmtree(temp_dir)
    
    def create_test_image(self, path: Path, size: tuple = (200, 100), format: str = 'PNG'):
        """Create a test image file"""
        img = Image.new('RGBA', size, color=(255, 0, 0, 255))
        img.save(path, format=format)
        return path
    
    def test_validate_nonexistent_file(self, processor):
        """Test validation of non-existent file"""
        is_valid, error = processor.validate_logo_file("/nonexistent/file.png")
        
        assert is_valid is False
        assert "not found" in error.lower()
    
    def test_validate_unsupported_format(self, processor, temp_dir):
        """Test validation of unsupported file format"""
        test_file = temp_dir / "test.txt"
        test_file.write_text("not an image")
        
        is_valid, error = processor.validate_logo_file(str(test_file))
        
        assert is_valid is False
        assert "unsupported file format" in error.lower()
    
    def test_validate_valid_png(self, processor, temp_dir):
        """Test validation of valid PNG file"""
        test_file = temp_dir / "test.png"
        self.create_test_image(test_file, format='PNG')
        
        is_valid, error = processor.validate_logo_file(str(test_file))
        
        assert is_valid is True
        assert error is None
    
    def test_validate_valid_jpg(self, processor, temp_dir):
        """Test validation of valid JPG file"""
        test_file = temp_dir / "test.jpg"
        # Create RGB image for JPEG (no transparency)
        img = Image.new('RGB', (200, 100), color=(255, 0, 0))
        img.save(test_file, format='JPEG')
        
        is_valid, error = processor.validate_logo_file(str(test_file))
        
        assert is_valid is True
        assert error is None
    
    def test_validate_svg_file(self, processor, temp_dir):
        """Test validation of SVG file"""
        test_file = temp_dir / "test.svg"
        svg_content = '''<?xml version="1.0" encoding="UTF-8"?>
        <svg width="100" height="50" xmlns="http://www.w3.org/2000/svg">
            <rect width="100" height="50" fill="red"/>
        </svg>'''
        test_file.write_text(svg_content)
        
        is_valid, error = processor.validate_logo_file(str(test_file))
        
        assert is_valid is True
        assert error is None
    
    @patch('src.core.report_branding_service.Image')
    def test_process_raster_logo(self, mock_image, processor, temp_dir):
        """Test processing of raster logo"""
        test_file = temp_dir / "test.png"
        self.create_test_image(test_file)
        
        # Mock PIL Image operations
        mock_img = MagicMock()
        mock_img.mode = 'RGBA'
        mock_img.width = 150
        mock_img.height = 75
        mock_image.open.return_value.__enter__.return_value = mock_img
        
        config = LogoConfiguration(
            enabled=True,
            file_path=str(test_file),
            size=LogoSize.MEDIUM,
            opacity=0.8
        )
        
        result = processor.process_logo(config)
        
        assert result is not None
        assert result['format'] == 'png'
        assert 'data' in result
        assert result['width'] == 150
        assert result['height'] == 75
    
    def test_process_svg_logo(self, processor, temp_dir):
        """Test processing of SVG logo"""
        test_file = temp_dir / "test.svg"
        svg_content = '''<svg width="100" height="50">
            <rect width="100" height="50" fill="red"/>
        </svg>'''
        test_file.write_text(svg_content)
        
        config = LogoConfiguration(
            enabled=True,
            file_path=str(test_file),
            opacity=0.9
        )
        
        result = processor.process_logo(config)
        
        assert result is not None
        assert result['format'] == 'svg'
        assert 'data' in result
        assert 'content' in result
        assert 'opacity: 0.9' in result['content']
    
    def test_process_disabled_logo(self, processor):
        """Test processing when logo is disabled"""
        config = LogoConfiguration(enabled=False)
        
        result = processor.process_logo(config)
        
        assert result is None


class TestReportBrandingService:
    """Test ReportBrandingService functionality"""
    
    @pytest.fixture
    def temp_config_dir(self):
        """Create temporary directory for config files"""
        temp_dir = tempfile.mkdtemp()
        yield Path(temp_dir)
        shutil.rmtree(temp_dir)
    
    @pytest.fixture
    def branding_service(self, temp_config_dir):
        """Create branding service with temporary config"""
        config_path = temp_config_dir / "branding.yaml"
        return ReportBrandingService(config_path)
    
    @pytest.fixture
    def temp_logo_dir(self):
        """Create temporary directory for logo files"""
        temp_dir = tempfile.mkdtemp()
        yield Path(temp_dir)
        shutil.rmtree(temp_dir)
    
    def create_test_logo(self, path: Path, format: str = 'PNG'):
        """Create a test logo file"""
        img = Image.new('RGBA', (200, 100), color=(0, 0, 255, 255))
        img.save(path, format=format)
        return path
    
    def test_service_initialization(self, branding_service):
        """Test service initialization with default config"""
        assert branding_service.branding_config is not None
        assert branding_service.branding_config.logo.enabled is False
        assert branding_service.logo_processor is not None
    
    def test_configure_logo_success(self, branding_service, temp_logo_dir):
        """Test successful logo configuration"""
        logo_file = temp_logo_dir / "logo.png"
        self.create_test_logo(logo_file)
        
        success = branding_service.configure_logo(
            str(logo_file),
            position=LogoPosition.TOP_LEFT,
            size=LogoSize.LARGE
        )
        
        assert success is True
        assert branding_service.branding_config.logo.enabled is True
        assert branding_service.branding_config.logo.file_path == str(logo_file)
        assert branding_service.branding_config.logo.position == LogoPosition.TOP_LEFT
        assert branding_service.branding_config.logo.size == LogoSize.LARGE
    
    def test_configure_logo_invalid_file(self, branding_service):
        """Test logo configuration with invalid file"""
        success = branding_service.configure_logo("/nonexistent/logo.png")
        
        assert success is False
        assert branding_service.branding_config.logo.enabled is False
    
    def test_disable_logo(self, branding_service, temp_logo_dir):
        """Test disabling logo"""
        # First configure a logo
        logo_file = temp_logo_dir / "logo.png"
        self.create_test_logo(logo_file)
        branding_service.configure_logo(str(logo_file))
        
        # Then disable it
        branding_service.disable_logo()
        
        assert branding_service.branding_config.logo.enabled is False
    
    def test_update_branding(self, branding_service):
        """Test updating branding configuration"""
        branding_service.update_branding(
            organization_name="Test Organization",
            primary_color="#ff0000",
            secondary_color="#00ff00",
            font_family="Helvetica, sans-serif"
        )
        
        config = branding_service.branding_config
        assert config.organization_name == "Test Organization"
        assert config.primary_color == "#ff0000"
        assert config.secondary_color == "#00ff00"
        assert config.font_family == "Helvetica, sans-serif"
    
    def test_get_logo_data_disabled(self, branding_service):
        """Test getting logo data when logo is disabled"""
        logo_data = branding_service.get_logo_data()
        
        assert logo_data is None
    
    @patch.object(LogoProcessor, 'process_logo')
    def test_get_logo_data_enabled(self, mock_process, branding_service, temp_logo_dir):
        """Test getting logo data when logo is enabled"""
        # Configure logo
        logo_file = temp_logo_dir / "logo.png"
        self.create_test_logo(logo_file)
        branding_service.configure_logo(str(logo_file))
        
        # Mock processor response
        mock_process.return_value = {
            'format': 'png',
            'data': 'data:image/png;base64,test',
            'width': 200,
            'height': 100
        }
        
        logo_data = branding_service.get_logo_data()
        
        assert logo_data is not None
        assert logo_data['format'] == 'png'
        assert 'data' in logo_data
        mock_process.assert_called_once()
    
    def test_generate_report_css_no_logo(self, branding_service):
        """Test CSS generation without logo"""
        css = branding_service.generate_report_css()
        
        assert ":root" in css
        assert "--primary-color" in css
        assert "--font-family" in css
        assert ".report-header" in css
        # Should not contain logo-specific CSS
        assert ".report-logo" not in css
    
    @patch.object(ReportBrandingService, 'get_logo_data')
    def test_generate_report_css_with_logo(self, mock_get_logo, branding_service):
        """Test CSS generation with logo"""
        # Mock logo data
        mock_get_logo.return_value = {
            'format': 'png',
            'data': 'data:image/png;base64,test'
        }
        
        css = branding_service.generate_report_css()
        
        assert ":root" in css
        assert ".report-logo" in css
        assert "position: absolute" in css
    
    def test_get_branding_context_no_logo(self, branding_service):
        """Test getting branding context without logo"""
        context = branding_service.get_branding_context()
        
        assert "branding" in context
        branding = context["branding"]
        assert branding["has_logo"] is False
        assert branding["logo_data"] is None
        assert "primary_color" in branding
        assert "custom_css" in branding
    
    @patch.object(ReportBrandingService, 'get_logo_data')
    def test_get_branding_context_with_logo(self, mock_get_logo, branding_service, temp_logo_dir):
        """Test getting branding context with logo"""
        # Configure logo
        logo_file = temp_logo_dir / "logo.png"
        self.create_test_logo(logo_file)
        branding_service.configure_logo(str(logo_file))
        
        # Mock logo data
        mock_logo_data = {
            'format': 'png',
            'data': 'data:image/png;base64,test'
        }
        mock_get_logo.return_value = mock_logo_data
        
        context = branding_service.get_branding_context()
        
        branding = context["branding"]
        assert branding["has_logo"] is True
        assert branding["logo_data"] == mock_logo_data
    
    def test_configuration_persistence(self, temp_config_dir):
        """Test that configuration persists across service instances"""
        config_path = temp_config_dir / "branding.yaml"
        
        # Create first service instance and configure it
        service1 = ReportBrandingService(config_path)
        service1.update_branding(
            organization_name="Persistent Org",
            primary_color="#123456"
        )
        
        # Create second service instance and verify configuration persisted
        service2 = ReportBrandingService(config_path)
        
        assert service2.branding_config.organization_name == "Persistent Org"
        assert service2.branding_config.primary_color == "#123456"
    
    def test_reset_to_defaults(self, branding_service):
        """Test resetting configuration to defaults"""
        # First modify configuration
        branding_service.update_branding(
            organization_name="Test Org",
            primary_color="#ff0000"
        )
        
        # Then reset
        branding_service.reset_to_defaults()
        
        config = branding_service.branding_config
        assert config.organization_name is None
        assert config.primary_color == "#2c5aa0"  # Default color
        assert config.logo.enabled is False


class TestIntegrationScenarios:
    """Test integration scenarios and edge cases"""
    
    @pytest.fixture
    def temp_dirs(self):
        """Create temporary directories for testing"""
        config_dir = tempfile.mkdtemp()
        logo_dir = tempfile.mkdtemp()
        yield Path(config_dir), Path(logo_dir)
        shutil.rmtree(config_dir)
        shutil.rmtree(logo_dir)
    
    def test_report_without_logo_has_no_placeholders(self, temp_dirs):
        """Test that reports without logos have no visual placeholders"""
        config_dir, logo_dir = temp_dirs
        service = ReportBrandingService(config_dir / "branding.yaml")
        
        # Get branding context without logo
        context = service.get_branding_context()
        css = service.generate_report_css()
        
        # Verify no logo-related elements
        assert context["branding"]["has_logo"] is False
        assert context["branding"]["logo_data"] is None
        assert ".report-logo" not in css
        
        # CSS should still be complete and professional
        assert ":root" in css
        assert ".report-header" in css
        assert "font-family" in css
    
    def test_seamless_logo_addition_removal(self, temp_dirs):
        """Test seamless addition and removal of logos"""
        config_dir, logo_dir = temp_dirs
        service = ReportBrandingService(config_dir / "branding.yaml")
        
        # Create test logo
        logo_file = logo_dir / "logo.png"
        img = Image.new('RGBA', (100, 50), color=(255, 0, 0, 255))
        img.save(logo_file, format='PNG')
        
        # Initially no logo
        context1 = service.get_branding_context()
        assert context1["branding"]["has_logo"] is False
        
        # Add logo
        service.configure_logo(str(logo_file))
        context2 = service.get_branding_context()
        assert context2["branding"]["has_logo"] is True
        assert context2["branding"]["logo_data"] is not None
        
        # Remove logo
        service.disable_logo()
        context3 = service.get_branding_context()
        assert context3["branding"]["has_logo"] is False
        assert context3["branding"]["logo_data"] is None
    
    def test_corrupted_logo_file_handling(self, temp_dirs):
        """Test handling of corrupted logo files"""
        config_dir, logo_dir = temp_dirs
        service = ReportBrandingService(config_dir / "branding.yaml")
        
        # Create corrupted image file
        corrupted_file = logo_dir / "corrupted.png"
        corrupted_file.write_bytes(b"not a real image file")
        
        # Attempt to configure corrupted logo
        success = service.configure_logo(str(corrupted_file))
        
        assert success is False
        assert service.branding_config.logo.enabled is False
        
        # Service should still work normally
        context = service.get_branding_context()
        assert context["branding"]["has_logo"] is False


if __name__ == "__main__":
    pytest.main([__file__])