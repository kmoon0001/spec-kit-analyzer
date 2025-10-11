"""Training data collection and management for confidence calibration."""

import json
import logging
import sqlite3
from collections.abc import Generator
from contextlib import contextmanager
from datetime import datetime
from pathlib import Path
from typing import Any

import requests
import sqlalchemy
import sqlalchemy.exc
from requests.exceptions import HTTPError

logger = logging.getLogger(__name__)


class CalibrationTrainer:
    """Manages collection and storage of training data for confidence calibration."""

    def __init__(self, db_path: str = "data/calibration_training.db"):
        """Initialize the calibration trainer.

        Args:
            db_path: Path to SQLite database for storing training data

        """
        self.db_path = db_path
        self._shared_conn: sqlite3.Connection | None = None  # For in-memory databases

        if db_path != ":memory:":
            db_path_obj = Path(db_path)
            db_path_obj.parent.mkdir(parents=True, exist_ok=True)

        self._init_database()

    def _init_database(self) -> None:
        """Initialize the training data database."""
        if self.db_path == ":memory:":
            # For in-memory databases, keep a shared connection
            if self._shared_conn is None:
                self._shared_conn = sqlite3.connect(self.db_path)
                self._shared_conn.row_factory = sqlite3.Row
            conn = self._shared_conn
            assert conn is not None
        else:
            conn = sqlite3.connect(self.db_path)

        try:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS training_data (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    finding_id TEXT NOT NULL,
                    original_confidence REAL NOT NULL,
                    user_feedback TEXT NOT NULL,  -- 'correct', 'incorrect', 'uncertain'
                    is_correct INTEGER NOT NULL,  -- 1 for correct, 0 for incorrect
                    document_type TEXT,
                    discipline TEXT,
                    rule_id TEXT,
                    issue_title TEXT,
                    severity TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    user_id TEXT,
                    notes TEXT
                )
            """)

            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_training_data_confidence
                ON training_data(original_confidence)
            """)

            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_training_data_feedback
                ON training_data(user_feedback)
            """)

            if self.db_path != ":memory:":
                conn.commit()
                conn.close()
        except (sqlalchemy.exc.SQLAlchemyError, sqlite3.Error):
            if self.db_path != ":memory:":
                conn.close()
            raise

    @contextmanager
    def _get_db_connection(self) -> Generator[sqlite3.Connection, None, None]:
        """Get database connection with proper cleanup."""
        if self.db_path == ":memory:":
            # Use shared connection for in-memory database
            if self._shared_conn is None:
                self._init_database()
            assert self._shared_conn is not None
            yield self._shared_conn
        else:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row
            try:
                yield conn
                conn.commit()
            except (sqlalchemy.exc.SQLAlchemyError, sqlite3.Error):
                conn.rollback()
                raise
            finally:
                conn.close()

    def record_feedback(
        self, finding: dict[str, Any], user_feedback: str, user_id: str | None = None, notes: str | None = None
    ) -> None:
        """Record user feedback on a compliance finding.

        Args:
            finding: The compliance finding dictionary
            user_feedback: User feedback ('correct', 'incorrect', 'uncertain')
            user_id: Optional user identifier
            notes: Optional additional notes

        """
        if user_feedback not in ["correct", "incorrect", "uncertain"]:
            raise ValueError("user_feedback must be 'correct', 'incorrect', or 'uncertain'") from None

        # Skip uncertain feedback for training (ambiguous cases)
        if user_feedback == "uncertain":
            logger.info("Skipping uncertain feedback for training data")
            return

        is_correct = 1 if user_feedback == "correct" else 0
        original_confidence = finding.get("original_confidence", finding.get("confidence", 0.5))

        # Ensure database is initialized (important for in-memory databases)
        self._init_database()

        with self._get_db_connection() as conn:
            conn.execute(
                """
                INSERT INTO training_data (
                    finding_id, original_confidence, user_feedback, is_correct,
                    document_type, discipline, rule_id, issue_title, severity,
                    user_id, notes
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
                (
                    finding.get("id", f"finding_{datetime.now().isoformat()}"),
                    float(original_confidence),
                    user_feedback,
                    is_correct,
                    finding.get("document_type"),
                    finding.get("discipline"),
                    finding.get("rule_id"),
                    finding.get("issue_title"),
                    finding.get("priority", finding.get("severity")),
                    user_id,
                    notes,
                ),
            )

        logger.info("Recorded feedback: %s for finding with confidence {original_confidence:.3f}", user_feedback)

    def get_training_data(
        self, min_samples: int = 10, confidence_range: tuple | None = None, discipline: str | None = None
    ) -> list[dict[str, Any]]:
        """Get training data for calibrator training.

        Args:
            min_samples: Minimum number of samples required
            confidence_range: Optional tuple (min_conf, max_conf) to filter by
            discipline: Optional discipline filter

        Returns:
            List of training samples with confidence and is_correct fields

        """
        # Ensure database is initialized
        self._init_database()

        query = "SELECT * FROM training_data WHERE user_feedback != 'uncertain'"
        params: list[Any] = []

        if confidence_range:
            query += " AND original_confidence BETWEEN ? AND ?"
            params.extend(confidence_range)

        if discipline:
            query += " AND discipline = ?"
            params.append(discipline)

        query += " ORDER BY created_at DESC"

        with self._get_db_connection() as conn:
            rows = conn.execute(query, params).fetchall()

        training_data = []
        for row in rows:
            training_data.append(
                {
                    "confidence": row["original_confidence"],
                    "is_correct": bool(row["is_correct"]),
                    "document_type": row["document_type"],
                    "discipline": row["discipline"],
                    "rule_id": row["rule_id"],
                    "issue_title": row["issue_title"],
                    "severity": row["severity"],
                    "created_at": row["created_at"],
                }
            )

        if len(training_data) < min_samples:
            logger.warning("Insufficient training data: %s samples (need {min_samples})", len(training_data))

        return training_data

    def get_feedback_statistics(self) -> dict[str, Any]:
        """Get statistics about collected feedback."""
        # Ensure database is initialized
        self._init_database()

        with self._get_db_connection() as conn:
            # Overall statistics
            total_feedback = conn.execute("SELECT COUNT(*) as count FROM training_data").fetchone()["count"]

            # Feedback distribution
            feedback_dist = conn.execute("""
                SELECT user_feedback, COUNT(*) as count
                FROM training_data
                GROUP BY user_feedback
            """).fetchall()

            # Confidence distribution for correct vs incorrect
            confidence_stats = conn.execute("""
                SELECT
                    is_correct,
                    AVG(original_confidence) as avg_confidence,
                    MIN(original_confidence) as min_confidence,
                    MAX(original_confidence) as max_confidence,
                    COUNT(*) as count
                FROM training_data
                WHERE user_feedback != 'uncertain'
                GROUP BY is_correct
            """).fetchall()

            # Discipline distribution
            discipline_dist = conn.execute("""
                SELECT discipline, COUNT(*) as count
                FROM training_data
                WHERE discipline IS NOT NULL
                GROUP BY discipline
            """).fetchall()

        return {
            "total_feedback": total_feedback,
            "feedback_distribution": {row["user_feedback"]: row["count"] for row in feedback_dist},
            "confidence_statistics": {
                "correct" if row["is_correct"] else "incorrect": {
                    "count": row["count"],
                    "avg_confidence": row["avg_confidence"],
                    "min_confidence": row["min_confidence"],
                    "max_confidence": row["max_confidence"],
                }
                for row in confidence_stats
            },
            "discipline_distribution": {row["discipline"]: row["count"] for row in discipline_dist},
        }

    def export_training_data(self, output_path: str, format: str = "json") -> None:
        """Export training data to file.

        Args:
            output_path: Path to output file
            format: Export format ('json' or 'csv')

        """
        training_data = self.get_training_data(min_samples=1)  # Get all data

        output_path_obj = Path(output_path)
        output_path_obj.parent.mkdir(parents=True, exist_ok=True)

        if format.lower() == "json":
            with open(output_path_obj, "w") as f:
                json.dump(training_data, f, indent=2, default=str)
        elif format.lower() == "csv":
            import csv

            if training_data:
                with open(output_path_obj, "w", newline="") as f:
                    writer = csv.DictWriter(f, fieldnames=training_data[0].keys())
                    writer.writeheader()
                    writer.writerows(training_data)
        else:
            raise ValueError("Format must be 'json' or 'csv'") from None

        logger.info("Exported %s training samples to {output_path_obj}", len(training_data))

    def clear_training_data(self, confirm: bool = False) -> None:
        """Clear all training data (use with caution).

        Args:
            confirm: Must be True to actually clear data

        """
        if not confirm:
            raise ValueError("Must set confirm=True to clear training data") from None

        with self._get_db_connection() as conn:
            conn.execute("DELETE FROM training_data")

        logger.warning("All training data has been cleared")


