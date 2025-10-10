"""Scheduler for automated ML training and model updates."""

import logging
from datetime import datetime
from typing import Any

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.interval import IntervalTrigger

from src.ml.trainer import MLTrainingPipeline

logger = logging.getLogger(__name__)


class MLScheduler:
    """Manages scheduled ML training and model updates."""

    def __init__(self,
                 training_pipeline: MLTrainingPipeline | None = None,
                 scheduler: AsyncIOScheduler | None = None):
        """Initialize the ML scheduler.

        Args:
            training_pipeline: MLTrainingPipeline instance for training
            scheduler: AsyncIOScheduler instance (creates new if None)

        """
        self.training_pipeline = training_pipeline or MLTrainingPipeline()
        self.scheduler = scheduler or AsyncIOScheduler()
        self.is_running = False

        # Training job configuration
        self.training_job_id = "ml_training_job"
        self.health_check_job_id = "ml_health_check_job"

        # Default schedule: daily at 2 AM
        self.default_training_schedule = CronTrigger(hour=2, minute=0)

        # Health check: every 6 hours
        self.health_check_schedule = IntervalTrigger(hours=6)

    def start(self,
              training_schedule: CronTrigger | None = None,
              enable_health_checks: bool = True) -> None:
        """Start the ML scheduler.

        Args:
            training_schedule: Custom training schedule (uses default if None)
            enable_health_checks: Whether to enable periodic health checks

        """
        if self.is_running:
            logger.warning("ML scheduler is already running")
            return

        try:
            # Add training job
            schedule = training_schedule or self.default_training_schedule
            self.scheduler.add_job(
                func=self._run_training_job,
                trigger=schedule,
                id=self.training_job_id,
                name="ML Model Training",
                replace_existing=True,
                max_instances=1,  # Prevent overlapping training jobs
            )

            # Add health check job if enabled
            if enable_health_checks:
                self.scheduler.add_job(
                    func=self._run_health_check,
                    trigger=self.health_check_schedule,
                    id=self.health_check_job_id,
                    name="ML System Health Check",
                    replace_existing=True,
                    max_instances=1,
                )

            # Start the scheduler
            self.scheduler.start()
            self.is_running = True

            logger.info("ML scheduler started with training schedule: %s", schedule)
            if enable_health_checks:
                logger.info("Health checks enabled every %s", self.health_check_schedule.interval)

        except Exception as e:
            logger.exception("Failed to start ML scheduler: %s", e)
            raise

    def stop(self) -> None:
        """Stop the ML scheduler."""
        if not self.is_running:
            logger.warning("ML scheduler is not running")
            return

        try:
            self.scheduler.shutdown(wait=True)
            self.is_running = False
            logger.info("ML scheduler stopped")
        except Exception as e:
            logger.exception("Error stopping ML scheduler: %s", e)

    async def _run_training_job(self) -> None:
        """Execute the ML training job."""
        job_start = datetime.now()
        logger.info("Starting scheduled ML training job")

        try:
            # Run the training pipeline
            result = await self.training_pipeline.fine_tune_model_with_feedback()

            # Log results
            duration = (datetime.now() - job_start).total_seconds()
            logger.info("ML training job completed in %ss: {result[", duration, status']}")

            # Log detailed results based on status
            if result["status"] == "completed":
                self._log_training_success(result, duration)
            elif result["status"] == "insufficient_data":
                self._log_insufficient_data(result)
            elif result["status"] == "skipped":
                self._log_training_skipped(result)
            elif result["status"] == "error":
                self._log_training_error(result)

        except (sqlalchemy.exc.SQLAlchemyError, sqlite3.Error) as e:
            duration = (datetime.now() - job_start).total_seconds()
            logger.error("ML training job failed after %ss: {e}", duration, exc_info=True)

    async def _run_health_check(self) -> None:
        """Execute ML system health check."""
        logger.info("Running ML system health check")

        try:
            health_status = await self._check_system_health()

            if health_status["overall_status"] == "healthy":
                logger.info("ML system health check: All systems healthy")
            elif health_status["overall_status"] == "warning":
                logger.warning("ML system health check: Warnings detected - %s", health_status['warnings'])
            else:
                logger.error("ML system health check: Issues detected - %s", health_status['errors'])

        except (ValueError, TypeError, AttributeError) as e:
            logger.error("ML health check failed: %s", e, exc_info=True)

    async def _check_system_health(self) -> dict[str, Any]:
        """Check the health of the ML system."""
        health_status: dict[str, Any] = {
            "overall_status": "healthy",
            "warnings": [],
            "errors": [],
            "metrics": {},
        }

        try:
            # Check training data availability
            training_data = self.training_pipeline.calibration_trainer.get_training_data(min_samples=1)
            data_count = len(training_data)
            health_status["metrics"]["training_data_count"] = data_count

            if data_count < 10:
                health_status["warnings"].append(f"Low training data count: {data_count}")
                health_status["overall_status"] = "warning"

            # Check model file existence
            models_dir = self.training_pipeline.models_dir
            production_model = models_dir / "confidence_calibrator.pkl"

            if production_model.exists():
                # Check model age
                model_age = datetime.now() - datetime.fromtimestamp(production_model.stat().st_mtime)
                health_status["metrics"]["model_age_days"] = model_age.days

                if model_age.days > 30:
                    health_status["warnings"].append(f"Model is {model_age.days} days old")
                    health_status["overall_status"] = "warning"
            else:
                health_status["errors"].append("No production model found")
                health_status["overall_status"] = "error"

            # Check training metadata
            metadata_file = models_dir / "training_metadata.json"
            if metadata_file.exists():
                import json
                with open(metadata_file) as f:
                    metadata = json.load(f)

                last_training = datetime.fromisoformat(metadata.get("last_training", "2000-01-01"))
                days_since_training = (datetime.now() - last_training).days
                health_status["metrics"]["days_since_last_training"] = days_since_training

                if days_since_training > 14:
                    health_status["warnings"].append(f"No training for {days_since_training} days")
                    health_status["overall_status"] = "warning"
            else:
                health_status["warnings"].append("No training metadata found")
                if health_status["overall_status"] == "healthy":
                    health_status["overall_status"] = "warning"

        except Exception as e:
            health_status["errors"].append(f"Health check error: {e!s}")
            health_status["overall_status"] = "error"

        return health_status

    def _log_training_success(self, result: dict[str, Any], duration: float) -> None:
        """Log successful training results."""
        eval_results = result.get("evaluation_results", {})
        deployment_results = result.get("deployment_results", {})

        ece_improvement = eval_results.get("ece_improvement", 0)
        deployed = deployment_results.get("deployed", False)

        logger.info("Training successful - ECE improvement: %s, ", ece_improvement * 100, 
                   f"Deployed: {deployed}, Samples: {result.get('samples_used', 0)}")

        if deployed:
            logger.info("New model deployed: %s", deployment_results.get('model_path', 'unknown'))

    def _log_insufficient_data(self, result: dict[str, Any]) -> None:
        """Log insufficient data results."""
        samples = result.get("samples_collected", 0)
        logger.info("Training skipped - insufficient data: %s samples collected", samples)

    def _log_training_skipped(self, result: dict[str, Any]) -> None:
        """Log skipped training results."""
        next_due = result.get("next_training_due", "unknown")
        logger.info("Training skipped - not due until: %s", next_due)

    def _log_training_error(self, result: dict[str, Any]) -> None:
        """Log training error results."""
        error_msg = result.get("message", "Unknown error")
        logger.error("Training failed: %s", error_msg)

    def trigger_immediate_training(self) -> None:
        """Trigger an immediate training job (async)."""
        if not self.is_running:
            logger.error("Cannot trigger training - scheduler not running")
            return

        try:
            # Schedule immediate training job
            self.scheduler.add_job(
                func=self._run_training_job,
                trigger="date",  # Run once immediately
                id=f"{self.training_job_id}_immediate",
                name="Immediate ML Training",
                replace_existing=True,
            )
            logger.info("Immediate training job scheduled")
        except Exception as e:
            logger.exception("Failed to schedule immediate training: %s", e)

    def get_next_training_time(self) -> datetime | None:
        """Get the next scheduled training time."""
        if not self.is_running:
            return None

        try:
            job = self.scheduler.get_job(self.training_job_id)
            if job and job.next_run_time:
                return job.next_run_time
        except Exception as e:
            logger.exception("Error getting next training time: %s", e)

        return None

    def get_scheduler_status(self) -> dict[str, Any]:
        """Get the current status of the scheduler."""
        status = {
            "is_running": self.is_running,
            "jobs": [],
            "next_training": None,
        }

        if self.is_running:
            try:
                # Get job information
                for job in self.scheduler.get_jobs():
                    job_info = {
                        "id": job.id,
                        "name": job.name,
                        "next_run_time": job.next_run_time.isoformat() if job.next_run_time else None,
                        "trigger": str(job.trigger),
                    }
                    status["jobs"].append(job_info)

                # Get next training time
                next_training = self.get_next_training_time()
                if next_training:
                    status["next_training"] = next_training.isoformat()

            except Exception as e:
                logger.exception("Error getting scheduler status: %s", e)
                status["error"] = str(e)

        return status


# Global scheduler instance for application-wide use
_global_scheduler: MLScheduler | None = None


def get_ml_scheduler() -> MLScheduler:
    """Get the global ML scheduler instance."""
    global _global_scheduler
    if _global_scheduler is None:
        _global_scheduler = MLScheduler()
    return _global_scheduler


def start_ml_scheduler(training_schedule: CronTrigger | None = None,
                      enable_health_checks: bool = True) -> None:
    """Start the global ML scheduler."""
    scheduler = get_ml_scheduler()
    scheduler.start(training_schedule, enable_health_checks)


def stop_ml_scheduler() -> None:
    """Stop the global ML scheduler."""
    global _global_scheduler
    if _global_scheduler:
        _global_scheduler.stop()
        _global_scheduler = None
