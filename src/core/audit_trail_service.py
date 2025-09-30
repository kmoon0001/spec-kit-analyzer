import logging
import json
from datetime import datetime
from typing import Dict, Any

class AuditTrailService:
    """
    A service to log all processing steps for regulatory compliance.
    """

    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.audit_log_file = self.config.get("audit_log_file", "audit_trail.log")
        self._configure_logger()

    def _configure_logger(self):
        """
        Configures a dedicated logger for the audit trail.
        """
        self.audit_logger = logging.getLogger("audit_trail")
        self.audit_logger.setLevel(logging.INFO)
        # Prevent audit logs from propagating to the root logger
        self.audit_logger.propagate = False

        # Add a file handler if not already present
        if not self.audit_logger.handlers:
            handler = logging.FileHandler(self.audit_log_file)
            formatter = logging.Formatter('%(asctime)s - %(message)s')
            handler.setFormatter(formatter)
            self.audit_logger.addHandler(handler)

    def log_pipeline_start(self, file_path: str, file_type: str):
        """Logs the start of the pipeline."""
        log_entry = {
            "event": "pipeline_start",
            "file_path": file_path,
            "file_type": file_type,
            "timestamp": datetime.utcnow().isoformat(),
        }
        self.audit_logger.info(json.dumps(log_entry))

    def log_pipeline_end(self, final_context: Dict[str, Any]):
        """Logs the end of the pipeline."""
        log_entry = {
            "event": "pipeline_end",
            "status": "success" if "error" not in final_context else "failure",
            "timestamp": datetime.utcnow().isoformat(),
        }
        if "error" in final_context:
            log_entry["error"] = final_context["error"]
        self.audit_logger.info(json.dumps(log_entry))

    def log_step(self, step_name: str, context: Dict[str, Any], status: str, error: str = None):
        """Logs the completion of a pipeline step."""
        log_entry = {
            "event": "pipeline_step",
            "step_name": step_name,
            "status": status,
            "timestamp": datetime.utcnow().isoformat(),
        }
        if error:
            log_entry["error"] = error

        # We can decide to log some context, but be careful not to log PHI
        # For example, we can log the keys of the context
        log_entry["context_keys"] = list(context.keys())

        self.audit_logger.info(json.dumps(log_entry))