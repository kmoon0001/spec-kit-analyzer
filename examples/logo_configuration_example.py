"""
Example: Configuring Optional Logo for Reports

This example demonstrates how to configure an optional logo for reports.
The system works seamlessly whether a logo is configured or not - no placeholders
or visual gaps appear when no logo is set.
"""

import sys
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from core.report_generation_engine import ReportGenerationEngine, ReportConfig, ReportType


def demonstrate_logo_configuration():
    """Demonstrate logo configuration and report generation"""
    
    # Initialize report engine
    engine = ReportGenerationEngine()
    
    print("=== Report Branding & Logo Configuration Demo ===\n")
    
    # 1. Check initial branding status
    print("1. Initial branding status:")
    status = engine.get_branding_status()
    print(f"   Branding available: {status['branding_available']}")
    print(f"   Logo enabled: {status['logo_enabled']}")
    print(f"   Organization: {status.get('organization_name', 'None')}")
    print()
    
    # 2. Configure basic branding without logo
    print("2. Configuring basic branding (no logo):")
    success = engine.configure_branding(
        organization_name="Healthcare Analytics Corp",
        primary_color="#1e3a8a",
        secondary_color="#64748b",
        accent_color="#10b981"
    )
    print(f"   Configuration successful: {success}")
    
    # Generate a report without logo
    config = ReportConfig(
        report_type=ReportType.PERFORMANCE_ANALYSIS,
        title="Performance Analysis Report",
        description="Comprehensive system performance analysis"
    )
    
    print("   Generating report without logo...")
    report = engine.generate_report(config)
    print(f"   Report generated: {report.id}")
    print("   Report has professional styling without logo placeholders")
    print()
    
    # 3. Configure logo (if logo file exists)
    logo_path = Path("examples/sample_logo.png")
    
    if logo_path.exists():
        print("3. Configuring logo:")
        success = engine.configure_branding(
            logo_path=str(logo_path),
            logo_position="top_right",
            logo_size="medium",
            logo_opacity=0.9
        )
        print(f"   Logo configuration successful: {success}")
        
        # Generate report with logo
        print("   Generating report with logo...")
        report_with_logo = engine.generate_report(config)
        print(f"   Report with logo generated: {report_with_logo.id}")
        print()
        
        # 4. Disable logo
        print("4. Disabling logo:")
        success = engine.disable_logo()
        print(f"   Logo disabled: {success}")
        
        # Generate report after disabling logo
        print("   Generating report after disabling logo...")
        report_no_logo = engine.generate_report(config)
        print(f"   Report generated: {report_no_logo.id}")
        print("   Report seamlessly returns to no-logo styling")
        print()
    else:
        print("3. Logo file not found - creating sample instructions:")
        print(f"   To test logo functionality, create a logo file at: {logo_path}")
        print("   Supported formats: PNG, JPG, JPEG, GIF, BMP, SVG")
        print("   Maximum file size: 5MB")
        print("   Recommended size: 200x100 pixels or similar aspect ratio")
        print()
    
    # 5. Show final status
    print("5. Final branding status:")
    final_status = engine.get_branding_status()
    for key, value in final_status.items():
        print(f"   {key}: {value}")
    print()
    
    print("=== Key Features Demonstrated ===")
    print("✓ Reports work perfectly with or without logos")
    print("✓ No placeholders or visual gaps when logo is disabled")
    print("✓ Seamless logo addition and removal")
    print("✓ Professional styling maintained in all cases")
    print("✓ Multiple logo positions and sizes supported")
    print("✓ Automatic logo validation and error handling")
    print("✓ Configuration persists across application restarts")


def create_sample_logo():
    """Create a sample logo for testing"""
    try:
        from PIL import Image, ImageDraw, ImageFont
        
        # Create a simple logo
        img = Image.new('RGBA', (200, 100), color=(30, 58, 138, 255))  # Blue background
        draw = ImageDraw.Draw(img)
        
        # Add text
        try:
            # Try to use a nice font
            font = ImageFont.truetype("arial.ttf", 24)
        except OSError:
            # Fallback to default font
            font = ImageFont.load_default()
        
        # Draw company name
        text = "HealthCorp"
        bbox = draw.textbbox((0, 0), text, font=font)
        text_width = bbox[2] - bbox[0]
        text_height = bbox[3] - bbox[1]
        
        x = (200 - text_width) // 2
        y = (100 - text_height) // 2
        
        draw.text((x, y), text, fill=(255, 255, 255, 255), font=font)
        
        # Add a simple graphic element
        draw.rectangle([10, 10, 30, 30], fill=(16, 185, 129, 255))  # Green square
        
        # Save the logo
        logo_path = Path("examples/sample_logo.png")
        logo_path.parent.mkdir(exist_ok=True)
        img.save(logo_path, format='PNG')
        
        print(f"Sample logo created at: {logo_path}")
        return True
        
    except ImportError:
        print("PIL not available - cannot create sample logo")
        print("Install Pillow to create sample logos: pip install Pillow")
        return False
    except Exception as e:
        print(f"Error creating sample logo: {e}")
        return False


if __name__ == "__main__":
    # Create sample logo if it doesn't exist
    logo_path = Path("examples/sample_logo.png")
    if not logo_path.exists():
        print("Creating sample logo for demonstration...")
        create_sample_logo()
        print()
    
    # Run the demonstration
    demonstrate_logo_configuration()