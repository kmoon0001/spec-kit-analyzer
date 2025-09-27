import pytest
import pytest_asyncio
import os
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

# Import the application's Base for metadata and the core services
from src.database import Base
from src.models import Rubric
from src.core.retriever import HybridRetriever
from src.core.analysis_service import AnalysisService

# --- Async In-Memory Database Fixture ---


@pytest_asyncio.fixture(scope="module")
async def seeded_db_session() -> AsyncSession:
    """
    Creates and seeds an isolated, in-memory async SQLite database for E2E testing.
    """
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    TestingSessionLocal = sessionmaker(
        bind=engine, class_=AsyncSession, expire_on_commit=False
    )

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    session = TestingSessionLocal()
    try:
        # Seed the database with test rubrics
        test_rubrics = [
            Rubric(
                name="Goal Specificity",
                content="Goals must be measurable and specific.",
            ),
            Rubric(name="Signature Missing", content="All documents must be signed."),
        ]
        session.add_all(test_rubrics)
        await session.commit()
        yield session
    finally:
        await session.close()
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.drop_all)


# --- E2E Test ---


@pytest.mark.e2e
@pytest.mark.asyncio
async def test_e2e_analysis_on_bad_note(seeded_db_session: AsyncSession):
    """
    Tests the full analysis pipeline end-to-end using a self-contained,
    in-memory async database.
    """
    # 1. Initialize the full dependency chain for the AnalysisService
    #    This uses the real services, not mocks, for a true E2E test.
    try:
        # The retriever needs the async db session to load guidelines
        retriever = await HybridRetriever.create(
            db_session=seeded_db_session, guideline_sources=[]
        )
        # The analysis service needs the retriever
        service = AnalysisService(retriever=retriever)
    except Exception as e:
        pytest.fail(f"Failed to initialize the core services for E2E test: {e}")

    # 2. Define the path to the test document
    # Ensure you have a 'test_data/bad_note_1.txt' file in your project root for this to pass
    test_file_path = "test_data/bad_note_1.txt"
    if not os.path.exists(test_file_path):
        os.makedirs("test_data", exist_ok=True)
        with open(test_file_path, "w") as f:
            f.write("The patient feels stronger. Plan is to continue.")

    # 3. Run the analysis on the document
    results = service.analyze_document(file_path=test_file_path, discipline="PT")

    # 4. Assert that the analysis produced a valid, non-empty result
    assert results is not None, "The analysis service returned None."
    assert "findings" in results, (
        f"The 'findings' key is missing from the analysis results. Got: {results}"
    )

    findings = results["findings"]
    assert isinstance(findings, list), "The 'findings' should be a list."
    assert len(findings) > 0, (
        "No compliance findings were returned for a document known to have issues."
    )

    # 5. Assert the structure of the findings
    first_finding = findings[0]
    assert "text" in first_finding
    assert "risk" in first_finding
    assert "suggestion" in first_finding
    assert "confidence" in first_finding
