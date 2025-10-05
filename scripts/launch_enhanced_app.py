#!/usr/bin/env python3
"""
🏥 Therapy Compliance Analyzer - Enhanced Edition Launcher
Launch the fully integrated application with all features
"""

import sys
from pathlib import Path
import asyncio

# Add project root to path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

def main():
    """Launch the enhanced application"""
    print("🏥 Therapy Compliance Analyzer - Enhanced Edition")
    print("=" * 50)
    print("🚀 Starting application with all features...")
    
    try:
        # Import required modules
        from PySide6.QtWidgets import QApplication
        from src.gui.main_window import MainApplicationWindow
        from src.database import init_db
        
        # Initialize database
        print("📊 Initializing database...")
        asyncio.run(init_db())
        print("✅ Database ready")
        
        # Create application
        print("🎨 Creating application...")
        app = QApplication(sys.argv)
        app.setApplicationName("Therapy Compliance Analyzer")
        app.setApplicationVersion("2.0 Enhanced")
        app.setOrganizationName("Healthcare AI Solutions")
        
        # Create main window
        print("🖥️ Loading enhanced interface...")
        main_window = MainApplicationWindow()
        
        # Show welcome message
        print("\n🎉 Application Ready!")
        print("✨ Features Available:")
        print("   • 📱 Modern tabbed interface")
        print("   • 🎨 4 beautiful themes (Light, Dark, Medical, Nature)")
        print("   • 🤖 AI-powered document analysis")
        print("   • 💬 Interactive chat assistant")
        print("   • 📊 Analytics dashboard")
        print("   • ⚙️ Comprehensive settings")
        print("   • 🎯 Hidden easter eggs (try clicking the logo 7 times!)")
        print("   • 🔧 Developer mode (Konami code: ↑↑↓↓←→←→BA)")
        print("   • 📋 Drag & drop document upload")
        print("   • ⌨️ Keyboard shortcuts (Ctrl+O, F5, Ctrl+T, etc.)")
        print("   • 🔔 System tray integration")
        print("   • 🎪 Floating action button")
        
        print("\n🎮 Try These Features:")
        print("   1. 📤 Upload a document (Ctrl+O)")
        print("   2. 🎨 Switch themes (Theme menu)")
        print("   3. 💬 Open chat assistant (💬 button or Ctrl+T)")
        print("   4. 📊 View dashboard (Dashboard tab)")
        print("   5. ⚙️ Explore settings (Settings tab)")
        print("   6. 🎯 Find easter eggs!")
        
        print("\n🚀 Launching GUI...")
        
        # Start the application
        main_window.start()
        
        # Run the event loop
        sys.exit(app.exec())
        
    except ImportError as e:
        print(f"❌ Import Error: {e}")
        print("💡 Make sure all dependencies are installed:")
        print("   pip install -r requirements.txt")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()