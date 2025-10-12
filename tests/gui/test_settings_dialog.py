from __future__ import annotations

import pytest
from PySide6.QtCore import QSettings
from PySide6.QtWidgets import QMessageBox

from src.gui.dialogs.settings_dialog import SettingsDialog


@pytest.fixture
def temp_settings(tmp_path) -> QSettings:
    settings_path = tmp_path / "settings.ini"
    qsettings = QSettings(str(settings_path), QSettings.Format.IniFormat)
    qsettings.clear()
    return qsettings


def test_settings_dialog_apply_settings_persists_values(qtbot, temp_settings, monkeypatch):
    monkeypatch.setattr(
        "src.gui.dialogs.settings_dialog.QMessageBox.information",
        lambda *args, **kwargs: QMessageBox.StandardButton.Ok,
    )

    dialog = SettingsDialog(settings=temp_settings)
    qtbot.addWidget(dialog)

    dialog.strict_mode_checkbox.setChecked(True)
    dialog.sensitivity_slider.setValue(7)
    dialog.confidence_threshold_spinbox.setValue(80)
    dialog.enable_fact_checking_checkbox.setChecked(False)
    dialog.use_gpu_checkbox.setChecked(True)
    dialog.max_workers_spinbox.setValue(4)
    dialog.cache_size_spinbox.setValue(512)
    dialog.watch_folder_enabled_checkbox.setChecked(True)
    dialog.watch_folder_path_edit.setText("/tmp/watch")
    dialog.scan_interval_spinbox.setValue(15)
    dialog.auto_export_checkbox.setChecked(True)
    dialog.auto_export_format_combo.setCurrentText("PDF")
    dialog.enable_phi_scrubbing_checkbox.setChecked(False)
    dialog.phi_confidence_spinbox.setValue(70)
    dialog.theme_combo.setCurrentText("Dark")
    dialog.font_size_spinbox.setValue(16)
    dialog.show_completion_notifications_checkbox.setChecked(False)

    dialog.apply_settings()
    temp_settings.sync()

    assert temp_settings.value("analysis/strict_mode", type=bool) is True
    assert temp_settings.value("analysis/sensitivity", type=int) == 7
    assert temp_settings.value("performance/use_gpu", type=bool) is True
    assert temp_settings.value("automation/watch_folder_path", type=str) == "/tmp/watch"
    assert temp_settings.value("privacy/phi_confidence", type=int) == 70
    assert temp_settings.value("interface/theme", type=str) == "Dark"
    assert temp_settings.value("interface/show_notifications", type=bool) is False


def test_settings_dialog_load_settings_populates_fields(qtbot, temp_settings):
    temp_settings.setValue("analysis/strict_mode", True)
    temp_settings.setValue("analysis/sensitivity", 9)
    temp_settings.setValue("performance/use_gpu", True)
    temp_settings.setValue("automation/watch_folder_enabled", True)
    temp_settings.setValue("automation/watch_folder_path", "C:/data")
    temp_settings.setValue("privacy/enable_phi_scrubbing", False)
    temp_settings.setValue("interface/theme", "Dark")
    temp_settings.sync()

    dialog = SettingsDialog(settings=temp_settings)
    qtbot.addWidget(dialog)

    assert dialog.strict_mode_checkbox.isChecked() is True
    assert dialog.sensitivity_slider.value() == 9
    assert dialog.use_gpu_checkbox.isChecked() is True
    assert dialog.watch_folder_enabled_checkbox.isChecked() is True
    assert dialog.watch_folder_path_edit.text() == "C:/data"
    assert dialog.enable_phi_scrubbing_checkbox.isChecked() is False
    assert dialog.theme_combo.currentText() == "Dark"


def test_settings_dialog_clear_cache(monkeypatch, qtbot, temp_settings):
    class DummyCache:
        def __init__(self):
            self.cleared = False

        def clear_disk_cache(self):
            self.cleared = True

    dummy_cache = DummyCache()

    monkeypatch.setattr(
        "src.gui.dialogs.settings_dialog.QMessageBox.question",
        lambda *args, **kwargs: QMessageBox.StandardButton.Yes,
    )
    monkeypatch.setattr(
        "src.gui.dialogs.settings_dialog.QMessageBox.information",
        lambda *args, **kwargs: QMessageBox.StandardButton.Ok,
    )

    dialog = SettingsDialog(settings=temp_settings, cache_service_override=dummy_cache)
    qtbot.addWidget(dialog)

    dialog.clear_cache()

    assert dummy_cache.cleared is True
