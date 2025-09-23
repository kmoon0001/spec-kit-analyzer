# Python
import os
import re
import tempfile
import time
import shutil
import unittest

# Ensure we import main after environment is set if needed.
from src import main

 
class TestHelpers(unittest.TestCase):
    def test_scrub_phi(self):
        text = "SSN 123-45-6789, Phone (555) 123-4567, Email a@b.com, Date 01/23/2024, MRN 1234567"
        red = main.scrub_phi(text)
        self.assertIn("[SSN]", red)
        self.assertIn("[PHONE]", red)
        self.assertIn("[EMAIL]", red)
        self.assertIn("[DATE]", red)
        self.assertIn("[MRN]", red)

    def test_generate_report_paths_format(self):
        pdf, csv = main.generate_report_paths()
        self.assertTrue(re.match(r".*/\d{8}report\d+\.pdf$", pdf.replace("\\", "/")))
        self.assertTrue(re.match(r".*/\d{8}report\d+\.csv$", csv.replace("\\", "/")))

    def test_purge_old_reports_safety(self):
        tmp = tempfile.mkdtemp()
        try:
            old_report = os.path.join(tmp, "01012025report1.pdf")
            new_report = os.path.join(tmp, "01012025report2.pdf")
            other_pdf = os.path.join(tmp, "unrelated.pdf")
            for p in (old_report, new_report, other_pdf):
                with open(p, "wb") as f:
                    f.write(b"%PDF-1.4")
            cutoff = time.time() - (main.REPORT_RETENTION_HOURS * main.SECONDS_PER_HOUR) - 100
            os.utime(old_report, (cutoff, cutoff))
            prev = main.REPORTS_DIR
            main.REPORTS_DIR = tmp
            try:
                # Without marker, nothing should be deleted
                main.purge_old_reports()
                self.assertTrue(os.path.exists(old_report))
                self.assertTrue(os.path.exists(new_report))
                self.assertTrue(os.path.exists(other_pdf))
                # With marker, only matching old report should be deleted
                with open(os.path.join(tmp, ".spec_kit_reports"), "w") as m:
                    m.write("marker")
                main.purge_old_reports()
                self.assertFalse(os.path.exists(old_report))
                self.assertTrue(os.path.exists(new_report))
                self.assertTrue(os.path.exists(other_pdf))
            finally:
                main.REPORTS_DIR = prev
        finally:
            shutil.rmtree(tmp, ignore_errors=True)

    def test_internet_check_cache(self):
        v1 = main.is_internet_available()
        v2 = main.is_internet_available()
        self.assertIsInstance(v1, bool)
        self.assertEqual(v1, v2)


if __name__ == "__main__":
    unittest.main()
