
import sys
from pathlib import Path

# Add the project root to the Python path
project_root = Path(__file__).resolve().parent.parent.parent
sys.path.append(str(project_root))

from kivy.app import App
from src.gui_kivy.main_window_kivy import MainWindow

class TherapyComplianceApp(App):
    """Main Kivy application class."""
    def build(self):
        """Build the Kivy UI."""
        return MainWindow()

def main():
    """Main function to run the Kivy application."""
    app = TherapyComplianceApp()
    app.run()

if __name__ == "__main__":
    main()
