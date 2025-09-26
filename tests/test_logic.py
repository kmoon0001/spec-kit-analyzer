import pytest
import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from src.core.analysis_service import AnalysisService
from src.database import Base
from src.models import Rubric

# --- In-Memory Database Setup for E2E Test ---

@pytest.fixture(scope="module")
def seeded_db_session():
    """
    A fixture that creates and seeds a completely isolated, in-memory SQLite database,
    and yields the session for use in tests. This is the most robust way to test
    database-dependent services.
    """
    engine = create_engine("sqlite:///:memory:")
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()

    test_rubrics = [
        Rubric(name="Goal Specificity", content="Goals must be measurable and specific, not vague like 'get stronger'."),
        Rubric(name="Signature Missing", content="All documents must be signed by the therapist."),
        Rubric(name="Untimed Codes", content="Each CPT code must have the total time spent documented."),
    ]

    try:
        db.add_all(test_rubrics)
        db.commit()
        print("\n--- In-Memory E2E Database Seeded ---")
        yield db
    finally:
        print("\n--- In-Memory E2E Database Cleanup ---")
        db.close()
        Base.metadata.drop_all(bind=engine)

@pytest.mark.e2e
def test_e2e_analysis_on_bad_note(seeded_db_session):
    """
    Tests the full analysis pipeline end-to-end using a self-contained,
    in-memory database.
    """
    # 1. Initialize the AnalysisService directly with the seeded in-memory database session.
    #    This ensures the service and all its sub-components use the test's isolated database.
    try:
        service = AnalysisService(db=seeded_db_session)
    except Exception as e:
        pytest.fail(f"Failed to initialize the core AnalysisService: {e}")

    # 2. Define the path to the test document and ensure it exists
    test_file_path = os.path.abspath("test_data/bad_note_1.txt")
    assert os.path.exists(test_file_path), f"Test file not found at: {test_file_path}"

    # 3. Run the analysis on the document
    results = service.analyze_document(file_path=test_file_path, discipline="PT")

    # 4. Assert that the analysis produced a valid, non-empty result
    assert results is not None, "The analysis service returned None."
    assert "findings" in results, f"The 'findings' key is missing from the analysis results. Got: {results}"

    findings = results["findings"]
    assert isinstance(findings, list), "The 'findings' should be a list."
    assert len(findings) > 0, "No compliance findings were returned for a document known to have issues."

    # 5. Assert the structure of the findings
    first_finding = findings[0]
    assert "text" in first_finding
    assert "risk" in first_finding
    assert "suggestion" in first_finding
    assert "confidence" in first_finding
    assert "personalized_tip" in first_finding

    print(f"\nE2E Test Passed: Found {len(findings)} findings in the test document.")
    print(f"First finding: {first_finding['risk']}")

    # Close the service to release the database connection
    service.close()