class FeedbackCollector:
    """Helper class for collecting user feedback in the GUI."""

    def __init__(self, trainer: CalibrationTrainer):
        """Initialize feedback collector with trainer."""
        self.trainer = trainer

    def create_feedback_widget(self, finding: dict[str, Any]) -> dict[str, Any]:
        """Create feedback widget data for a finding.

        Args:
            finding: The compliance finding

        Returns:
            Dictionary with widget configuration

        """
        return {
            "finding_id": finding.get("id", "unknown"),
            "issue_title": finding.get("issue_title", "Unknown Issue"),
            "confidence": finding.get("confidence", 0.5),
            "original_confidence": finding.get("original_confidence", finding.get("confidence", 0.5)),
            "calibrated": finding.get("confidence_calibrated", False),
            "buttons": [
                {"label": "✓ Correct", "value": "correct", "style": "success"},
                {"label": "✗ Incorrect", "value": "incorrect", "style": "danger"},
                {"label": "? Uncertain", "value": "uncertain", "style": "warning"},
            ],
        }

    def process_feedback(
        self, finding: dict[str, Any], feedback_value: str, user_id: str | None = None, notes: str | None = None
    ) -> None:
        """Process user feedback and store it for training.

        Args:
            finding: The compliance finding
            feedback_value: The feedback value ('correct', 'incorrect', 'uncertain')
            user_id: Optional user identifier
            notes: Optional notes from user

        """
        try:
            self.trainer.record_feedback(finding, feedback_value, user_id, notes)
            logger.info("Processed feedback: %s for finding %s", feedback_value, finding.get("id", "unknown"))
        except (requests.RequestException, ConnectionError, TimeoutError, HTTPError) as e:
            logger.exception("Failed to process feedback: %s", e)
