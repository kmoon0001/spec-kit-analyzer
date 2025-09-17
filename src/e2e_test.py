import unittest
import os
import json
from src.analyzer import run_analyzer

class E2ETest(unittest.TestCase):
    def test_run_analyzer_end_to_end(self):
        # Define the path to the test document
        test_file = 'test_data/good_note_1.txt'

        # Define the analysis parameters
        selected_disciplines = ['pt']

        # Run the analyzer
        results = run_analyzer(
            file_path=test_file,
            selected_disciplines=selected_disciplines
        )

        # Verify the results
        self.assertIsNotNone(results)
        self.assertIn('json', results)
        self.assertIn('pdf', results)
        self.assertIn('csv', results)

        # Check that the report files were created
        self.assertTrue(os.path.exists(results['json']))
        self.assertTrue(os.path.exists(results['pdf']))
        self.assertTrue(os.path.exists(results['csv']))

        # Load the JSON report and check its contents
        with open(results['json'], 'r') as f:
            report_data = json.load(f)

        self.assertIn('issues', report_data)
        self.assertIn('compliance', report_data)
        self.assertIsInstance(report_data['issues'], list)
        self.assertIsInstance(report_data['compliance']['score'], float)

        # Add more specific assertions
        self.assertGreater(report_data['compliance']['score'], 80)

        sev_counts = {
            "flag": sum(1 for i in report_data['issues'] if i.get("severity") == "flag"),
            "wobbler": sum(1 for i in report_data['issues'] if i.get("severity") == "wobbler"),
        }
        self.assertEqual(sev_counts['flag'], 0)
        self.assertEqual(sev_counts['wobbler'], 0)

    def test_run_analyzer_bad_note(self):
        # Define the path to the test document
        test_file = 'test_data/bad_note_1.txt'

        # Define the analysis parameters
        selected_disciplines = ['pt']

        # Run the analyzer
        results = run_analyzer(
            file_path=test_file,
            selected_disciplines=selected_disciplines,
            review_mode_override="Strict"
        )

        # Verify the results
        self.assertIsNotNone(results)

        # Load the JSON report and check its contents
        with open(results['json'], 'r') as f:
            report_data = json.load(f)

        self.assertLess(report_data['compliance']['score'], 100)

        sev_counts = {
            "flag": sum(1 for i in report_data['issues'] if i.get("severity") == "flag"),
        }
        self.assertGreater(sev_counts['flag'], 0)

if __name__ == '__main__':
    unittest.main()
