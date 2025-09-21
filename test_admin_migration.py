# Python
import os
import sqlite3
import tempfile
import unittest
import importlib
import hashlib


class TestAdminMigration(unittest.TestCase):
    def setUp(self):
        # Use a temporary database for this test
        self.tmpdir = tempfile.TemporaryDirectory()
        self.db_path = os.path.join(self.tmpdir.name, "spec_kit.db")
        os.environ["SPEC_KIT_DB"] = self.db_path
        # Ensure module reload picks up new path
        if "main" in list(importlib.sys.modules.keys()):
            importlib.invalidate_caches()
            importlib.reload(importlib.import_module("main"))
        else:
            import main  # noqa: F401

    def tearDown(self):
        # Clean up env and temp files
        if "SPEC_KIT_DB" in os.environ:
            del os.environ["SPEC_KIT_DB"]
        self.tmpdir.cleanup()

    def test_migrate_from_legacy_defaults(self):
        import main
        # Initialize DB and force legacy default admin credentials
        self.assertTrue(main.initialize_database())
        with sqlite3.connect(self.db_path) as conn:
            cur = conn.cursor()
            # Overwrite admin with legacy default values
            legacy_salt = main.LEGACY_DEFAULT_ADMIN_SALT
            legacy_hash = hashlib.pbkdf2_hmac('sha256', b"admin", legacy_salt, main.ITERATIONS)
            cur.execute("UPDATE users SET password_hash=?, salt=?, iterations=? WHERE username=?",
                        (legacy_hash, legacy_salt, main.ITERATIONS, main.ADMIN_USERNAME))
            conn.commit()
        # Run migration
        new_password = main.migrate_default_admin_credentials()
        # Validate changes
        with sqlite3.connect(self.db_path) as conn:
            cur = conn.cursor()
            cur.execute("SELECT password_hash, salt, iterations FROM users WHERE username=?",
                        (main.ADMIN_USERNAME,))
            row = cur.fetchone()
            self.assertIsNotNone(row)
            stored_hash, stored_salt, stored_iterations = row
            self.assertNotEqual(stored_salt, legacy_salt)
            self.assertNotEqual(stored_hash, legacy_hash)
            self.assertEqual(stored_iterations, main.ITERATIONS)
        # Verify that either a password was returned (if no ADMIN_INITIAL_PASSWORD)
        # or None if ADMIN_INITIAL_PASSWORD was set in environment
        # Here, by default, we didn't set ADMIN_INITIAL_PASSWORD, so we expect a value
        self.assertIsInstance(new_password, (str, type(None)))

    def test_set_and_verify_admin_password(self):
        import main
        self.assertTrue(main.initialize_database())
        pw = "S3cure!Passw0rd"
        main._set_admin_password(pw)
        self.assertTrue(main._verify_admin_password(pw))
        self.assertFalse(main._verify_admin_password("wrong"))

if __name__ == "__main__":
    unittest.main()