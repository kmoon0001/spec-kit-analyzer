import unittest
import sqlite3
import os
from unittest.mock import patch, MagicMock

# Add src to path to allow direct import of main
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'src')))

# Mock heavy dependencies for headless testing
sys.modules['PyQt6.QtWidgets'] = MagicMock()
sys.modules['PyQt6.QtGui'] = MagicMock()
sys.modules['PyQt6.QtCore'] = MagicMock()
sys.modules['matplotlib.backends.backend_qtagg'] = MagicMock()
sys.modules['src.ui_components'] = MagicMock()
sys.modules['src.local_llm'] = MagicMock()
sys.modules['src.rubric_service'] = MagicMock()
sys.modules['src.guideline_service'] = MagicMock()
sys.modules['pdfplumber'] = MagicMock()
sys.modules['pytesseract'] = MagicMock()
sys.modules['transformers'] = MagicMock()
sys.modules['PIL'] = MagicMock()
sys.modules['shap'] = MagicMock()
sys.modules['fhir.resources.bundle'] = MagicMock()
sys.modules['fhir.resources.diagnosticreport'] = MagicMock()
sys.modules['fhir.resources.observation'] = MagicMock()
sys.modules['fhir.resources.codeableconcept'] = MagicMock()
sys.modules['fhir.resources.coding'] = MagicMock()
sys.modules['fhir.resources.reference'] = MagicMock()
sys.modules['fhir.resources.meta'] = MagicMock()


from main import (
    _ensure_analytics_schema,
    persist_analysis_run,
    run_analyzer,
    compute_compliance_score,
)

DB_PATH = ":memory:"

class TestAnalyticsDB(unittest.TestCase):

    def setUp(self):
        """Set up a temporary in-memory database for each test."""
        # Use a real sqlite3 connection that can be passed to the functions
        self.conn = sqlite3.connect(DB_PATH)
        # Simulate the pre-migration state of the database
        cur = self.conn.cursor()
        cur.execute("""
            CREATE TABLE IF NOT EXISTS analysis_runs
            (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                file_name TEXT NOT NULL,
                run_time TEXT NOT NULL,
                pages_est INTEGER,
                flags INTEGER,
                wobblers INTEGER,
                suggestions INTEGER,
                notes INTEGER,
                sentences_final INTEGER,
                dedup_removed INTEGER,
                compliance_score REAL,
                mode TEXT
            )
        """)
        self.conn.commit()

    def tearDown(self):
        """Close the database connection after each test."""
        self.conn.close()

    def test_ensure_analytics_schema_adds_disciplines_column(self):
        """Verify that the schema migration adds the 'disciplines' column."""
        _ensure_analytics_schema(self.conn)

        cur = self.conn.cursor()
        cur.execute("PRAGMA table_info(analysis_runs)")
        columns = [row[1] for row in cur.fetchall()]
        self.assertIn("disciplines", columns)

    @patch('main._get_db_connection')
    def test_persist_analysis_run_with_disciplines(self, mock_get_db_connection):
        """Test that analysis run persistence includes disciplines."""
        # Have the mock return our in-memory connection
        mock_get_db_connection.return_value = self.conn
        _ensure_analytics_schema(self.conn)

        # Define test data
        disciplines = ["Skilled Nursing", "Physical Therapy"]

        # Call the function to test
        run_id = persist_analysis_run(
            file_path="test.pdf",
            run_time="2025-01-01T12:00:00",
            metrics={'pages_est': 1, 'flags': 2, 'wobblers': 3, 'suggestions': 4, 'notes': 5, 'sentences_final': 100, 'dedup_removed': 10},
            issues_scored=[],
            compliance={"score": 95.5},
            mode="TestMode",
            disciplines=disciplines
        )

        self.assertIsNotNone(run_id)

        # Verify data was inserted correctly
        cur = self.conn.cursor()
        cur.execute("SELECT disciplines FROM analysis_runs WHERE id=?", (run_id,))
        result = cur.fetchone()
        self.assertIsNotNone(result)
        self.assertEqual(result[0], "Skilled Nursing,Physical Therapy")

    @patch('main.persist_analysis_run')
    @patch('main.parse_document_content', return_value=[("text", "src")])
    @patch('main._audit_from_rubric', return_value=[])
    @patch('main.build_rich_summary', return_value={'total_sentences_raw': 1, 'dedup_removed': 0, 'total_sentences_final': 1})
    @patch('main._score_issue_confidence', return_value=[])
    @patch('main._attach_issue_citations', return_value=[])
    @patch('main._compute_recent_trends', return_value={})
    @patch('main.generate_report_paths', return_value=('mock.pdf', 'mock.csv'))
    @patch('main.export_report_json')
    @patch('main.export_report_pdf')
    @patch('os.path.isfile', return_value=True)
    def test_run_analyzer_calls_persist_with_disciplines(self, mock_isfile, mock_export_pdf, mock_export_json, mock_gen_paths, mock_trends, mock_attach, mock_score, mock_summary, mock_audit, mock_parse, mock_persist):
        """Ensure run_analyzer passes selected disciplines to the persistence layer."""
        selected_disciplines = ["Occupational Therapy"]

        with patch('main.logger'), patch('main.NLGService'), patch('main.shap'):
            run_analyzer(
                file_path="dummy.pdf",
                selected_disciplines=selected_disciplines
            )

        mock_persist.assert_called_once()
        self.assertEqual(mock_persist.call_args.kwargs['disciplines'], selected_disciplines)

class TestComplianceScore(unittest.TestCase):

    def test_compute_compliance_score(self):
        """
        Test the compliance score calculation.
        """
        issues = [{"severity": "flag"}, {"severity": "wobbler"}]
        strengths = ["Provider authentication (signature/date) appears to be present."]
        missing = ["Measurable/Time-bound Goals"]

        # Test moderate mode
        score_data = compute_compliance_score(issues, strengths, missing, "Moderate")
        self.assertIn("score", score_data)
        self.assertIsInstance(score_data["score"], float)
        # Expected: 100 - (1 * 4.0 flag) - (1 * 2.0 wobbler) - (1 * 2.5 missing) + (1 * 0.5 strength) = 92.0
        self.assertAlmostEqual(score_data["score"], 92.0, places=1)

        # Test strict mode
        score_data_strict = compute_compliance_score(issues, strengths, missing, "Strict")
        self.assertIn("score", score_data_strict)
        self.assertIsInstance(score_data_strict["score"], float)
        # Expected: 100 - (1 * 6.0 flag) - (1 * 3.0 wobbler) - (1 * 4.0 missing) + (1 * 0.5 strength) = 87.5
        self.assertAlmostEqual(score_data_strict["score"], 87.5, places=1)


if __name__ == '__main__':
    unittest.main(argv=['first-arg-is-ignored'], exit=False)
