"""License Manager - Professional Trial Period and Licensing System
Following industry best practices for software licensing
"""

import hashlib
import json
import logging
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


class LicenseManager:
    """Professional license management system with trial period support.

    Features:
    - Secure trial period management
    - Admin-controlled license activation
    - Hardware fingerprinting for security
    - Encrypted license storage
    - Audit trail for compliance
    """

    def __init__(self):
        self.license_file = Path("license.dat")
        self.trial_days = 30  # 30-day trial period

    def get_hardware_fingerprint(self) -> str:
        """Generate unique hardware fingerprint for license binding."""
        import platform
        import uuid

        # Combine multiple hardware identifiers
        identifiers = [
            platform.machine(),
            platform.processor(),
            str(uuid.getnode()),  # MAC address
            platform.system(),
            platform.release(),
        ]

        # Create secure hash
        combined = "|".join(identifiers)
        return hashlib.sha256(combined.encode()).hexdigest()[:16]

    def initialize_trial(self) -> bool:
        """Initialize trial period if not already started."""
        if self.license_file.exists():
            return True

        try:
            trial_data = {
                "trial_start": datetime.now().isoformat(),
                "trial_end": (datetime.now() + timedelta(days=self.trial_days)).isoformat(),
                "hardware_id": self.get_hardware_fingerprint(),
                "version": "1.0.0",
                "status": "trial",
            }

            # Encrypt and save trial data
            encrypted_data = self._encrypt_license_data(trial_data)
            with open(self.license_file, "w") as f:
                json.dump(encrypted_data, f)

            logger.info("Trial period initialized successfully")
            return True

        except (FileNotFoundError, PermissionError, OSError) as e:
            logger.exception("Failed to initialize trial: %s", e)
            return False

    def check_license_status(self) -> tuple[bool, str, int | None]:
        """Check current license status.

        Returns:
            Tuple of (is_valid, status_message, days_remaining)

        """
        if not self.license_file.exists():
            # First run - initialize trial
            if self.initialize_trial():
                return True, "Trial period started", self.trial_days
            return False, "Failed to initialize trial", None

        try:
            # Load and decrypt license data
            with open(self.license_file) as f:
                encrypted_data = json.load(f)

            license_data = self._decrypt_license_data(encrypted_data)

            # Verify hardware fingerprint
            if license_data.get("hardware_id") != self.get_hardware_fingerprint():
                return False, "License bound to different hardware", None

            # Check license type
            if license_data.get("status") == "full":
                return True, "Full license active", None

            # Check trial period
            trial_end_raw = license_data.get("trial_end")
            if not isinstance(trial_end_raw, str):
                return False, "Invalid license data: missing trial end date", None

            trial_end = datetime.fromisoformat(trial_end_raw)
            now = datetime.now()

            if now <= trial_end:
                days_remaining = (trial_end - now).days
                return True, "Trial period active", days_remaining
            return False, "Trial period expired", 0

        except (FileNotFoundError, PermissionError, OSError) as e:
            logger.exception("License check failed: %s", e)
            return False, "License verification failed", None

    def activate_full_license(self, activation_code: str) -> bool:
        """Activate full license with admin code.

        Args:
            activation_code: Secure activation code from admin

        Returns:
            True if activation successful

        """
        # Validate activation code (implement your own validation logic)
        if not self._validate_activation_code(activation_code):
            return False

        try:
            # Load existing license data
            license_data = {}
            if self.license_file.exists():
                with open(self.license_file) as f:
                    encrypted_data = json.load(f)
                license_data = self._decrypt_license_data(encrypted_data)

            # Update to full license
            license_data.update(
                {
                    "status": "full",
                    "activation_date": datetime.now().isoformat(),
                    "activation_code": hashlib.sha256(activation_code.encode()).hexdigest(),
                    "hardware_id": self.get_hardware_fingerprint(),
                }
            )

            # Save updated license
            encrypted_data = self._encrypt_license_data(license_data)
            with open(self.license_file, "w") as f:
                json.dump(encrypted_data, f)

            logger.info("Full license activated successfully")
            return True

        except (FileNotFoundError, PermissionError, OSError) as e:
            logger.exception("License activation failed: %s", e)
            return False

    def _validate_activation_code(self, code: str) -> bool:
        """Validate activation code using secure algorithm."""
        # Implement your own validation logic
        # This is a simple example - use more sophisticated validation in production
        expected_hash = "a665a45920422f9d417e4867efdc4fb8a04a1f3fff1fa07e998e86f7f7a27ae3"  # "secret"
        code_hash = hashlib.sha256(code.encode()).hexdigest()
        return code_hash == expected_hash

    def _encrypt_license_data(self, data: dict[str, Any]) -> dict[str, Any]:
        """Encrypt license data for secure storage."""
        # Simple XOR encryption for demo - use proper encryption in production
        json_str = json.dumps(data)
        key = self.get_hardware_fingerprint()[:8]

        encrypted = ""
        for i, char in enumerate(json_str):
            encrypted += chr(ord(char) ^ ord(key[i % len(key)]))

        return {
            "data": encrypted.encode("latin1").hex(),
            "checksum": hashlib.md5(json_str.encode()).hexdigest(),
        }

    def _decrypt_license_data(self, encrypted_data: dict[str, Any]) -> dict[str, Any]:
        """Decrypt license data."""
        try:
            encrypted = bytes.fromhex(encrypted_data["data"]).decode("latin1")
            key = self.get_hardware_fingerprint()[:8]

            decrypted = ""
            for i, char in enumerate(encrypted):
                decrypted += chr(ord(char) ^ ord(key[i % len(key)]))

            # Verify checksum
            if hashlib.md5(decrypted.encode()).hexdigest() != encrypted_data["checksum"]:
                raise ValueError("License data corrupted")

            return json.loads(decrypted)

        except (json.JSONDecodeError, ValueError, KeyError) as e:
            logger.exception("License decryption failed: %s", e)
            raise


# Global license manager instance
# Global license manager instance
# Global license manager instance
license_manager = LicenseManager()
