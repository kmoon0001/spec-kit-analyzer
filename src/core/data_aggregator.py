import json
import logging
import sqlite3
import statistics
import threading
from dataclasses import dataclass
from datetime import datetime, timedelta
from enum import Enum
from pathlib import Path
from typing import Any

import requests
import sqlalchemy
import sqlalchemy.exc
from requests.exceptions import HTTPError

logger = logging.getLogger(__name__)


class AggregationLevel(Enum):
    """Levels of data aggregation."""

    RAW = "raw"  # 5-second intervals
    SHORT_TERM = "short"  # 1-minute averages
    MEDIUM_TERM = "medium"  # 5-minute averages
    LONG_TERM = "long"  # 1-hour averages


@dataclass
class AggregatedMetric:
    """Aggregated metric data."""

    timestamp: datetime
    name: str
    source: str
    aggregation_level: AggregationLevel
    count: int
    min_value: float
    max_value: float
    avg_value: float
    sum_value: float
    std_dev: float | None
    tags: dict[str, str]
    metadata: dict[str, Any]


class MetricBuffer:
    """Thread-safe buffer for collecting metrics before aggregation."""

    def __init__(self, max_size: int = 10000):
        self.max_size = max_size
        self._buffer: list[dict[str, Any]] = []
        self._lock = threading.Lock()

    def add_metrics(self, metrics: list[dict[str, Any]]) -> None:
        """Add metrics to buffer.

        Args:
            metrics: List of metric dictionaries

        """
        with self._lock:
            self._buffer.extend(metrics)

            # Prevent buffer overflow
            if len(self._buffer) > self.max_size:
                overflow = len(self._buffer) - self.max_size
                self._buffer = self._buffer[overflow:]
                logger.warning("Metric buffer overflow, dropped %s oldest metrics", overflow)

    def get_and_clear(self) -> list[dict[str, Any]]:
        """Get all buffered metrics and clear the buffer.

        Returns:
            List of buffered metrics

        """
        with self._lock:
            metrics = self._buffer.copy()
            self._buffer.clear()
            return metrics

    def size(self) -> int:
        """Get current buffer size.

        Returns:
            Number of metrics in buffer

        """
        with self._lock:
            return len(self._buffer)


