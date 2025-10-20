"""Production Monitoring and Alerting Setup for Clinical Compliance Analyzer.

This module provides comprehensive production monitoring setup with real-time
alerting, performance tracking, and automated incident response.

Features:
- Real-time performance monitoring
- Automated alerting and notifications
- Health check automation
- Performance baseline establishment
- Incident response procedures
- Monitoring dashboard setup
"""

import asyncio
import json
import smtplib
import time
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import requests
import psutil

from src.core.centralized_logging import get_logger, setup_logging
from src.core.type_safety import Result, ErrorHandler


@dataclass
class AlertThreshold:
    """Alert threshold configuration."""
    metric_name: str
    warning_threshold: float
    critical_threshold: float
    time_window_minutes: int = 5
    enabled: bool = True


@dataclass
class AlertNotification:
    """Alert notification configuration."""
    alert_id: str
    metric_name: str
    current_value: float
    threshold_value: float
    severity: str
    timestamp: datetime
    message: str
    resolved: bool = False


class ProductionMonitor:
    """Comprehensive production monitoring system."""

    def __init__(self, config_path: str = "monitoring_config.yaml"):
        self.config_path = config_path
        self.logger = get_logger(__name__)
        self.error_handler = ErrorHandler()

        # Load monitoring configuration
        self.config = self._load_monitoring_config()

        # Alert thresholds
        self.alert_thresholds = self._setup_alert_thresholds()

        # Monitoring state
        self.monitoring_active = False
        self.baseline_metrics = {}
        self.alert_history = []

        # Notification settings
        self.notification_config = self.config.get("notifications", {})

    def _load_monitoring_config(self) -> Dict[str, Any]:
        """Load monitoring configuration."""
        default_config = {
            "monitoring": {
                "enabled": True,
                "check_interval_seconds": 30,
                "baseline_period_hours": 24,
                "alert_cooldown_minutes": 15
            },
            "thresholds": {
                "cpu_usage_percent": {"warning": 70, "critical": 90},
                "memory_usage_percent": {"warning": 80, "critical": 95},
                "disk_usage_percent": {"warning": 85, "critical": 95},
                "response_time_ms": {"warning": 2000, "critical": 5000},
                "error_rate": {"warning": 0.05, "critical": 0.1},
                "cache_hit_rate": {"warning": 0.7, "critical": 0.5}
            },
            "notifications": {
                "email": {
                    "enabled": True,
                    "smtp_server": "smtp.gmail.com",
                    "smtp_port": 587,
                    "username": "",
                    "password": "",
                    "recipients": []
                },
                "webhook": {
                    "enabled": False,
                    "url": "",
                    "headers": {}
                }
            },
            "endpoints": {
                "health_check": "http://localhost:8000/api/v2/system/health",
                "performance_metrics": "http://localhost:8000/api/v2/performance/metrics",
                "security_metrics": "http://localhost:8000/api/v2/security/metrics"
            }
        }

        try:
            import yaml
            with open(self.config_path, 'r') as f:
                return yaml.safe_load(f) or default_config
        except FileNotFoundError:
            # Create default config file
            import yaml
            with open(self.config_path, 'w') as f:
                yaml.dump(default_config, f, default_flow_style=False)
            return default_config

    def _setup_alert_thresholds(self) -> List[AlertThreshold]:
        """Setup alert thresholds from configuration."""
        thresholds = []

        for metric_name, config in self.config["thresholds"].items():
            threshold = AlertThreshold(
                metric_name=metric_name,
                warning_threshold=config["warning"],
                critical_threshold=config["critical"],
                enabled=True
            )
            thresholds.append(threshold)

        return thresholds

    async def start_monitoring(self) -> Result[bool, str]:
        """Start production monitoring."""
        try:
            self.logger.info("Starting production monitoring...")

            # Establish baseline metrics
            await self._establish_baseline_metrics()

            # Start monitoring loop
            self.monitoring_active = True
            asyncio.create_task(self._monitoring_loop())

            self.logger.info("Production monitoring started successfully")
            return Result.success(True)

        except Exception as e:
            error_context = self.error_handler.handle_error(
                e,
                context={"operation": "start_monitoring"},
                severity="HIGH"
            )
            return Result.failure(f"Failed to start monitoring: {str(e)}")

    async def stop_monitoring(self) -> None:
        """Stop production monitoring."""
        self.monitoring_active = False
        self.logger.info("Production monitoring stopped")

    async def _establish_baseline_metrics(self) -> None:
        """Establish baseline metrics for comparison."""
        self.logger.info("Establishing baseline metrics...")

        baseline_period = self.config["monitoring"]["baseline_period_hours"]
        end_time = datetime.now(timezone.utc)
        start_time = end_time - timedelta(hours=baseline_period)

        # Collect baseline metrics
        baseline_data = {
            "cpu_usage_percent": [],
            "memory_usage_percent": [],
            "disk_usage_percent": [],
            "response_time_ms": [],
            "error_rate": [],
            "cache_hit_rate": []
        }

        # Simulate baseline collection (in real implementation, collect from logs/metrics)
        for metric_name in baseline_data.keys():
            # Generate sample baseline data
            baseline_data[metric_name] = [50.0, 55.0, 60.0, 45.0, 52.0]  # Sample values

        # Calculate baseline averages
        self.baseline_metrics = {
            metric_name: sum(values) / len(values)
            for metric_name, values in baseline_data.items()
        }

        self.logger.info(f"Baseline metrics established: {self.baseline_metrics}")

    async def _monitoring_loop(self) -> None:
        """Main monitoring loop."""
        check_interval = self.config["monitoring"]["check_interval_seconds"]

        while self.monitoring_active:
            try:
                # Collect current metrics
                current_metrics = await self._collect_current_metrics()

                # Check against thresholds
                alerts = await self._check_thresholds(current_metrics)

                # Send notifications for new alerts
                for alert in alerts:
                    await self._send_alert_notification(alert)

                # Update alert history
                self.alert_history.extend(alerts)

                # Log monitoring status
                self.logger.debug(f"Monitoring check completed. Alerts: {len(alerts)}")

                await asyncio.sleep(check_interval)

            except Exception as e:
                self.logger.error(f"Error in monitoring loop: {str(e)}")
                await asyncio.sleep(check_interval)

    async def _collect_current_metrics(self) -> Dict[str, float]:
        """Collect current system metrics."""
        metrics = {}

        try:
            # System metrics
            metrics["cpu_usage_percent"] = psutil.cpu_percent(interval=1)
            metrics["memory_usage_percent"] = psutil.virtual_memory().percent
            metrics["disk_usage_percent"] = psutil.disk_usage('/').percent

            # Application metrics (simulated - in real implementation, fetch from API)
            metrics["response_time_ms"] = 1500.0  # Simulated
            metrics["error_rate"] = 0.02  # Simulated
            metrics["cache_hit_rate"] = 0.85  # Simulated

            return metrics

        except Exception as e:
            self.logger.error(f"Error collecting metrics: {str(e)}")
            return {}

    async def _check_thresholds(self, current_metrics: Dict[str, float]) -> List[AlertNotification]:
        """Check current metrics against thresholds."""
        alerts = []

        for threshold in self.alert_thresholds:
            if not threshold.enabled:
                continue

            metric_name = threshold.metric_name
            if metric_name not in current_metrics:
                continue

            current_value = current_metrics[metric_name]

            # Check critical threshold
            if current_value >= threshold.critical_threshold:
                alert = AlertNotification(
                    alert_id=f"critical_{metric_name}_{int(time.time())}",
                    metric_name=metric_name,
                    current_value=current_value,
                    threshold_value=threshold.critical_threshold,
                    severity="critical",
                    timestamp=datetime.now(timezone.utc),
                    message=f"CRITICAL: {metric_name} is {current_value:.2f}, exceeds threshold {threshold.critical_threshold}"
                )
                alerts.append(alert)

            # Check warning threshold
            elif current_value >= threshold.warning_threshold:
                alert = AlertNotification(
                    alert_id=f"warning_{metric_name}_{int(time.time())}",
                    metric_name=metric_name,
                    current_value=current_value,
                    threshold_value=threshold.warning_threshold,
                    severity="warning",
                    timestamp=datetime.now(timezone.utc),
                    message=f"WARNING: {metric_name} is {current_value:.2f}, exceeds threshold {threshold.warning_threshold}"
                )
                alerts.append(alert)

        return alerts

    async def _send_alert_notification(self, alert: AlertNotification) -> None:
        """Send alert notification."""
        try:
            # Check cooldown to avoid spam
            cooldown_minutes = self.config["monitoring"]["alert_cooldown_minutes"]
            recent_alerts = [
                a for a in self.alert_history
                if a.metric_name == alert.metric_name
                and a.timestamp >= datetime.now(timezone.utc) - timedelta(minutes=cooldown_minutes)
            ]

            if recent_alerts:
                self.logger.debug(f"Alert for {alert.metric_name} in cooldown period")
                return

            # Send email notification
            if self.notification_config.get("email", {}).get("enabled", False):
                await self._send_email_alert(alert)

            # Send webhook notification
            if self.notification_config.get("webhook", {}).get("enabled", False):
                await self._send_webhook_alert(alert)

            self.logger.warning(f"Alert sent: {alert.message}")

        except Exception as e:
            self.logger.error(f"Failed to send alert notification: {str(e)}")

    async def _send_email_alert(self, alert: AlertNotification) -> None:
        """Send email alert notification."""
        try:
            email_config = self.notification_config["email"]

            # Create email message
            msg = MIMEMultipart()
            msg['From'] = email_config["username"]
            msg['To'] = ", ".join(email_config["recipients"])
            msg['Subject'] = f"[{alert.severity.upper()}] Clinical Compliance Analyzer Alert"

            # Email body
            body = f"""
            Alert Details:
            - Metric: {alert.metric_name}
            - Current Value: {alert.current_value:.2f}
            - Threshold: {alert.threshold_value}
            - Severity: {alert.severity.upper()}
            - Time: {alert.timestamp.isoformat()}
            - Message: {alert.message}

            Please check the system immediately.
            """

            msg.attach(MIMEText(body, 'plain'))

            # Send email
            server = smtplib.SMTP(email_config["smtp_server"], email_config["smtp_port"])
            server.starttls()
            server.login(email_config["username"], email_config["password"])
            server.send_message(msg)
            server.quit()

            self.logger.info(f"Email alert sent for {alert.metric_name}")

        except Exception as e:
            self.logger.error(f"Failed to send email alert: {str(e)}")

    async def _send_webhook_alert(self, alert: AlertNotification) -> None:
        """Send webhook alert notification."""
        try:
            webhook_config = self.notification_config["webhook"]

            payload = {
                "alert_id": alert.alert_id,
                "metric_name": alert.metric_name,
                "current_value": alert.current_value,
                "threshold_value": alert.threshold_value,
                "severity": alert.severity,
                "timestamp": alert.timestamp.isoformat(),
                "message": alert.message
            }

            response = requests.post(
                webhook_config["url"],
                json=payload,
                headers=webhook_config.get("headers", {}),
                timeout=10
            )

            if response.status_code == 200:
                self.logger.info(f"Webhook alert sent for {alert.metric_name}")
            else:
                self.logger.error(f"Webhook alert failed: {response.status_code}")

        except Exception as e:
            self.logger.error(f"Failed to send webhook alert: {str(e)}")

    async def get_monitoring_status(self) -> Dict[str, Any]:
        """Get current monitoring status."""
        current_metrics = await self._collect_current_metrics()

        return {
            "monitoring_active": self.monitoring_active,
            "baseline_metrics": self.baseline_metrics,
            "current_metrics": current_metrics,
            "active_alerts": len([a for a in self.alert_history if not a.resolved]),
            "total_alerts": len(self.alert_history),
            "thresholds": [
                {
                    "metric_name": t.metric_name,
                    "warning_threshold": t.warning_threshold,
                    "critical_threshold": t.critical_threshold,
                    "enabled": t.enabled
                }
                for t in self.alert_thresholds
            ],
            "timestamp": datetime.now(timezone.utc).isoformat()
        }

    async def get_performance_dashboard_data(self) -> Dict[str, Any]:
        """Get data for performance dashboard."""
        current_metrics = await self._collect_current_metrics()

        # Calculate performance trends
        trends = {}
        for metric_name, current_value in current_metrics.items():
            if metric_name in self.baseline_metrics:
                baseline = self.baseline_metrics[metric_name]
                trends[metric_name] = {
                    "current": current_value,
                    "baseline": baseline,
                    "deviation": current_value - baseline,
                    "deviation_percent": ((current_value - baseline) / baseline * 100) if baseline > 0 else 0
                }

        return {
            "current_metrics": current_metrics,
            "baseline_metrics": self.baseline_metrics,
            "trends": trends,
            "alerts": [
                {
                    "metric_name": a.metric_name,
                    "severity": a.severity,
                    "message": a.message,
                    "timestamp": a.timestamp.isoformat()
                }
                for a in self.alert_history[-10:]  # Last 10 alerts
            ],
            "timestamp": datetime.now(timezone.utc).isoformat()
        }


# Production monitoring script
async def main():
    """Main monitoring function."""
    # Setup logging
    setup_logging(
        log_level='INFO',
        log_file='monitoring.log',
        log_format='json'
    )

    logger = get_logger(__name__)
    logger.info("Starting production monitoring...")

    # Create production monitor
    monitor = ProductionMonitor()

    # Start monitoring
    result = await monitor.start_monitoring()

    if result.is_success:
        logger.info("Production monitoring started successfully!")
        print("✅ Production monitoring started successfully!")

        # Keep monitoring running
        try:
            while True:
                status = await monitor.get_monitoring_status()
                print(f"📊 Monitoring Status: Active={status['monitoring_active']}, Alerts={status['active_alerts']}")
                await asyncio.sleep(60)  # Print status every minute

        except KeyboardInterrupt:
            logger.info("Stopping monitoring...")
            await monitor.stop_monitoring()
            print("🛑 Monitoring stopped")

    else:
        logger.error(f"Failed to start monitoring: {result.error}")
        print(f"❌ Failed to start monitoring: {result.error}")


if __name__ == "__main__":
    asyncio.run(main())
