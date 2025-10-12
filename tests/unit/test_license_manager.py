from __future__ import annotations

import json

from src.core.license_manager import LicenseManager


def _stub_fingerprint() -> str:
    return "ABCDEF12"


def test_check_license_status_recovers_from_corrupted_file(tmp_path, monkeypatch):
    manager = LicenseManager()
    manager.license_file = tmp_path / "license.dat"
    monkeypatch.setattr(manager, "get_hardware_fingerprint", _stub_fingerprint)

    assert manager.initialize_trial(force=True) is True

    payload = json.loads(manager.license_file.read_text(encoding="utf-8"))
    payload["data"] = "00" + payload["data"][2:]
    manager.license_file.write_text(json.dumps(payload), encoding="utf-8")

    is_valid, message, days_remaining = manager.check_license_status()

    assert is_valid is True
    assert "reset" in message.lower()
    assert days_remaining == manager.trial_days

    second_valid, _, _ = manager.check_license_status()
    assert second_valid is True
