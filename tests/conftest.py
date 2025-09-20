# import pytest
# from PyQt6.QtWidgets import QApplication
# import logging
#
# logger = logging.getLogger(__name__)
#
# @pytest.fixture(scope="session")
# def qapp():
#     """
#     Session-scoped fixture to create a single QApplication instance for the entire test run.
#     This is a standard practice for pytest-qt tests to avoid creating a new application
#     for every test, which can be slow and resource-intensive.
#     """
#     logging.warning(">>> qapp fixture started")
#     app = QApplication.instance()
#     if app is None:
#         logging.warning(">>> QApplication instance is None, creating a new one.")
#         app = QApplication([])
#     else:
#         logging.warning(">>> QApplication instance already exists.")
#     logging.warning(">>> qapp fixture finished")
#     return app
