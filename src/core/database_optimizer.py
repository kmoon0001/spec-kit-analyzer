"""Database Optimizer Service.

Provides database optimization features including:
- Query optimization and monitoring
- Connection pooling
- Index recommendations
- Statistics collection and analysis
- Medical data retention policies
- Performance monitoring for clinical workflows
"""

import logging
import sqlite3
from datetime import datetime, timedelta
from typing import Any

import sqlalchemy
import sqlalchemy.exc
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from src.database.crud import delete_reports_older_than

logger = logging.getLogger(__name__)


class DatabaseOptimizer:
    """Provides database optimization capabilities and monitoring for the
    Therapy Compliance Analyzer application.
    """

    def __init__(self, db_url: str):
        """Initializes the DatabaseOptimizer with the database URL.

        Args:
            db_url (str): The URL of the database to optimize.

        """
        """Initialize the database optimizer."""
        logger.info("Initializing DatabaseOptimizer")

        # Core tables in our application
        self.core_tables = [
            "users",
            "rubrics",
            "reports",
            "findings",
            "habit_goals",
            "habit_achievements",
            "habit_progress_snapshots",
        ]

        # Performance thresholds
        self.large_table_threshold = 10000  # rows
        self.old_data_threshold_days = 90  # days
        self.vacuum_size_threshold = 100 * 1024 * 1024  # 100MB

    async def analyze_table_statistics(self, db: AsyncSession, table_name: str) -> dict[str, Any]:
        """Analyzes statistics for a given database table.

        Retrieves row count, table size, and average row size to identify
        tables that might benefit from optimization.

        Args:
            db (AsyncSession): The asynchronous database session.
            table_name (str): The name of the table to analyze.

        Returns:
            Dict[str, Any]: A dictionary containing the table's statistics and
                            an indication if it needs optimization.

        """
        """
        Analyze table statistics for optimization insights.

        Args:
            db: Database session
            table_name: Name of the table to analyze

        Returns:
            Dictionary with table statistics
        """
        try:
            # Get row count
            result = await db.execute(text(f"SELECT COUNT(*) as row_count FROM {table_name}"))
            row_count = result.scalar()

            # Get table size information (SQLite specific)
            size_result = await db.execute(text(f"SELECT SUM(pgsize) FROM dbstat WHERE name='{table_name}'"))
            table_size = size_result.scalar() or 0

            # Calculate average row size
            avg_row_size = table_size / row_count if row_count > 0 else 0

            # Determine if table needs attention
            needs_optimization = row_count > self.large_table_threshold

            return {
                "table_name": table_name,
                "row_count": row_count,
                "table_size_bytes": table_size,
                "avg_row_size_bytes": round(avg_row_size, 2),
                "needs_optimization": needs_optimization,
                "analyzed_at": datetime.now().isoformat(),
            }
        except (sqlalchemy.exc.SQLAlchemyError, sqlite3.Error) as e:
            logger.exception("Error analyzing table %s: {e}", table_name)
            return {
                "table_name": table_name,
                "error": str(e),
                "analyzed_at": datetime.now().isoformat(),
            }

    async def get_optimization_recommendations(self, db: AsyncSession) -> list[dict[str, Any]]:
        """Generates a list of database optimization recommendations.

        These recommendations can include suggestions for regular maintenance tasks
        like VACUUM and advice on index usage.

        Args:
            db (AsyncSession): The asynchronous database session.

        Returns:
            List[Dict[str, Any]]: A list of dictionaries, each representing an
                                  optimization recommendation.

        """
        """
        Get database optimization recommendations.

        Args:
            db: Database session

        Returns:
            List of optimization recommendations
        """
        recommendations = []

        try:
            # Basic recommendations for SQLite
            recommendations.append(
                {
                    "type": "maintenance",
                    "title": "Regular VACUUM",
                    "description": "Run VACUUM periodically to reclaim space",
                    "priority": "medium",
                    "impact": "storage optimization",
                }
            )

            recommendations.append(
                {
                    "type": "performance",
                    "title": "Index Usage",
                    "description": "Ensure proper indexes on frequently queried columns",
                    "priority": "high",
                    "impact": "query performance",
                }
            )

        except (sqlalchemy.exc.SQLAlchemyError, sqlite3.Error) as e:
            logger.exception("Error getting optimization recommendations: %s", e)

        return recommendations

    async def cleanup_old_data(self, db: AsyncSession, days_to_keep: int = 90) -> dict[str, Any]:
        """Cleans up old data from the database based on a retention policy.

        This method deletes records older than a specified number of days,
        primarily targeting old reports.

        Args:
            db (AsyncSession): The asynchronous database session.
            days_to_keep (int): The number of days to retain data. Records older
                                than this will be deleted.

        Returns:
            Dict[str, Any]: A dictionary summarizing the cleanup operation, including
                            the number of records cleaned.

        """
        """
        Clean up old data based on retention policy.

        Args:
            db: Database session
            days_to_keep: Number of days to keep data

        Returns:
            Cleanup results
        """
        cutoff_date = datetime.now() - timedelta(days=days_to_keep)

        try:
            # Call the existing CRUD function to delete old reports
            num_deleted = await delete_reports_older_than(db, days=days_to_keep)

            logger.info("Successfully cleaned up %s old reports.", num_deleted)

            return {
                "cleanup_date": cutoff_date.isoformat(),
                "days_kept": days_to_keep,
                "status": "completed",
                "records_cleaned": num_deleted,
            }
        except (sqlalchemy.exc.SQLAlchemyError, sqlite3.Error) as e:
            logger.exception("Error during cleanup: %s", e)
            return {
                "cleanup_date": cutoff_date.isoformat(),
                "days_kept": days_to_keep,
                "status": "error",
                "error": str(e),
            }

    async def optimize_db(self):
        """Performs a full optimization of the database.

        This includes vacuuming the database to reclaim space and reindexing
        all tables to improve query performance.
        """
