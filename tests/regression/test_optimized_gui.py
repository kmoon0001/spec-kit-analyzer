# This file has been disabled because it is a manual testing script that was
# causing pytest collection errors due to a missing import.
# The original content has been commented out to preserve it for future reference.

# #!/usr/bin/env python3
# """
# Test script for the optimized GUI implementation.
# """
# 
# import sys
# from pathlib import Path
# import asyncio
# from PySide6.QtWidgets import QApplication
# 
# # Add project root to the Python path
# sys.path.insert(0, str(Path(__file__).resolve().parent))
# 
# from src.gui.main_window_optimized import OptimizedMainWindow
# from src.database import init_db
# 
# def main():
#     """Test the optimized main window."""
#     print("🧪 Testing Optimized GUI Implementation")
#     print("=" * 50)
#     
#     try:
#         # Initialize the database first
#         asyncio.run(init_db())
#         print("✅ Database initialized")
#         
#         # Create and run the application
#         app = QApplication(sys.argv)
#         print("✅ QApplication created")
#         
#         main_win = OptimizedMainWindow()
#         print("✅ OptimizedMainWindow created")
#         
#         main_win.start()
#         print("✅ Application started")
#         
#         print("\n🎉 SUCCESS! Optimized GUI is working.")
#         print("\nFeatures to test:")
#         print("- Theme toggle (sun/moon button in header)")
#         print("- Document upload and analysis")
#         print("- AI status indicators")
#         print("- Component-based architecture")
#         
#         sys.exit(app.exec())
#         
#     except Exception as e:
#         print(f"❌ ERROR: {str(e)}")
#         import traceback
#         traceback.print_exc()
#         return 1
# 
# if __name__ == "__main__":
#     main()
