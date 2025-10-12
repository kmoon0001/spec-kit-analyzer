
from kivy.uix.boxlayout import BoxLayout
from kivy.properties import StringProperty, ObjectProperty

from src.gui.view_models.main_view_model import MainViewModel

class MainWindow(BoxLayout):
    """The main application window (View)."""
    status_text = StringProperty("Ready")
    view_model = ObjectProperty(None)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # For now, use a dummy token. This will be replaced by the login flow.
        dummy_token = "dummy_token"
        self.view_model = MainViewModel(token=dummy_token)
        
        # Connect ViewModel signals to Kivy properties/methods
        self.view_model.status_message_changed.connect(self.on_status_message_changed)
        
        # Start the view model's background workers
        self.view_model.start_workers()

    def on_status_message_changed(self, message):
        """Callback for when the status message changes in the ViewModel."""
        self.status_text = message

