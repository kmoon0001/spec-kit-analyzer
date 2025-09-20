# Python
import os
import tempfile
import shutil
import unittest

import importlib

# Import the module under test
import main as app


class CoreTests(unittest.TestCase):
    def setUp(self):
        # Use a temp reports dir for tests
        self.tmpdir = tempfile.mkdtemp(prefix="reports_")
        app.set_setting("reports_dir", self.tmpdir)
        # Reset date/counter to a known state
        try:
            app.set_setting("last_report_date", "01012000")
        except Exception:
            pass
        app.set_setting("report_counter", "1")

    def tearDown(self):
        shutil.rmtree(self.tmpdir, ignore_errors=True)

    def test_settings_roundtrip(self):
        app.set_setting("probe_host", "8.8.8.8")
        self.assertEqual(app.get_setting("probe_host"), "8.8.8.8")

    def test_daily_counter_reset_and_increment(self):
        # First call -> 1, second same day -> 2
        p1, c1 = app.generate_report_paths()
        p2, c2 = app.generate_report_paths()
        self.assertNotEqual(os.path.basename(p1), os.path.basename(p2))
        # Force "new day" by changing last_report_date to a day prior
        app.set_setting("last_report_date", "01012000")
        p3, c3 = app.generate_report_paths()
        self.assertNotEqual(os.path.basename(p2), os.path.basename(p3))
        # ensure counter reset to 1 pattern
        self.assertIn("report1.pdf", p3)

    def test_export_pdf_and_csv(self):
        report = "Line1\nLine2\n"
        rows = [{"rule": "R1", "status": "MET", "match": "M", "score": 0.9, "source": "S"}]
        pdf, csv = app.generate_report_paths()
        ok_pdf = app.export_report_pdf(report, pdf)
        ok_csv = app.export_report_csv(rows, csv)
        self.assertTrue(ok_pdf and os.path.isfile(pdf))
        self.assertTrue(ok_csv and os.path.isfile(csv))

    def test_admin_password_set_and_verify(self):
        self.assertTrue(app._set_admin_password("secret123"))
        self.assertTrue(app._verify_admin_password("secret123"))
        self.assertFalse(app._verify_admin_password("wrong"))

    def test_toggle_offline_requires_password(self):
        app._set_admin_password("adminpw")
        self.assertFalse(app._set_offline_only(True, "badpw"))
        self.assertTrue(app._set_offline_only(True, "adminpw"))
        self.assertTrue(app._get_offline_only())


if __name__ == "__main__":
    unittest.main()