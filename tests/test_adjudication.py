import pytest
import sqlite3
from unittest.mock import MagicMock, patch

# Since AdjudicationService is in src/adjudication_service.py, we need to adjust the path
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.adjudication_service import AdjudicationService

@pytest.fixture
def mock_db_connection():
    """Fixture to create a mock database connection."""
    mock_conn = MagicMock(spec=sqlite3.Connection)
    mock_cursor = MagicMock(spec=sqlite3.Cursor)
    mock_conn.cursor.return_value = mock_cursor
    # Make the connection object a context manager
    mock_conn.__enter__.return_value = mock_conn
    mock_conn.__exit__.return_value = None
    return mock_conn

@pytest.fixture
def adjudication_service(mock_db_connection):
    """Fixture to create an AdjudicationService with a mocked DB connection provider."""
    db_provider = MagicMock(return_value=mock_db_connection)
    return AdjudicationService(db_connection_provider=db_provider)

def test_get_adjudication_items(adjudication_service, mock_db_connection):
    """
    Test that get_adjudication_items executes the correct SQL query.
    """
    mock_cursor = mock_db_connection.cursor.return_value
    mock_cursor.fetchall.return_value = [
        (1, 'Test Title', 'Test Detail', 0.9, 'test_file.txt', '2025-01-01', 'DISAGREEMENT')
    ]

    items = adjudication_service.get_adjudication_items()

    assert mock_cursor.execute.call_count == 1

    executed_sql = mock_cursor.execute.call_args[0][0]
    # Check for key parts of the query to make it less brittle
    assert "SELECT" in executed_sql
    assert "FROM analysis_issues i" in executed_sql
    assert "JOIN analysis_runs r ON i.run_id = r.id" in executed_sql
    assert "LEFT JOIN adjudication_log a ON i.id = a.analysis_issue_id" in executed_sql
    assert "WHERE i.label = 'DISAGREEMENT' AND a.id IS NULL" in executed_sql

    assert len(items) == 1
    assert items[0]['issue_id'] == 1
    assert items[0]['title'] == 'Test Title'

def test_save_adjudication(adjudication_service, mock_db_connection):
    """
    Test that save_adjudication executes the correct SQL INSERT/REPLACE statement.
    """
    mock_cursor = mock_db_connection.cursor.return_value

    issue_id = 123
    decision = "confirm_a"
    corrected_label = "some_label"
    notes = "Some notes"

    success = adjudication_service.save_adjudication(issue_id, decision, corrected_label, notes)

    assert success is True
    assert mock_cursor.execute.call_count == 1

    executed_sql = mock_cursor.execute.call_args[0][0]
    params = mock_cursor.execute.call_args[0][1]

    assert "INSERT OR REPLACE INTO adjudication_log" in executed_sql
    assert "(analysis_issue_id, user_decision, corrected_label, notes, adjudicated_at)" in executed_sql

    assert params[0] == issue_id
    assert params[1] == decision
    assert params[2] == corrected_label
    assert params[3] == notes
    # We don't check the timestamp as it's generated dynamically

    assert mock_db_connection.commit.call_count == 1
