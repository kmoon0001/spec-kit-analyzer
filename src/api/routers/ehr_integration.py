"""Enhanced EHR Integration API Router

Provides comprehensive APIs for integrating with Electronic Health Record systems
with advanced features including real-time sync, data mapping, and compliance monitoring.

Enhanced Features:
- Real-time data synchronization
- Advanced data mapping and transformation
- Compliance monitoring and alerts
- Data quality validation
- Audit trail and logging
- Performance monitoring
- Error handling and recovery
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional
from enum import Enum

import requests
from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, status
from pydantic import BaseModel, Field
from requests.exceptions import HTTPError

from src.auth import get_current_user
from src.core.compliance_sync_service import compliance_sync_service
from src.core.ehr_connector import ehr_connector
from src.database.models import User

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/ehr", tags=["EHR Integration"])


class EHRSystemType(Enum):
    """Supported EHR system types."""
    EPIC = "epic"
    CERNER = "cerner"
    ALLSCRIPTS = "allscripts"
    ATHENAHEALTH = "athenahealth"
    NEXTHEALTH = "nexhealth"
    GENERIC_FHIR = "generic_fhir"


class SyncStatus(Enum):
    """EHR sync status."""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    PARTIAL = "partial"


class DataQualityLevel(Enum):
    """Data quality levels."""
    EXCELLENT = "excellent"
    GOOD = "good"
    FAIR = "fair"
    POOR = "poor"


class EHRConnectionConfig(BaseModel):
    """Enhanced EHR connection configuration."""

    system_type: str = Field(
        ...,
        description="EHR system type (epic, cerner, allscripts, athenahealth, nexhealth, generic_fhir)",
    )
    endpoint_url: str = Field(..., description="EHR system API endpoint")
    client_id: str = Field(..., description="OAuth client ID")
    client_secret: str = Field(..., description="OAuth client secret")
    scope: str = Field(default="patient/*.read", description="FHIR scopes")
    facility_id: str = Field(..., description="Healthcare facility identifier")
    department_codes: List[str] = Field(
        default=[], description="Department codes to sync"
    )
    sync_frequency_minutes: int = Field(
        default=60, description="Automatic sync frequency in minutes"
    )
    enable_real_time_sync: bool = Field(
        default=False, description="Enable real-time data synchronization"
    )
    data_retention_days: int = Field(
        default=365, description="Data retention period in days"
    )
    compliance_threshold: float = Field(
        default=0.8, description="Minimum compliance score threshold for alerts"
    )


class EHRSyncRequest(BaseModel):
    """Enhanced EHR data synchronization request."""

    patient_ids: Optional[List[str]] = Field(
        default=None, description="Specific patient IDs to sync"
    )
    date_range_start: Optional[datetime] = Field(
        default=None, description="Start date for data sync"
    )
    date_range_end: Optional[datetime] = Field(
        default=None, description="End date for data sync"
    )
    document_types: List[str] = Field(
        default=["progress_notes", "evaluations", "treatment_plans"],
        description="Types of documents to sync",
    )
    auto_analyze: bool = Field(
        default=False, description="Automatically analyze synced documents"
    )
    sync_mode: str = Field(
        default="incremental", description="Sync mode: incremental, full, or delta"
    )
    priority: str = Field(
        default="normal", description="Sync priority: low, normal, high, urgent"
    )
    validate_data_quality: bool = Field(
        default=True, description="Validate data quality during sync"
    )


class EHRDocumentMetadata(BaseModel):
    """Enhanced EHR document metadata."""

    document_id: str
    patient_id: str
    document_type: str
    created_date: datetime
    author: str
    department: str
    status: str
    compliance_analyzed: bool = False
    data_quality_score: Optional[float] = None
    sync_timestamp: Optional[datetime] = None
    last_modified: Optional[datetime] = None
    version: Optional[str] = None
    tags: List[str] = Field(default_factory=list)


class EHRSyncResult(BaseModel):
    """EHR synchronization result."""

    sync_id: str
    status: SyncStatus
    start_time: datetime
    end_time: Optional[datetime] = None
    documents_synced: int = 0
    documents_failed: int = 0
    data_quality_score: Optional[float] = None
    errors: List[str] = Field(default_factory=list)
    warnings: List[str] = Field(default_factory=list)
    performance_metrics: Dict[str, Any] = Field(default_factory=dict)


class EHRComplianceAlert(BaseModel):
    """EHR compliance alert."""

    alert_id: str
    patient_id: str
    document_id: str
    alert_type: str
    severity: str
    message: str
    compliance_score: float
    threshold: float
    created_at: datetime
    acknowledged: bool = False
    resolved: bool = False


class EHRDataQualityReport(BaseModel):
    """EHR data quality report."""

    report_id: str
    generated_at: datetime
    overall_quality_score: float
    quality_level: DataQualityLevel
    metrics: Dict[str, Any] = Field(default_factory=dict)
    issues: List[Dict[str, Any]] = Field(default_factory=list)
    recommendations: List[str] = Field(default_factory=list)


@router.get("/sync-status/{sync_id}")
async def get_sync_status(
    sync_id: str,
    current_user: User = Depends(get_current_user)
) -> EHRSyncResult:
    """Get detailed status of an EHR synchronization operation.

    Args:
        sync_id: Synchronization ID
        current_user: Current authenticated user

    Returns:
        Detailed sync status and metrics
    """
    try:
        # Get sync status from EHR connector
        sync_status = await ehr_connector.get_sync_status(sync_id)

        if not sync_status:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Sync operation not found: {sync_id}"
            )

        return EHRSyncResult(**sync_status)

    except HTTPException:
        raise
    except Exception as e:
        logger.exception("Failed to get sync status for %s: %s", sync_id, e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get sync status: {str(e)}"
        )


@router.get("/compliance-alerts")
async def get_compliance_alerts(
    severity: Optional[str] = None,
    acknowledged: Optional[bool] = None,
    limit: int = 50,
    current_user: User = Depends(get_current_user)
) -> List[EHRComplianceAlert]:
    """Get EHR compliance alerts with optional filtering.

    Args:
        severity: Filter by alert severity
        acknowledged: Filter by acknowledgment status
        limit: Maximum number of alerts to return
        current_user: Current authenticated user

    Returns:
        List of compliance alerts
    """
    try:
        # Get compliance alerts from EHR connector
        alerts = await ehr_connector.get_compliance_alerts(
            severity=severity,
            acknowledged=acknowledged,
            limit=limit
        )

        return [EHRComplianceAlert(**alert) for alert in alerts]

    except Exception as e:
        logger.exception("Failed to get compliance alerts: %s", e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get compliance alerts: {str(e)}"
        )


@router.post("/compliance-alerts/{alert_id}/acknowledge")
async def acknowledge_compliance_alert(
    alert_id: str,
    current_user: User = Depends(get_current_user)
) -> Dict[str, Any]:
    """Acknowledge a compliance alert.

    Args:
        alert_id: Alert ID to acknowledge
        current_user: Current authenticated user

    Returns:
        Acknowledgment confirmation
    """
    try:
        # Acknowledge alert
        success = await ehr_connector.acknowledge_alert(alert_id, current_user.id)

        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Alert not found: {alert_id}"
            )

        return {
            "alert_id": alert_id,
            "acknowledged": True,
            "acknowledged_by": current_user.username,
            "acknowledged_at": datetime.now().isoformat()
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.exception("Failed to acknowledge alert %s: %s", alert_id, e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to acknowledge alert: {str(e)}"
        )


@router.get("/data-quality-report")
async def get_data_quality_report(
    time_range_days: int = 30,
    current_user: User = Depends(get_current_user)
) -> EHRDataQualityReport:
    """Get comprehensive EHR data quality report.

    Args:
        time_range_days: Number of days to analyze
        current_user: Current authenticated user

    Returns:
        Data quality report
    """
    try:
        # Generate data quality report
        report = await ehr_connector.generate_data_quality_report(time_range_days)

        return EHRDataQualityReport(**report)

    except Exception as e:
        logger.exception("Failed to generate data quality report: %s", e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate data quality report: {str(e)}"
        )


@router.get("/performance-metrics")
async def get_ehr_performance_metrics(
    time_range_days: int = 7,
    current_user: User = Depends(get_current_user)
) -> Dict[str, Any]:
    """Get EHR integration performance metrics.

    Args:
        time_range_days: Number of days to analyze
        current_user: Current authenticated user

    Returns:
        Performance metrics
    """
    try:
        # Get performance metrics
        metrics = await ehr_connector.get_performance_metrics(time_range_days)

        return {
            "time_range_days": time_range_days,
            "metrics": metrics,
            "generated_at": datetime.now().isoformat()
        }

    except Exception as e:
        logger.exception("Failed to get performance metrics: %s", e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get performance metrics: {str(e)}"
        )


@router.post("/real-time-sync/enable")
async def enable_real_time_sync(
    config: Dict[str, Any],
    current_user: User = Depends(get_current_user)
) -> Dict[str, Any]:
    """Enable real-time EHR data synchronization.

    Args:
        config: Real-time sync configuration
        current_user: Current authenticated user

    Returns:
        Real-time sync status
    """
    if not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin privileges required for real-time sync configuration"
        )

    try:
        # Enable real-time sync
        result = await ehr_connector.enable_real_time_sync(config)

        logger.info("Real-time sync enabled by user %s", current_user.username)

        return {
            "real_time_sync_enabled": True,
            "configuration": config,
            "enabled_by": current_user.username,
            "enabled_at": datetime.now().isoformat(),
            "status": result
        }

    except Exception as e:
        logger.exception("Failed to enable real-time sync: %s", e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to enable real-time sync: {str(e)}"
        )


@router.post("/real-time-sync/disable")
async def disable_real_time_sync(
    current_user: User = Depends(get_current_user)
) -> Dict[str, Any]:
    """Disable real-time EHR data synchronization.

    Args:
        current_user: Current authenticated user

    Returns:
        Real-time sync status
    """
    if not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin privileges required for real-time sync configuration"
        )

    try:
        # Disable real-time sync
        result = await ehr_connector.disable_real_time_sync()

        logger.info("Real-time sync disabled by user %s", current_user.username)

        return {
            "real_time_sync_enabled": False,
            "disabled_by": current_user.username,
            "disabled_at": datetime.now().isoformat(),
            "status": result
        }

    except Exception as e:
        logger.exception("Failed to disable real-time sync: %s", e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to disable real-time sync: {str(e)}"
        )


@router.get("/supported-systems")
async def get_supported_ehr_systems() -> Dict[str, Any]:
    """Get list of supported EHR systems and their capabilities.

    Returns:
        Supported EHR systems information
    """
    try:
        supported_systems = {
            "epic": {
                "name": "Epic",
                "version": "R4",
                "capabilities": [
                    "FHIR R4",
                    "OAuth 2.0",
                    "SMART on FHIR",
                    "Real-time sync",
                    "Bulk data export"
                ],
                "document_types": [
                    "progress_notes",
                    "evaluations",
                    "treatment_plans",
                    "discharge_summaries"
                ]
            },
            "cerner": {
                "name": "Cerner",
                "version": "R4",
                "capabilities": [
                    "FHIR R4",
                    "OAuth 2.0",
                    "SMART on FHIR",
                    "Real-time sync"
                ],
                "document_types": [
                    "progress_notes",
                    "evaluations",
                    "treatment_plans"
                ]
            },
            "allscripts": {
                "name": "Allscripts",
                "version": "R4",
                "capabilities": [
                    "FHIR R4",
                    "OAuth 2.0",
                    "Bulk data export"
                ],
                "document_types": [
                    "progress_notes",
                    "evaluations"
                ]
            },
            "athenahealth": {
                "name": "athenahealth",
                "version": "R4",
                "capabilities": [
                    "FHIR R4",
                    "OAuth 2.0",
                    "SMART on FHIR"
                ],
                "document_types": [
                    "progress_notes",
                    "evaluations",
                    "treatment_plans"
                ]
            },
            "generic_fhir": {
                "name": "Generic FHIR",
                "version": "R4",
                "capabilities": [
                    "FHIR R4",
                    "OAuth 2.0"
                ],
                "document_types": [
                    "progress_notes",
                    "evaluations",
                    "treatment_plans"
                ]
            }
        }

        return {
            "supported_systems": supported_systems,
            "total_systems": len(supported_systems),
            "last_updated": datetime.now().isoformat()
        }

    except Exception as e:
        logger.exception("Failed to get supported EHR systems: %s", e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get supported systems: {str(e)}"
        )


@router.get("/audit-trail")
async def get_ehr_audit_trail(
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    action_type: Optional[str] = None,
    limit: int = 100,
    current_user: User = Depends(get_current_user)
) -> Dict[str, Any]:
    """Get EHR integration audit trail.

    Args:
        start_date: Start date for audit trail
        end_date: End date for audit trail
        action_type: Filter by action type
        limit: Maximum number of entries
        current_user: Current authenticated user

    Returns:
        Audit trail entries
    """
    try:
        # Get audit trail
        audit_entries = await ehr_connector.get_audit_trail(
            start_date=start_date,
            end_date=end_date,
            action_type=action_type,
            limit=limit
        )

        return {
            "audit_entries": audit_entries,
            "total_entries": len(audit_entries),
            "filters": {
                "start_date": start_date.isoformat() if start_date else None,
                "end_date": end_date.isoformat() if end_date else None,
                "action_type": action_type
            },
            "generated_at": datetime.now().isoformat()
        }

    except Exception as e:
        logger.exception("Failed to get audit trail: %s", e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get audit trail: {str(e)}"
        )


@router.post("/connect")
async def connect_ehr_system(
    config: EHRConnectionConfig, current_user: User = Depends(get_current_user)
) -> dict[str, Any]:
    """Connect to an EHR system and validate the connection.

    Requires admin privileges for security.
    """
    if not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin privileges required for EHR integration",
        )

    try:
        logger.info("Attempting EHR connection to %s system", config.system_type)

        # Validate and establish connection
        connection_result = await ehr_connector.connect(
            system_type=config.system_type,
            endpoint_url=config.endpoint_url,
            client_id=config.client_id,
            client_secret=config.client_secret,
            scope=config.scope,
            facility_id=config.facility_id,
        )

        if connection_result.get("success"):
            logger.info("Successfully connected to %s EHR system", config.system_type)
            return {
                "success": True,
                "message": f"Successfully connected to {config.system_type} EHR system",
                "connection_id": connection_result.get("connection_id"),
                "capabilities": connection_result.get("capabilities", []),
                "connected_at": datetime.now().isoformat(),
            }
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to connect to EHR system: {connection_result.get('error', 'Unknown error')}",
        )

    except (requests.RequestException, ConnectionError, TimeoutError, HTTPError) as e:
        logger.exception("EHR connection failed: %s", e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"EHR connection failed: {e!s}",
        ) from e


@router.get("/status")
async def get_ehr_connection_status(
    current_user: User = Depends(get_current_user),
) -> dict[str, Any]:
    """Get the current EHR connection status."""
    try:
        status_info = await ehr_connector.get_connection_status()

        return {
            "connected": status_info.get("connected", False),
            "system_type": status_info.get("system_type"),
            "facility_id": status_info.get("facility_id"),
            "last_sync": status_info.get("last_sync"),
            "connection_health": status_info.get("health", "unknown"),
            "capabilities": status_info.get("capabilities", []),
            "error_count": status_info.get("error_count", 0),
        }

    except (requests.RequestException, ConnectionError, TimeoutError, HTTPError) as e:
        logger.exception("Failed to get EHR status: %s", e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get EHR status: {e!s}",
        ) from e


@router.post("/sync")
async def sync_ehr_data(
    sync_request: EHRSyncRequest,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
) -> dict[str, Any]:
    """Synchronize data from the connected EHR system.

    This operation runs in the background to avoid timeout issues.
    """
    try:
        # Validate EHR connection
        connection_status = await ehr_connector.get_connection_status()
        if not connection_status.get("connected"):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No active EHR connection. Please connect to an EHR system first.",
            )

        # Start background sync task
        sync_task_id = f"ehr_sync_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

        background_tasks.add_task(
            compliance_sync_service.sync_ehr_documents,
            sync_task_id=sync_task_id,
            patient_ids=sync_request.patient_ids,
            date_range_start=sync_request.date_range_start,
            date_range_end=sync_request.date_range_end,
            document_types=sync_request.document_types,
            auto_analyze=sync_request.auto_analyze,
            user_id=str(current_user.id),
        )

        logger.info("Started EHR sync task: %s", sync_task_id)

        return {
            "success": True,
            "message": "EHR data synchronization started",
            "sync_task_id": sync_task_id,
            "estimated_duration": "5-15 minutes",
            "status_endpoint": f"/ehr/sync/{sync_task_id}/status",
        }

    except Exception as e:
        logger.exception("EHR sync failed to start: %s", e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to start EHR sync: {e!s}",
        ) from e


@router.get("/sync/{sync_task_id}/status")
async def get_sync_status(
    sync_task_id: str, current_user: User = Depends(get_current_user)
) -> dict[str, Any]:
    """Get the status of an EHR synchronization task."""
    try:
        sync_status = await compliance_sync_service.get_sync_status(sync_task_id)

        if not sync_status:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Sync task {sync_task_id} not found",
            )

        return sync_status

    except (requests.RequestException, ConnectionError, TimeoutError, HTTPError) as e:
        logger.exception("Failed to get sync status: %s", e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get sync status: {e!s}",
        ) from e


@router.get("/documents")
async def list_ehr_documents(
    limit: int = 50,
    offset: int = 0,
    document_type: str | None = None,
    analyzed_only: bool = False,
    current_user: User = Depends(get_current_user),
) -> dict[str, Any]:
    """List documents synchronized from the EHR system."""
    try:
        documents = await ehr_connector.list_synced_documents(
            limit=limit,
            offset=offset,
            document_type=document_type,
            analyzed_only=analyzed_only,
        )

        return {
            "documents": documents.get("documents", []),
            "total_count": documents.get("total_count", 0),
            "limit": limit,
            "offset": offset,
            "has_more": documents.get("has_more", False),
        }

    except (requests.RequestException, ConnectionError, TimeoutError, HTTPError) as e:
        logger.exception("Failed to list EHR documents: %s", e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list EHR documents: {e!s}",
        ) from e


@router.post("/documents/{document_id}/analyze")
async def analyze_ehr_document(
    document_id: str,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
) -> dict[str, Any]:
    """Analyze a specific EHR document for compliance."""
    try:
        # Validate document exists
        document = await ehr_connector.get_document(document_id)
        if not document:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Document {document_id} not found",
            )

        # Start background analysis
        analysis_task_id = (
            f"ehr_analysis_{document_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        )

        background_tasks.add_task(
            compliance_sync_service.analyze_ehr_document,
            document_id=document_id,
            analysis_task_id=analysis_task_id,
            user_id=str(current_user.id),
        )

        logger.info("Started EHR document analysis: %s", analysis_task_id)

        return {
            "success": True,
            "message": f"Analysis started for document {document_id}",
            "analysis_task_id": analysis_task_id,
            "document_id": document_id,
            "estimated_duration": "2-5 minutes",
        }

    except Exception as e:
        logger.exception("Failed to start EHR document analysis: %s", e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to start document analysis: {e!s}",
        ) from e


@router.get("/analytics/compliance-trends")
async def get_ehr_compliance_trends(
    days: int = 30,
    department: str | None = None,
    current_user: User = Depends(get_current_user),
) -> dict[str, Any]:
    """Get compliance trends from EHR-synchronized documents."""
    try:
        trends = await compliance_sync_service.get_compliance_trends(
            days=days, department=department
        )

        return {
            "trends": trends,
            "period_days": days,
            "department": department,
            "generated_at": datetime.now().isoformat(),
        }

    except Exception as e:
        logger.exception("Failed to get compliance trends: %s", e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get compliance trends: {e!s}",
        ) from e


@router.post("/disconnect")
async def disconnect_ehr_system(
    current_user: User = Depends(get_current_user),
) -> dict[str, Any]:
    """Disconnect from the current EHR system."""
    if not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin privileges required for EHR integration",
        )

    try:
        await ehr_connector.disconnect()

        logger.info("EHR system disconnected")

        return {
            "success": True,
            "message": "Successfully disconnected from EHR system",
            "disconnected_at": datetime.now().isoformat(),
        }

    except (ImportError, ModuleNotFoundError) as e:
        logger.exception("Failed to disconnect EHR system: %s", e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to disconnect EHR system: {e!s}",
        ) from e


@router.get("/supported-systems")
async def get_supported_ehr_systems(
    current_user: User = Depends(get_current_user),
) -> dict[str, Any]:
    """Get list of supported EHR systems."""
    return {
        "supported_systems": [
            {
                "system_type": "epic",
                "name": "Epic Systems",
                "description": "Epic EHR integration via FHIR R4",
                "capabilities": ["patient_data", "clinical_notes", "orders", "results"],
            },
            {
                "system_type": "cerner",
                "name": "Oracle Cerner",
                "description": "Cerner EHR integration via FHIR R4",
                "capabilities": [
                    "patient_data",
                    "clinical_notes",
                    "medications",
                    "allergies",
                ],
            },
            {
                "system_type": "allscripts",
                "name": "Allscripts",
                "description": "Allscripts EHR integration",
                "capabilities": ["patient_data", "clinical_notes", "prescriptions"],
            },
            {
                "system_type": "athenahealth",
                "name": "athenahealth",
                "description": "athenahealth EHR integration",
                "capabilities": ["patient_data", "clinical_notes", "appointments"],
            },
            {
                "system_type": "generic_fhir",
                "name": "Generic FHIR",
                "description": "Generic FHIR R4 compliant system",
                "capabilities": ["patient_data", "clinical_notes", "observations"],
            },
        ],
        "fhir_version": "R4",
        "security_standards": ["OAuth 2.0", "SMART on FHIR", "HL7 FHIR Security"],
    }
