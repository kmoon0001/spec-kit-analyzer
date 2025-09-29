"""
Dialog for the supervisor's Review Dashboard.
"""
import logging
from PyQt6.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QListWidget,
    QListWidgetItem,
    QPushButton,
    QDialogButtonBox,
    QLabel,
    QMessageBox,
)
from PyQt6.QtCore import QThread, Qt
from typing import List, Dict, Any

from ..workers.review_dashboard_worker import ReviewDashboardWorker
# from .review_detail_dialog import ReviewDetailDialog # To be created

logger = logging.getLogger(__name__)

class ReviewDashboardDialog(QDialog):
    """
    A dialog that displays a list of reports pending review for a supervisor.
    """
    def __init__(self, token: str, parent=None):
        super().__init__(parent)
        self.token = token
        self.setWindowTitle("Supervisor Review Dashboard")
        self.setMinimumSize(600, 500)
        self._init_ui()
        self.fetch_pending_reviews()

    def _init_ui(self):
        """Initialize the user interface."""
        main_layout = QVBoxLayout(self)

        title_label = QLabel("Reports Pending Review")
        title_label.setStyleSheet("font-size: 16px; font-weight: bold;")
        main_layout.addWidget(title_label)

        self.review_list_widget = QListWidget()
        self.review_list_widget.itemDoubleClicked.connect(self.open_review_detail)
        main_layout.addWidget(self.review_list_widget)

        button_box = QDialogButtonBox(QDialogButtonBox.StandardButton.Close)
        button_box.rejected.connect(self.reject)
        main_layout.addWidget(button_box)

    def fetch_pending_reviews(self):
        """Fetches the list of pending reviews from the API."""
        self.review_list_widget.clear()
        self.review_list_widget.addItem("Fetching reviews...")

        self.worker_thread = QThread()
        self.worker = ReviewDashboardWorker(self.token)
        self.worker.moveToThread(self.worker_thread)

        self.worker.success.connect(self.on_fetch_success)
        self.worker.error.connect(self.on_fetch_error)
        self.worker.finished.connect(self.worker_thread.quit)
        self.worker.finished.connect(self.worker.deleteLater)
        self.worker_thread.finished.connect(self.worker_thread.deleteLater)

        self.worker_thread.started.connect(self.worker.run)
        self.worker_thread.start()

    def on_fetch_success(self, reviews: List[Dict[str, Any]]):
        """Populates the list widget with pending reviews."""
        self.review_list_widget.clear()
        if not reviews:
            self.review_list_widget.addItem("No reviews are currently pending.")
            return

        for review in reviews:
            report = review.get("report", {})
            author = review.get("author", {})
            item_text = (
                f"Report: {report.get('document_name', 'N/A')} "
                f"(Author: {author.get('username', 'N/A')})"
            )
            list_item = QListWidgetItem(item_text)
            list_item.setData(Qt.ItemDataRole.UserRole, review) # Store the full review data
            self.review_list_widget.addItem(list_item)

    def on_fetch_error(self, error_message: str):
        """Handles errors during the fetch process."""
        self.review_list_widget.clear()
        self.review_list_widget.addItem(f"Error fetching reviews: {error_message}")
        QMessageBox.critical(self, "Error", f"Could not fetch pending reviews:\n{error_message}")

    def open_review_detail(self, item: QListWidgetItem):
        """Opens the detailed view for the selected review."""
        review_data = item.data(Qt.ItemDataRole.UserRole)
        if not review_data:
            return

        QMessageBox.information(self, "Coming Soon", f"This will open the detail view for review ID: {review_data.get('id')}")
        # TODO: Implement the ReviewDetailDialog
        # detail_dialog = ReviewDetailDialog(review_data, self.token, self)
        # detail_dialog.exec()
        # self.fetch_pending_reviews() # Refresh list after a review is handled