class TimeSeriesStorage:
    """SQLite-based time-series storage for metrics."""

    def _init_database(self) -> None:
        """Initialize database schema."""
        with self._lock:
            conn = sqlite3.connect(self.db_path)
            try:
                # Raw metrics table
                conn.execute("""
                    CREATE TABLE IF NOT EXISTS raw_metrics (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        timestamp TEXT NOT NULL,
                        name TEXT NOT NULL,
                        value REAL NOT NULL,
                        unit TEXT,
                        type TEXT,
                        source TEXT NOT NULL,
                        tags TEXT,
                        metadata TEXT,
                        created_at TEXT DEFAULT CURRENT_TIMESTAMP
                    )
                """)

                # Aggregated metrics table
                conn.execute("""
                    CREATE TABLE IF NOT EXISTS aggregated_metrics (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        timestamp TEXT NOT NULL,
                        name TEXT NOT NULL,
                        source TEXT NOT NULL,
                        aggregation_level TEXT NOT NULL,
                        count INTEGER NOT NULL,
                        min_value REAL NOT NULL,
                        max_value REAL NOT NULL,
                        avg_value REAL NOT NULL,
                        sum_value REAL NOT NULL,
                        std_dev REAL,
                        tags TEXT,
                        metadata TEXT,
                        created_at TEXT DEFAULT CURRENT_TIMESTAMP
                    )
                """)

                # Create indexes for better query performance
                conn.execute("CREATE INDEX IF NOT EXISTS idx_raw_timestamp ON raw_metrics(timestamp)")
                conn.execute("CREATE INDEX IF NOT EXISTS idx_raw_name ON raw_metrics(name)")
                conn.execute("CREATE INDEX IF NOT EXISTS idx_raw_source ON raw_metrics(source)")

                conn.execute("CREATE INDEX IF NOT EXISTS idx_agg_timestamp ON aggregated_metrics(timestamp)")
                conn.execute("CREATE INDEX IF NOT EXISTS idx_agg_name ON aggregated_metrics(name)")
                conn.execute("CREATE INDEX IF NOT EXISTS idx_agg_level ON aggregated_metrics(aggregation_level)")

                conn.commit()
                logger.debug("Database schema initialized")

            finally:
                conn.close()

    def store_raw_metrics(self, metrics: list[dict[str, Any]]) -> int:
        """Store raw metrics in database.

        Args:
            metrics: List of metric dictionaries

        Returns:
            Number of metrics stored

        """
        if not metrics:
            return 0

        with self._lock:
            conn = sqlite3.connect(self.db_path)
            try:
                cursor = conn.cursor()

                for metric in metrics:
                    cursor.execute(
                        """
                        INSERT INTO raw_metrics
                        (timestamp, name, value, unit, type, source, tags, metadata)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                        (
                            metric.get("timestamp"),
                            metric.get("name"),
                            metric.get("value"),
                            metric.get("unit"),
                            metric.get("type"),
                            metric.get("source"),
                            json.dumps(metric.get("tags", {})),
                            json.dumps(metric.get("metadata", {})),
                        ),
                    )

                conn.commit()
                return len(metrics)

            except (requests.RequestException, ConnectionError, TimeoutError, HTTPError) as e:
                logger.exception("Error storing raw metrics: %s", e)
                conn.rollback()
                return 0
            finally:
                conn.close()

    def store_aggregated_metrics(self, metrics: list[AggregatedMetric]) -> int:
        """Store aggregated metrics in database.

        Args:
            metrics: List of aggregated metrics

        Returns:
            Number of metrics stored

        """
        if not metrics:
            return 0

        with self._lock:
            conn = sqlite3.connect(self.db_path)
            try:
                cursor = conn.cursor()

                for metric in metrics:
                    cursor.execute(
                        """
                        INSERT INTO aggregated_metrics
                        (timestamp, name, source, aggregation_level, count,
                         min_value, max_value, avg_value, sum_value, std_dev, tags, metadata)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                        (
                            metric.timestamp.isoformat(),
                            metric.name,
                            metric.source,
                            metric.aggregation_level.value,
                            metric.count,
                            metric.min_value,
                            metric.max_value,
                            metric.avg_value,
                            metric.sum_value,
                            metric.std_dev,
                            json.dumps(metric.tags),
                            json.dumps(metric.metadata),
                        ),
                    )

                conn.commit()
                return len(metrics)

            except (json.JSONDecodeError, ValueError, KeyError) as e:
                logger.exception("Error storing aggregated metrics: %s", e)
                conn.rollback()
                return 0
            finally:
                conn.close()

    def query_raw_metrics(
        self, start_time: datetime, end_time: datetime, metric_name: str | None = None, source: str | None = None
    ) -> list[dict[str, Any]]:
        """Query raw metrics from database.

        Args:
            start_time: Start of time range
            end_time: End of time range
            metric_name: Optional metric name filter
            source: Optional source filter

        Returns:
            List of raw metrics

        """
        with self._lock:
            conn = sqlite3.connect(self.db_path)
            try:
                cursor = conn.cursor()

                query = """
                    SELECT timestamp, name, value, unit, type, source, tags, metadata
                    FROM raw_metrics
                    WHERE timestamp >= ? AND timestamp <= ?
                """
                params = [start_time.isoformat(), end_time.isoformat()]

                if metric_name:
                    query += " AND name = ?"
                    params.append(metric_name)

                if source:
                    query += " AND source = ?"
                    params.append(source)

                query += " ORDER BY timestamp"

                cursor.execute(query, params)
                rows = cursor.fetchall()

                metrics = []
                for row in rows:
                    metrics.append(
                        {
                            "timestamp": row[0],
                            "name": row[1],
                            "value": row[2],
                            "unit": row[3],
                            "type": row[4],
                            "source": row[5],
                            "tags": json.loads(row[6]) if row[6] else {},
                            "metadata": json.loads(row[7]) if row[7] else {},
                        }
                    )

                return metrics

            except (sqlalchemy.exc.SQLAlchemyError, sqlite3.Error) as e:
                logger.exception("Error querying raw metrics: %s", e)
                return []
            finally:
                conn.close()

    def query_aggregated_metrics(
        self,
        start_time: datetime,
        end_time: datetime,
        aggregation_level: AggregationLevel,
        metric_name: str | None = None,
        source: str | None = None,
    ) -> list[AggregatedMetric]:
        """Query aggregated metrics from database.

        Args:
            start_time: Start of time range
            end_time: End of time range
            aggregation_level: Level of aggregation
            metric_name: Optional metric name filter
            source: Optional source filter

        Returns:
            List of aggregated metrics

        """
        with self._lock:
            conn = sqlite3.connect(self.db_path)
            try:
                cursor = conn.cursor()

                query = """
                    SELECT timestamp, name, source, aggregation_level, count,
                           min_value, max_value, avg_value, sum_value, std_dev, tags, metadata
                    FROM aggregated_metrics
                    WHERE timestamp >= ? AND timestamp <= ? AND aggregation_level = ?
                """
                params = [start_time.isoformat(), end_time.isoformat(), aggregation_level.value]

                if metric_name:
                    query += " AND name = ?"
                    params.append(metric_name)

                if source:
                    query += " AND source = ?"
                    params.append(source)

                query += " ORDER BY timestamp"

                cursor.execute(query, params)
                rows = cursor.fetchall()

                metrics = []
                for row in rows:
                    metrics.append(
                        AggregatedMetric(
                            timestamp=datetime.fromisoformat(row[0]),
                            name=row[1],
                            source=row[2],
                            aggregation_level=AggregationLevel(row[3]),
                            count=row[4],
                            min_value=row[5],
                            max_value=row[6],
                            avg_value=row[7],
                            sum_value=row[8],
                            std_dev=row[9],
                            tags=json.loads(row[10]) if row[10] else {},
                            metadata=json.loads(row[11]) if row[11] else {},
                        )
                    )

                return metrics

            except (sqlalchemy.exc.SQLAlchemyError, sqlite3.Error) as e:
                logger.exception("Error querying aggregated metrics: %s", e)
                return []
            finally:
                conn.close()

    def cleanup_old_data(self, retention_days: int) -> tuple[int, int]:
        """Clean up old data beyond retention period.

        Args:
            retention_days: Number of days to retain data

        Returns:
            Tuple of (raw_deleted, aggregated_deleted)

        """
        cutoff_time = datetime.now() - timedelta(days=retention_days)

        with self._lock:
            conn = sqlite3.connect(self.db_path)
            try:
                cursor = conn.cursor()

                # Delete old raw metrics
                cursor.execute("DELETE FROM raw_metrics WHERE timestamp < ?", (cutoff_time.isoformat()))
                raw_deleted = cursor.rowcount

                # Delete old aggregated metrics
                cursor.execute("DELETE FROM aggregated_metrics WHERE timestamp < ?", (cutoff_time.isoformat()))
                aggregated_deleted = cursor.rowcount

                conn.commit()

                # Vacuum database to reclaim space
                conn.execute("VACUUM")

                return raw_deleted, aggregated_deleted

            except (sqlalchemy.exc.SQLAlchemyError, sqlite3.Error) as e:
                logger.exception("Error cleaning up old data: %s", e)
                conn.rollback()
                return 0, 0
            finally:
                conn.close()

    def get_storage_stats(self) -> dict[str, Any]:
        """Get storage statistics.

        Returns:
            Dictionary with storage statistics

        """
        with self._lock:
            conn = sqlite3.connect(self.db_path)
            try:
                cursor = conn.cursor()

                # Count raw metrics
                cursor.execute("SELECT COUNT(*) FROM raw_metrics")
                raw_count = cursor.fetchone()[0]

                # Count aggregated metrics
                cursor.execute("SELECT COUNT(*) FROM aggregated_metrics")
                agg_count = cursor.fetchone()[0]

                # Get database file size
                db_size = Path(self.db_path).stat().st_size if Path(self.db_path).exists() else 0

                # Get oldest and newest timestamps
                cursor.execute("SELECT MIN(timestamp), MAX(timestamp) FROM raw_metrics")
                raw_range = cursor.fetchone()

                return {
                    "raw_metrics_count": raw_count,
                    "aggregated_metrics_count": agg_count,
                    "database_size_bytes": db_size,
                    "oldest_metric": raw_range[0] if raw_range[0] else None,
                    "newest_metric": raw_range[1] if raw_range[1] else None,
                }

            except (FileNotFoundError, PermissionError, OSError) as e:
                logger.exception("Error getting storage stats: %s", e)
                return {}
            finally:
                conn.close()


