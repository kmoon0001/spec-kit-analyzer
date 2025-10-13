import pytest
from sqlalchemy.ext.asyncio import AsyncSession
from src.database import crud, models, schemas

@pytest.mark.asyncio
async def test_get_user(db_session: AsyncSession):
    user = await crud.create_user(db_session, schemas.UserCreate(username="testuser_crud", password="password"), "hashed_password")
    retrieved_user = await crud.get_user(db_session, user.id)
    assert retrieved_user is not None
    assert retrieved_user.id == user.id
    assert retrieved_user.username == "testuser_crud"

@pytest.mark.asyncio
async def test_get_user_by_username(db_session: AsyncSession):
    await crud.create_user(db_session, schemas.UserCreate(username="testuser2_crud", password="password"), "hashed_password")
    retrieved_user = await crud.get_user_by_username(db_session, "testuser2_crud")
    assert retrieved_user is not None
    assert retrieved_user.username == "testuser2_crud"

@pytest.mark.asyncio
async def test_change_user_password(db_session: AsyncSession):
    user = await crud.create_user(db_session, schemas.UserCreate(username="testuser3_crud", password="password"), "hashed_password")
    await crud.change_user_password(db_session, user, "new_hashed_password")
    retrieved_user = await crud.get_user(db_session, user.id)
    assert retrieved_user.hashed_password == "new_hashed_password"

@pytest.mark.asyncio
async def test_create_rubric(db_session: AsyncSession):
    rubric_data = schemas.RubricCreate(
        name="Test Rubric 1",
        discipline="PT",
        category="Test",
        regulation="Test Regulation",
        common_pitfalls="Test Pitfalls",
        best_practice="Test Best Practice",
    )
    rubric = await crud.create_rubric(db_session, rubric_data)
    assert rubric.name == "Test Rubric 1"
    assert rubric.discipline == "PT"

@pytest.mark.asyncio
async def test_get_rubrics(db_session: AsyncSession):
    await crud.create_rubric(
        db_session,
        schemas.RubricCreate(
            name="Test Rubric 2",
            discipline="OT",
            category="Test",
            regulation="Test Regulation",
            common_pitfalls="Test Pitfalls",
            best_practice="Test Best Practice",
        ),
    )
    rubrics = await crud.get_rubrics(db_session)
    assert len(rubrics) > 0

@pytest.mark.asyncio
async def test_get_rubric(db_session: AsyncSession):
    rubric = await crud.create_rubric(
        db_session,
        schemas.RubricCreate(
            name="Test Rubric 3",
            discipline="SLP",
            category="Test",
            regulation="Test Regulation",
            common_pitfalls="Test Pitfalls",
            best_practice="Test Best Practice",
        ),
    )
    retrieved_rubric = await crud.get_rubric(db_session, rubric.id)
    assert retrieved_rubric is not None
    assert retrieved_rubric.id == rubric.id

@pytest.mark.asyncio
async def test_update_rubric(db_session: AsyncSession):
    rubric = await crud.create_rubric(
        db_session,
        schemas.RubricCreate(
            name="Test Rubric 4",
            discipline="PT",
            category="Test",
            regulation="Test Regulation",
            common_pitfalls="Test Pitfalls",
            best_practice="Test Best Practice",
        ),
    )
    updated_rubric_data = schemas.RubricCreate(
        name="Updated Rubric",
        discipline="OT",
        category="Updated",
        regulation="Updated Regulation",
        common_pitfalls="Updated Pitfalls",
        best_practice="Updated Best Practice",
    )
    updated_rubric = await crud.update_rubric(db_session, rubric.id, updated_rubric_data)
    assert updated_rubric.name == "Updated Rubric"
    assert updated_rubric.discipline == "OT"

@pytest.mark.asyncio
async def test_delete_rubric(db_session: AsyncSession):
    rubric = await crud.create_rubric(
        db_session,
        schemas.RubricCreate(
            name="Test Rubric 5",
            discipline="PT",
            category="Test",
            regulation="Test Regulation",
            common_pitfalls="Test Pitfalls",
            best_practice="Test Best Practice",
        ),
    )
    result = await crud.delete_rubric(db_session, rubric.id)
    assert result is True
    retrieved_rubric = await crud.get_rubric(db_session, rubric.id)
    assert retrieved_rubric is None

@pytest.mark.asyncio
async def test_get_dashboard_statistics(populated_db: AsyncSession):
    stats = await crud.get_dashboard_statistics(populated_db)
    assert stats["total_documents_analyzed"] == 4
    assert stats["overall_compliance_score"] == pytest.approx(86.25)

@pytest.mark.asyncio
async def test_get_organizational_metrics(populated_db: AsyncSession):
    metrics = await crud.get_organizational_metrics(populated_db, days_back=30)
    assert metrics["total_analyses"] == 4

@pytest.mark.asyncio
async def test_get_discipline_breakdown(populated_db: AsyncSession):
    breakdown = await crud.get_discipline_breakdown(populated_db, days_back=30)
    assert len(breakdown) == 3

@pytest.mark.asyncio
async def test_get_team_performance_trends(populated_db: AsyncSession):
    trends = await crud.get_team_performance_trends(populated_db, days_back=21)
    assert len(trends) == 3

@pytest.mark.asyncio
async def test_get_benchmark_data(populated_db: AsyncSession):
    benchmarks = await crud.get_benchmark_data(populated_db, min_analyses=3)
    assert benchmarks["data_quality"] == "adequate"

@pytest.mark.asyncio
async def test_find_similar_report(populated_db: AsyncSession):
    report_2 = await crud.get_report(populated_db, 2)
    similar_report = await crud.find_similar_report(
        db=populated_db,
        document_type="Evaluation",
        exclude_report_id=2,
        embedding=report_2.document_embedding,
        threshold=0.5,
    )
    assert similar_report is not None

@pytest.mark.asyncio
async def test_create_analysis_report(db_session: AsyncSession):
    report_data = schemas.ReportCreate(
        document_name="Test Report",
        compliance_score=99.0,
        analysis_result={},
        document_type="Test Note",
    )
    findings_data = [
        schemas.FindingCreate(
            rule_id="test-rule",
            risk="Low",
            personalized_tip="Test tip",
            problematic_text="Test text",
            confidence_score=0.9,
        )
    ]
    report = await crud.create_analysis_report(db_session, report_data, findings_data)
    assert report.document_name == "Test Report"
    assert len(report.findings) == 1

@pytest.mark.asyncio
async def test_get_reports(populated_db: AsyncSession):
    reports = await crud.get_reports(populated_db)
    assert len(reports) == 4

@pytest.mark.asyncio
async def test_get_findings_summary(populated_db: AsyncSession):
    summary = await crud.get_findings_summary(populated_db)
    assert isinstance(summary, list)

@pytest.mark.asyncio
async def test_get_total_findings_count(populated_db: AsyncSession):
    count = await crud.get_total_findings_count(populated_db)
    assert count >= 0