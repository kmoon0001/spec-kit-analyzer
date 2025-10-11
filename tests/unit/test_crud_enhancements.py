"""
Unit tests for enhanced CRUD operations.

Tests the new functionality and best practices added to the CRUD layer,
including input validation, error handling, and bulk operations.
"""

from unittest.mock import AsyncMock, MagicMock

import pytest
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from src.database import crud, schemas


class TestInputValidation:
    """Test input validation in CRUD operations"""

    @pytest.mark.asyncio
    async def test_get_user_by_username_validation(self):
        """Test username validation in get_user_by_username"""
        db_mock = AsyncMock(spec=AsyncSession)

        # Test empty username
        with pytest.raises(ValueError, match="Username cannot be empty"):
            await crud.get_user_by_username(db_mock, "")

        # Test whitespace-only username
        with pytest.raises(ValueError, match="Username cannot be empty"):
            await crud.get_user_by_username(db_mock, "   ")

    @pytest.mark.asyncio
    async def test_get_rubrics_pagination_validation(self):
        """Test pagination validation in get_rubrics"""
        db_mock = AsyncMock(spec=AsyncSession)

        # Test negative skip
        with pytest.raises(ValueError, match="Skip parameter must be non-negative"):
            await crud.get_rubrics(db_mock, skip=-1)

        # Test invalid limit
        with pytest.raises(ValueError, match="Limit must be between 1 and 1000"):
            await crud.get_rubrics(db_mock, limit=0)

        with pytest.raises(ValueError, match="Limit must be between 1 and 1000"):
            await crud.get_rubrics(db_mock, limit=1001)

    @pytest.mark.asyncio
    async def test_delete_rubric_validation(self):
        """Test rubric ID validation in delete_rubric"""
        db_mock = AsyncMock(spec=AsyncSession)

        # Test invalid rubric ID
        with pytest.raises(ValueError, match="Rubric ID must be positive"):
            await crud.delete_rubric(db_mock, 0)

        with pytest.raises(ValueError, match="Rubric ID must be positive"):
            await crud.delete_rubric(db_mock, -1)


class TestErrorHandling:
    """Test error handling in CRUD operations"""

    @pytest.mark.asyncio
    async def test_create_user_error_handling(self):
        """Test error handling in create_user"""
        db_mock = AsyncMock(spec=AsyncSession)
        db_mock.commit.side_effect = IntegrityError("", "", "")
        db_mock.rollback = AsyncMock()

        user_data = schemas.UserCreate(username="testuser", password="password")

        with pytest.raises(IntegrityError):
            await crud.create_user(db_mock, user_data, "hashed_password")

        # Verify rollback was called
        db_mock.rollback.assert_called_once()

    @pytest.mark.asyncio
    async def test_dashboard_statistics_error_recovery(self):
        """Test error recovery in get_dashboard_statistics"""
        db_mock = AsyncMock(spec=AsyncSession)
        db_mock.execute.side_effect = SQLAlchemyError("Database error")

        # Should return default statistics on error
        stats = await crud.get_dashboard_statistics(db_mock)

        assert stats["total_documents_analyzed"] == 0
        assert stats["overall_compliance_score"] == 0.0
        assert stats["compliance_by_category"] == {}
        assert "error" in stats


class TestBulkOperations:
    """Test bulk operations for performance"""

    @pytest.mark.asyncio
    async def test_bulk_create_findings_validation(self):
        """Test validation in bulk_create_findings"""
        db_mock = AsyncMock(spec=AsyncSession)

        # Test invalid report ID
        with pytest.raises(ValueError, match="Report ID must be positive"):
            await crud.bulk_create_findings(db_mock, 0, [])

        # Test empty findings list
        result = await crud.bulk_create_findings(db_mock, 1, [])
        assert result == []

        # Test invalid finding data
        invalid_finding = schemas.FindingCreate(
            rule_id="",  # Empty rule ID
            risk="High",
            personalized_tip="Test tip",
            problematic_text="Test text",
            confidence_score=0.5,
        )

        with pytest.raises(ValueError, match="Rule ID cannot be empty"):
            await crud.bulk_create_findings(db_mock, 1, [invalid_finding])

    @pytest.mark.asyncio
    async def test_bulk_create_findings_risk_validation(self):
        """Test risk level validation in bulk_create_findings"""
        db_mock = AsyncMock(spec=AsyncSession)

        invalid_finding = schemas.FindingCreate(
            rule_id="test_rule",
            risk="Invalid",  # Invalid risk level
            personalized_tip="Test tip",
            problematic_text="Test text",
            confidence_score=0.5,
        )

        with pytest.raises(ValueError, match="Risk must be High, Medium, or Low"):
            await crud.bulk_create_findings(db_mock, 1, [invalid_finding])

    @pytest.mark.asyncio
    async def test_bulk_create_findings_confidence_validation(self):
        """Test confidence score validation in bulk_create_findings"""
        db_mock = AsyncMock(spec=AsyncSession)

        invalid_finding = schemas.FindingCreate(
            rule_id="test_rule",
            risk="High",
            personalized_tip="Test tip",
            problematic_text="Test text",
            confidence_score=1.5,  # Invalid confidence score
        )

        with pytest.raises(ValueError, match="Confidence score must be between 0.0 and 1.0"):
            await crud.bulk_create_findings(db_mock, 1, [invalid_finding])