class DataAggregator:
    """Processes and aggregates performance metrics with time-series storage."""

    def process_metrics(self, metrics: list[dict[str, Any]]) -> None:
        """Process and store metrics.

        Args:
            metrics: List of metric dictionaries to process

        """
        if not metrics:
            return

        try:
            # Add to buffer for batch processing
            self.buffer.add_metrics(metrics)

            with self._lock:
                self._metrics_processed += len(metrics)

            logger.debug("Buffered %s metrics for processing", len(metrics))

        except (OSError, FileNotFoundError) as e:
            logger.exception("Error processing metrics: %s", e)

    def _start_background_threads(self) -> None:
        """Start background processing threads."""
        # Aggregation thread
        self._aggregation_thread = threading.Thread(
            target=self._aggregation_loop, name="DataAggregator-Aggregation", daemon=True
        )
        self._aggregation_thread.start()

        # Cleanup thread
        self._cleanup_thread = threading.Thread(target=self._cleanup_loop, name="DataAggregator-Cleanup", daemon=True)
        self._cleanup_thread.start()

        logger.debug("Background threads started")

    def _aggregation_loop(self) -> None:
        """Background loop for processing and aggregating metrics."""
        while not self._stop_event.is_set():
            try:
                # Process buffered metrics
                buffered_metrics = self.buffer.get_and_clear()
                if buffered_metrics:
                    stored_count = self.storage.store_raw_metrics(buffered_metrics)

                    with self._lock:
                        self._metrics_stored += stored_count

                    logger.debug("Stored %s raw metrics", stored_count)

                # Perform aggregations
                self._perform_aggregations()

                # Sleep for a short interval
                self._stop_event.wait(5.0)  # Process every 5 seconds

            except Exception as e:
                logger.exception("Error in aggregation loop: %s", e)
                self._stop_event.wait(1.0)

    def _cleanup_loop(self) -> None:
        """Background loop for data cleanup."""
        while not self._stop_event.is_set():
            try:
                # Clean up old data
                raw_deleted, agg_deleted = self.storage.cleanup_old_data(self.config.retention_days)

                if raw_deleted > 0 or agg_deleted > 0:
                    logger.info("Cleaned up %s raw metrics and {agg_deleted} aggregated metrics", raw_deleted)

                # Sleep for an hour before next cleanup
                self._stop_event.wait(3600.0)

            except Exception as e:
                logger.exception("Error in cleanup loop: %s", e)
                self._stop_event.wait(300.0)  # Wait 5 minutes on error

    def _perform_aggregations(self) -> None:
        """Perform time-based aggregations."""
        now = datetime.now()

        # Short-term aggregation (1-minute)
        if (now - self._last_aggregation[AggregationLevel.SHORT_TERM]).total_seconds() >= 60:
            self._create_aggregations(AggregationLevel.SHORT_TERM, timedelta(minutes=1))
            self._last_aggregation[AggregationLevel.SHORT_TERM] = now

        # Medium-term aggregation (5-minute)
        if (now - self._last_aggregation[AggregationLevel.MEDIUM_TERM]).total_seconds() >= 300:
            self._create_aggregations(AggregationLevel.MEDIUM_TERM, timedelta(minutes=5))
            self._last_aggregation[AggregationLevel.MEDIUM_TERM] = now

        # Long-term aggregation (1-hour)
        if (now - self._last_aggregation[AggregationLevel.LONG_TERM]).total_seconds() >= 3600:
            self._create_aggregations(AggregationLevel.LONG_TERM, timedelta(hours=1))
            self._last_aggregation[AggregationLevel.LONG_TERM] = now

    def _create_aggregations(self, level: AggregationLevel, window: timedelta) -> None:
        """Create aggregations for a specific time window.

        Args:
            level: Aggregation level
            window: Time window for aggregation

        """
        try:
            end_time = datetime.now()
            start_time = end_time - window

            # Get raw metrics for the time window
            raw_metrics = self.storage.query_raw_metrics(start_time, end_time)

            if not raw_metrics:
                return

            # Group metrics by name and source
            grouped_metrics: dict[tuple[str, str], list[dict[str, Any]]] = {}
            for metric in raw_metrics:
                key = (metric["name"], metric["source"])
                if key not in grouped_metrics:
                    grouped_metrics[key] = []
                grouped_metrics[key].append(metric)

            # Create aggregated metrics
            aggregated_metrics: list[AggregatedMetric] = []
            for (name, source), metric_group in grouped_metrics.items():
                if not metric_group:
                    continue

                values = [m["value"] for m in metric_group]

                # Calculate statistics
                count = len(values)
                min_value = min(values)
                max_value = max(values)
                avg_value = sum(values) / count
                sum_value = sum(values)
                std_dev = statistics.stdev(values) if count > 1 else 0.0

                # Combine tags and metadata
                all_tags = {}
                all_metadata = {}
                for metric in metric_group:
                    all_tags.update(metric.get("tags", {}))
                    all_metadata.update(metric.get("metadata", {}))

                aggregated_metric = AggregatedMetric(
                    timestamp=end_time,
                    name=name,
                    source=source,
                    aggregation_level=level,
                    count=count,
                    min_value=min_value,
                    max_value=max_value,
                    avg_value=avg_value,
                    sum_value=sum_value,
                    std_dev=std_dev,
                    tags=all_tags,
                    metadata=all_metadata,
                )

                aggregated_metrics.append(aggregated_metric)

            # Store aggregated metrics
            if aggregated_metrics:
                stored_count = self.storage.store_aggregated_metrics(aggregated_metrics)

                with self._lock:
                    self._aggregations_created += stored_count

                logger.debug("Created %s {level.value} aggregations", stored_count)

        except Exception:
            logger.exception("Error creating %s aggregations: {e}", level.value)

    def get_metrics(
        self,
        start_time: datetime,
        end_time: datetime,
        aggregation_level: AggregationLevel = AggregationLevel.RAW,
        metric_name: str | None = None,
        source: str | None = None,
    ) -> list[dict[str, Any]]:
        """Get metrics from storage.

        Args:
            start_time: Start of time range
            end_time: End of time range
            aggregation_level: Level of aggregation
            metric_name: Optional metric name filter
            source: Optional source filter

        Returns:
            List of metrics

        """
        try:
            if aggregation_level == AggregationLevel.RAW:
                return self.storage.query_raw_metrics(start_time, end_time, metric_name, source)
            aggregated = self.storage.query_aggregated_metrics(
                start_time, end_time, aggregation_level, metric_name, source
            )

            # Convert to dictionary format
            result = []
            for metric in aggregated:
                result.append(
                    {
                        "timestamp": metric.timestamp.isoformat(),
                        "name": metric.name,
                        "source": metric.source,
                        "aggregation_level": metric.aggregation_level.value,
                        "count": metric.count,
                        "min_value": metric.min_value,
                        "max_value": metric.max_value,
                        "avg_value": metric.avg_value,
                        "sum_value": metric.sum_value,
                        "std_dev": metric.std_dev,
                        "tags": metric.tags,
                        "metadata": metric.metadata,
                    }
                )

            return result

        except (sqlalchemy.exc.SQLAlchemyError, sqlite3.Error) as e:
            logger.exception("Error getting metrics: %s", e)
            return []

    def get_aggregator_stats(self) -> dict[str, Any]:
        """Get aggregator statistics.

        Returns:
            Dictionary with aggregator statistics

        """
        with self._lock:
            stats = {
                "metrics_processed": self._metrics_processed,
                "metrics_stored": self._metrics_stored,
                "aggregations_created": self._aggregations_created,
                "buffer_size": self.buffer.size(),
                "last_aggregations": {
                    level.value: timestamp.isoformat() for level, timestamp in self._last_aggregation.items()
                },
            }

        # Add storage stats
        storage_stats = self.storage.get_storage_stats()
        stats.update(storage_stats)

        return stats

    def force_aggregation(self) -> dict[str, int]:
        """Force immediate aggregation of all levels.

        Returns:
            Dictionary with aggregation counts

        """
        try:
            results = {}

            # Force all aggregation levels
            for level in [AggregationLevel.SHORT_TERM, AggregationLevel.MEDIUM_TERM, AggregationLevel.LONG_TERM]:
                if level == AggregationLevel.SHORT_TERM:
                    window = timedelta(minutes=1)
                elif level == AggregationLevel.MEDIUM_TERM:
                    window = timedelta(minutes=5)
                else:
                    window = timedelta(hours=1)

                before_count = self._aggregations_created
                self._create_aggregations(level, window)
                after_count = self._aggregations_created

                results[level.value] = after_count - before_count

            return results

        except (RuntimeError, AttributeError) as e:
            logger.exception("Error forcing aggregation: %s", e)
            return {}

    def update_config(self, config) -> None:
        """Update aggregator configuration.

        Args:
            config: New monitoring configuration

        """
        self.config = config
        logger.debug("Data aggregator configuration updated")

    def cleanup(self) -> None:
        """Cleanup aggregator resources."""
        try:
            # Stop background threads
            self._stop_event.set()

            if self._aggregation_thread and self._aggregation_thread.is_alive():
                self._aggregation_thread.join(timeout=5.0)

            if self._cleanup_thread and self._cleanup_thread.is_alive():
                self._cleanup_thread.join(timeout=5.0)

            # Process any remaining buffered metrics
            buffered_metrics = self.buffer.get_and_clear()
            if buffered_metrics:
                self.storage.store_raw_metrics(buffered_metrics)
                logger.debug("Stored %s final metrics during cleanup", len(buffered_metrics))

            logger.debug("Data aggregator cleaned up")

        except Exception as e:
            logger.exception("Error during aggregator cleanup: %s", e)
