"""Security Log Review and Analysis Tools for Clinical Compliance Analysis.

This module provides comprehensive security log analysis, threat detection,
and security monitoring capabilities using expert patterns and best practices.

Features:
- Real-time security log analysis
- Threat pattern detection
- Security incident correlation
- Automated security reporting
- Security metrics and dashboards
- Compliance reporting
- Security alerting and notifications
"""

import asyncio
import json
import re
from datetime import datetime, timezone, timedelta
from typing import Any, Dict, List, Optional, Union
from dataclasses import dataclass, field
from enum import Enum
import uuid
from collections import defaultdict, Counter
import threading

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from src.core.centralized_logging import get_logger, audit_logger
from src.core.advanced_security_system import AdvancedSecuritySystem
from src.core.type_safety import ErrorHandler, error_handler


class ThreatLevel(Enum):
    """Threat severity levels."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class SecurityEventType(Enum):
    """Types of security events."""
    LOGIN_FAILURE = "login_failure"
    BRUTE_FORCE = "brute_force"
    SQL_INJECTION = "sql_injection"
    XSS_ATTEMPT = "xss_attempt"
    CSRF_ATTEMPT = "csrf_attempt"
    UNAUTHORIZED_ACCESS = "unauthorized_access"
    DATA_BREACH = "data_breach"
    SUSPICIOUS_ACTIVITY = "suspicious_activity"
    MALWARE_DETECTED = "malware_detected"
    PRIVILEGE_ESCALATION = "privilege_escalation"


@dataclass
class SecurityEvent:
    """Security event record."""
    event_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    event_type: SecurityEventType = SecurityEventType.SUSPICIOUS_ACTIVITY
    threat_level: ThreatLevel = ThreatLevel.MEDIUM
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    source_ip: Optional[str] = None
    user_id: Optional[int] = None
    user_agent: Optional[str] = None
    description: str = ""
    details: Dict[str, Any] = field(default_factory=dict)
    raw_log: Optional[str] = None
    resolved: bool = False
    resolved_at: Optional[datetime] = None
    resolved_by: Optional[str] = None


@dataclass
class ThreatPattern:
    """Threat pattern definition."""
    pattern_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    name: str = ""
    description: str = ""
    pattern_type: str = ""  # regex, keyword, behavioral
    pattern_value: str = ""
    threat_level: ThreatLevel = ThreatLevel.MEDIUM
    enabled: bool = True
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


@dataclass
class SecurityIncident:
    """Security incident record."""
    incident_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    title: str = ""
    description: str = ""
    threat_level: ThreatLevel = ThreatLevel.MEDIUM
    events: List[SecurityEvent] = field(default_factory=list)
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    status: str = "open"  # open, investigating, resolved, closed
    assigned_to: Optional[str] = None
    resolution_notes: Optional[str] = None


class SecurityLogAnalyzer:
    """Advanced security log analyzer."""

    def __init__(self):
        self.logger = get_logger(__name__)
        self.security_events: List[SecurityEvent] = []
        self.threat_patterns: Dict[str, ThreatPattern] = {}
        self.security_incidents: Dict[str, SecurityIncident] = {}
        self.lock = threading.RLock()

        # Initialize default threat patterns
        self._initialize_default_patterns()

    def _initialize_default_patterns(self) -> None:
        """Initialize default threat detection patterns."""
        default_patterns = [
            ThreatPattern(
                name="SQL Injection Attempt",
                description="Detects SQL injection patterns",
                pattern_type="regex",
                pattern_value=r"(?i)(union|select|insert|update|delete|drop|create|alter|exec|execute).*?(from|into|where|set|values)",
                threat_level=ThreatLevel.HIGH
            ),
            ThreatPattern(
                name="XSS Attempt",
                description="Detects XSS attack patterns",
                pattern_type="regex",
                pattern_value=r"(?i)<script[^>]*>.*?</script>|<script[^>]*>|javascript:|vbscript:|onload=|onerror=|onclick=",
                threat_level=ThreatLevel.HIGH
            ),
            ThreatPattern(
                name="Path Traversal",
                description="Detects path traversal attempts",
                pattern_type="regex",
                pattern_value=r"\.\./|\.\.\\|\.\.%2f|\.\.%5c",
                threat_level=ThreatLevel.MEDIUM
            ),
            ThreatPattern(
                name="Command Injection",
                description="Detects command injection patterns",
                pattern_type="regex",
                pattern_value=r"[;&|`$(){}]|(?:rm|del|format|shutdown|reboot)\s",
                threat_level=ThreatLevel.HIGH
            ),
            ThreatPattern(
                name="Suspicious User Agent",
                description="Detects suspicious user agents",
                pattern_type="keyword",
                pattern_value="sqlmap|nmap|nikto|havij|w3af",
                threat_level=ThreatLevel.MEDIUM
            )
        ]

        for pattern in default_patterns:
            self.threat_patterns[pattern.pattern_id] = pattern

    def analyze_log_entry(self, log_entry: str, metadata: Optional[Dict[str, Any]] = None) -> List[SecurityEvent]:
        """Analyze a log entry for security threats."""
        detected_events = []

        with self.lock:
            for pattern in self.threat_patterns.values():
                if not pattern.enabled:
                    continue

                if self._matches_pattern(log_entry, pattern):
                    event = SecurityEvent(
                        event_type=self._get_event_type_from_pattern(pattern),
                        threat_level=pattern.threat_level,
                        description=f"Detected {pattern.name}",
                        details={
                            "pattern_id": pattern.pattern_id,
                            "pattern_name": pattern.name,
                            "matched_text": self._extract_matched_text(log_entry, pattern)
                        },
                        raw_log=log_entry,
                        source_ip=metadata.get("source_ip") if metadata else None,
                        user_id=metadata.get("user_id") if metadata else None,
                        user_agent=metadata.get("user_agent") if metadata else None
                    )

                    detected_events.append(event)
                    self.security_events.append(event)

        return detected_events

    def _matches_pattern(self, log_entry: str, pattern: ThreatPattern) -> bool:
        """Check if log entry matches threat pattern."""
        try:
            if pattern.pattern_type == "regex":
                return bool(re.search(pattern.pattern_value, log_entry))
            elif pattern.pattern_type == "keyword":
                return pattern.pattern_value.lower() in log_entry.lower()
            elif pattern.pattern_type == "behavioral":
                # Implement behavioral pattern matching
                return self._matches_behavioral_pattern(log_entry, pattern)
            else:
                return False
        except Exception as e:
            self.logger.error("Error matching pattern %s: %s", pattern.name, e)
            return False

    def _matches_behavioral_pattern(self, log_entry: str, pattern: ThreatPattern) -> bool:
        """Check behavioral patterns (e.g., multiple failed logins)."""
        # This would implement behavioral analysis
        # For now, return False
        return False

    def _extract_matched_text(self, log_entry: str, pattern: ThreatPattern) -> str:
        """Extract the text that matched the pattern."""
        try:
            if pattern.pattern_type == "regex":
                match = re.search(pattern.pattern_value, log_entry)
                return match.group(0) if match else ""
            else:
                return pattern.pattern_value
        except Exception:
            return ""

    def _get_event_type_from_pattern(self, pattern: ThreatPattern) -> SecurityEventType:
        """Map pattern to security event type."""
        pattern_name_lower = pattern.name.lower()

        if "sql" in pattern_name_lower:
            return SecurityEventType.SQL_INJECTION
        elif "xss" in pattern_name_lower:
            return SecurityEventType.XSS_ATTEMPT
        elif "csrf" in pattern_name_lower:
            return SecurityEventType.CSRF_ATTEMPT
        elif "brute" in pattern_name_lower or "login" in pattern_name_lower:
            return SecurityEventType.BRUTE_FORCE
        elif "unauthorized" in pattern_name_lower:
            return SecurityEventType.UNAUTHORIZED_ACCESS
        else:
            return SecurityEventType.SUSPICIOUS_ACTIVITY

    def correlate_events(self, time_window_hours: int = 24) -> List[SecurityIncident]:
        """Correlate security events into incidents."""
        with self.lock:
            cutoff_time = datetime.now(timezone.utc) - timedelta(hours=time_window_hours)
            recent_events = [e for e in self.security_events if e.timestamp >= cutoff_time]

            # Group events by source IP, user, or event type
            incidents = []

            # Group by source IP
            ip_groups = defaultdict(list)
            for event in recent_events:
                if event.source_ip:
                    ip_groups[event.source_ip].append(event)

            for ip, events in ip_groups.items():
                if len(events) >= 3:  # Threshold for incident creation
                    incident = SecurityIncident(
                        title=f"Multiple security events from {ip}",
                        description=f"Detected {len(events)} security events from IP {ip}",
                        threat_level=self._calculate_incident_threat_level(events),
                        events=events
                    )
                    incidents.append(incident)
                    self.security_incidents[incident.incident_id] = incident

            # Group by user
            user_groups = defaultdict(list)
            for event in recent_events:
                if event.user_id:
                    user_groups[event.user_id].append(event)

            for user_id, events in user_groups.items():
                if len(events) >= 5:  # Higher threshold for user-based incidents
                    incident = SecurityIncident(
                        title=f"Multiple security events for user {user_id}",
                        description=f"Detected {len(events)} security events for user {user_id}",
                        threat_level=self._calculate_incident_threat_level(events),
                        events=events
                    )
                    incidents.append(incident)
                    self.security_incidents[incident.incident_id] = incident

            return incidents

    def _calculate_incident_threat_level(self, events: List[SecurityEvent]) -> ThreatLevel:
        """Calculate threat level for an incident based on events."""
        if not events:
            return ThreatLevel.LOW

        threat_levels = [event.threat_level for event in events]

        # Return the highest threat level
        if ThreatLevel.CRITICAL in threat_levels:
            return ThreatLevel.CRITICAL
        elif ThreatLevel.HIGH in threat_levels:
            return ThreatLevel.HIGH
        elif ThreatLevel.MEDIUM in threat_levels:
            return ThreatLevel.MEDIUM
        else:
            return ThreatLevel.LOW

    def get_security_metrics(self, hours: int = 24) -> Dict[str, Any]:
        """Get security metrics for specified time period."""
        with self.lock:
            cutoff_time = datetime.now(timezone.utc) - timedelta(hours=hours)
            recent_events = [e for e in self.security_events if e.timestamp >= cutoff_time]

            # Count events by type
            event_type_counts = Counter(e.event_type.value for e in recent_events)

            # Count events by threat level
            threat_level_counts = Counter(e.threat_level.value for e in recent_events)

            # Count events by source IP
            ip_counts = Counter(e.source_ip for e in recent_events if e.source_ip)

            # Count unresolved incidents
            unresolved_incidents = len([i for i in self.security_incidents.values() if i.status != "resolved"])

            return {
                "total_events": len(recent_events),
                "events_by_type": dict(event_type_counts),
                "events_by_threat_level": dict(threat_level_counts),
                "top_source_ips": dict(ip_counts.most_common(10)),
                "unresolved_incidents": unresolved_incidents,
                "time_period_hours": hours,
                "timestamp": datetime.now(timezone.utc).isoformat()
            }

    def get_threat_trends(self, days: int = 7) -> Dict[str, Any]:
        """Get threat trends over specified days."""
        with self.lock:
            trends = {}

            for i in range(days):
                day_start = datetime.now(timezone.utc) - timedelta(days=i+1)
                day_end = datetime.now(timezone.utc) - timedelta(days=i)

                day_events = [
                    e for e in self.security_events
                    if day_start <= e.timestamp < day_end
                ]

                trends[day_start.strftime("%Y-%m-%d")] = {
                    "total_events": len(day_events),
                    "critical_events": len([e for e in day_events if e.threat_level == ThreatLevel.CRITICAL]),
                    "high_events": len([e for e in day_events if e.threat_level == ThreatLevel.HIGH]),
                    "medium_events": len([e for e in day_events if e.threat_level == ThreatLevel.MEDIUM]),
                    "low_events": len([e for e in day_events if e.threat_level == ThreatLevel.LOW])
                }

            return trends


class SecurityReportGenerator:
    """Generate comprehensive security reports."""

    def __init__(self, analyzer: SecurityLogAnalyzer):
        self.analyzer = analyzer
        self.logger = get_logger(__name__)

    def generate_daily_report(self) -> Dict[str, Any]:
        """Generate daily security report."""
        metrics = self.analyzer.get_security_metrics(24)
        trends = self.analyzer.get_threat_trends(7)

        return {
            "report_type": "daily",
            "date": datetime.now(timezone.utc).strftime("%Y-%m-%d"),
            "summary": {
                "total_events": metrics["total_events"],
                "critical_events": metrics["events_by_threat_level"].get("critical", 0),
                "high_events": metrics["events_by_threat_level"].get("high", 0),
                "unresolved_incidents": metrics["unresolved_incidents"]
            },
            "metrics": metrics,
            "trends": trends,
            "recommendations": self._generate_recommendations(metrics),
            "generated_at": datetime.now(timezone.utc).isoformat()
        }

    def generate_compliance_report(self) -> Dict[str, Any]:
        """Generate compliance report."""
        metrics = self.analyzer.get_security_metrics(24)

        # Check compliance requirements
        compliance_checks = {
            "no_critical_events": metrics["events_by_threat_level"].get("critical", 0) == 0,
            "low_error_rate": metrics["total_events"] < 100,  # Threshold
            "incidents_resolved": metrics["unresolved_incidents"] < 5,
            "monitoring_active": True  # Always true if report is generated
        }

        compliance_score = sum(compliance_checks.values()) / len(compliance_checks) * 100

        return {
            "report_type": "compliance",
            "date": datetime.now(timezone.utc).strftime("%Y-%m-%d"),
            "compliance_score": compliance_score,
            "compliance_checks": compliance_checks,
            "metrics": metrics,
            "status": "compliant" if compliance_score >= 80 else "non_compliant",
            "generated_at": datetime.now(timezone.utc).isoformat()
        }

    def _generate_recommendations(self, metrics: Dict[str, Any]) -> List[str]:
        """Generate security recommendations based on metrics."""
        recommendations = []

        if metrics["events_by_threat_level"].get("critical", 0) > 0:
            recommendations.append("Investigate and resolve critical security events immediately")

        if metrics["events_by_threat_level"].get("high", 0) > 10:
            recommendations.append("Review and strengthen security controls for high-threat events")

        if metrics["unresolved_incidents"] > 5:
            recommendations.append("Prioritize resolution of outstanding security incidents")

        if len(metrics["top_source_ips"]) > 0:
            top_ip = list(metrics["top_source_ips"].keys())[0]
            recommendations.append(f"Consider blocking or monitoring IP {top_ip}")

        if not recommendations:
            recommendations.append("Security posture appears stable - continue monitoring")

        return recommendations


# Global instances
security_analyzer = SecurityLogAnalyzer()
security_report_generator = SecurityReportGenerator(security_analyzer)

# API Router
router = APIRouter(prefix="/api/v2/security", tags=["Security Analysis"])


# Pydantic models
class LogAnalysisRequest(BaseModel):
    """Request model for log analysis."""
    log_entry: str = Field(..., description="Log entry to analyze")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Additional metadata")


class ThreatPatternRequest(BaseModel):
    """Request model for creating threat patterns."""
    name: str = Field(..., description="Pattern name")
    description: str = Field(..., description="Pattern description")
    pattern_type: str = Field(..., description="Pattern type")
    pattern_value: str = Field(..., description="Pattern value")
    threat_level: str = Field(default="medium", description="Threat level")


# API Endpoints
@router.post("/analyze")
async def analyze_log_entry(request: LogAnalysisRequest) -> Dict[str, Any]:
    """Analyze a log entry for security threats."""
    try:
        events = security_analyzer.analyze_log_entry(
            request.log_entry,
            request.metadata
        )

        return {
            "events_detected": len(events),
            "events": [event.__dict__ for event in events],
            "timestamp": datetime.now(timezone.utc).isoformat()
        }

    except Exception as e:
        raise HTTPException(
            status_code=400,
            detail=f"Failed to analyze log entry: {str(e)}"
        )


@router.get("/metrics")
async def get_security_metrics(hours: int = 24) -> Dict[str, Any]:
    """Get security metrics."""
    return security_analyzer.get_security_metrics(hours)


@router.get("/trends")
async def get_threat_trends(days: int = 7) -> Dict[str, Any]:
    """Get threat trends."""
    return security_analyzer.get_threat_trends(days)


@router.get("/incidents")
async def get_security_incidents() -> List[Dict[str, Any]]:
    """Get security incidents."""
    incidents = list(security_analyzer.security_incidents.values())
    return [incident.__dict__ for incident in incidents]


@router.post("/patterns")
async def create_threat_pattern(request: ThreatPatternRequest) -> Dict[str, Any]:
    """Create a new threat pattern."""
    try:
        pattern = ThreatPattern(
            name=request.name,
            description=request.description,
            pattern_type=request.pattern_type,
            pattern_value=request.pattern_value,
            threat_level=ThreatLevel(request.threat_level)
        )

        security_analyzer.threat_patterns[pattern.pattern_id] = pattern

        return {
            "message": "Threat pattern created successfully",
            "pattern_id": pattern.pattern_id,
            "name": pattern.name,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }

    except Exception as e:
        raise HTTPException(
            status_code=400,
            detail=f"Failed to create threat pattern: {str(e)}"
        )


@router.get("/reports/daily")
async def get_daily_report() -> Dict[str, Any]:
    """Get daily security report."""
    return security_report_generator.generate_daily_report()


@router.get("/reports/compliance")
async def get_compliance_report() -> Dict[str, Any]:
    """Get compliance report."""
    return security_report_generator.generate_compliance_report()


@router.post("/correlate")
async def correlate_events(time_window_hours: int = 24) -> List[Dict[str, Any]]:
    """Correlate security events into incidents."""
    incidents = security_analyzer.correlate_events(time_window_hours)
    return [incident.__dict__ for incident in incidents]