class TestEnhancedReporting:
    """Test enhanced reporting functions"""

    @pytest.mark.asyncio
    async def test_create_analysis_report_validation(self):
        """Test validation in create_analysis_report"""
        db_mock = AsyncMock(spec=AsyncSession)

        # Test empty document name
        invalid_report = schemas.ReportCreate(document_name="", compliance_score=85.0, analysis_result={})

        with pytest.raises(ValueError, match="Document name cannot be empty"):
            await crud.create_analysis_report(db_mock, invalid_report)

        # Test invalid compliance score
        invalid_report = schemas.ReportCreate(
            document_name="test.pdf",
            compliance_score=150.0,  # Invalid score
            analysis_result={},
        )

        with pytest.raises(ValueError, match="Compliance score must be between 0 and 100"):
            await crud.create_analysis_report(db_mock, invalid_report)

    @pytest.mark.asyncio
    async def test_get_benchmark_data_parameters(self):
        """Test parameter handling in get_benchmark_data"""
        db_mock = AsyncMock(spec=AsyncSession)

        # Mock empty result
        mock_result = MagicMock()
        mock_result.fetchall.return_value = []
        db_mock.execute.return_value = mock_result

        # Test with custom parameters
        benchmarks = await crud.get_benchmark_data(db_mock, days_back=30, min_analyses=5)

        assert benchmarks["data_quality"] == "insufficient"
        assert benchmarks["days_analyzed"] == 30
        assert "last_updated" in benchmarks


class TestDatabaseHealth:
    """Test database health and maintenance functions"""

    @pytest.mark.asyncio
    async def test_get_database_health_success(self):
        """Test successful database health check"""
        db_mock = AsyncMock(spec=AsyncSession)

        # Mock successful scalar calls
        db_mock.scalar.side_effect = [10, 50, 200, 5, 15, 85.5]

        health = await crud.get_database_health(db_mock)

        assert health["status"] == "healthy"
        assert health["table_counts"]["users"] == 10
        assert health["table_counts"]["reports"] == 50
        assert health["table_counts"]["findings"] == 200
        assert health["table_counts"]["rubrics"] == 5
        assert health["recent_activity"]["reports_last_7_days"] == 15
        assert health["metrics"]["average_compliance_score"] == 85.5

    @pytest.mark.asyncio
    async def test_get_database_health_error(self):
        """Test database health check error handling"""
        db_mock = AsyncMock(spec=AsyncSession)
        db_mock.scalar.side_effect = SQLAlchemyError("Connection failed")

        health = await crud.get_database_health(db_mock)

        assert health["status"] == "unhealthy"
        assert "error" in health

    @pytest.mark.asyncio
    async def test_cleanup_old_data_dry_run(self):
        """Test cleanup old data in dry run mode"""
        db_mock = AsyncMock(spec=AsyncSession)

        # Mock count queries
        db_mock.scalar.side_effect = [25, 100]  # old reports, old snapshots

        cleanup_counts = await crud.cleanup_old_data(db_mock, days_to_keep=30, dry_run=True)

        assert cleanup_counts["reports"] == 25
        assert cleanup_counts["snapshots"] == 100

        # Verify no delete operations were called
        db_mock.execute.assert_not_called()
        db_mock.commit.assert_not_called()


class TestHabitProgressValidation:
    """Test habit progress snapshot validation"""

    @pytest.mark.asyncio
    async def test_create_habit_progress_snapshot_validation(self):
        """Test validation in create_habit_progress_snapshot"""
        db_mock = AsyncMock(spec=AsyncSession)

        # Test invalid user ID
        with pytest.raises(ValueError, match="User ID must be positive"):
            await crud.create_habit_progress_snapshot(db_mock, 0, {})

        # Test invalid habit percentage
        invalid_data = {
            "habit_breakdown": {
                "habit_1": 150.0  # Invalid percentage
            }
        }

        with pytest.raises(ValueError, match="Habit 1 percentage must be between 0 and 100"):
            await crud.create_habit_progress_snapshot(db_mock, 1, invalid_data)


if __name__ == "__main__":
    pytest.main([__file__])
