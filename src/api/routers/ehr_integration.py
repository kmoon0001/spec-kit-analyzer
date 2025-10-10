"""EHR Integration API Router
Provides APIs for integrating with Electronic Health Record systems.
"""

import logging
from datetime import datetime
from typing import Any

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, status
from pydantic import BaseModel, Field

from src.auth import get_current_user
from src.core.compliance_sync_service import compliance_sync_service
from src.core.ehr_connector import ehr_connector
from src.database.models import User

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/ehr", tags=["EHR Integration"])


class EHRConnectionConfig(BaseModel):
    """EHR connection configuration."""

    system_type: str = Field(..., description="EHR system type (epic, cerner, allscripts, athenahealth, nethealth, etc.)")
    endpoint_url: str = Field(..., description="EHR system API endpoint")
    client_id: str = Field(..., description="OAuth client ID")
    client_secret: str = Field(..., description="OAuth client secret")
    scope: str = Field(default="patient/*.read", description="FHIR scopes")
    facility_id: str = Field(..., description="Healthcare facility identifier")
    department_codes: list[str] = Field(default=[], description="Department codes to sync")


class EHRSyncRequest(BaseModel):
    """EHR data synchronization request."""

    patient_ids: list[str] | None = Field(default=None, description="Specific patient IDs to sync")
    date_range_start: datetime | None = Field(default=None, description="Start date for data sync")
    date_range_end: datetime | None = Field(default=None, description="End date for data sync")
    document_types: list[str] = Field(default=["progress_notes", "evaluations", "treatment_plans"],
                                    description="Types of documents to sync")
    auto_analyze: bool = Field(default=False, description="Automatically analyze synced documents")


class EHRDocumentMetadata(BaseModel):
    """EHR document metadata."""

    document_id: str
    patient_id: str
    document_type: str
    created_date: datetime
    author: str
    department: str
    status: str
    compliance_analyzed: bool = False


@router.post("/connect")
async def connect_ehr_system(
    config: EHRConnectionConfig,
    current_user: User = Depends(get_current_user),
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

    except Exception as e:
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

    except Exception as e:
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
    sync_task_id: str,
    current_user: User = Depends(get_current_user),
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

    except Exception as e:
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

    except Exception as e:
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
        analysis_task_id = f"ehr_analysis_{document_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

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
            days=days,
            department=department,
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

    except Exception as e:
        logger.exception("Failed to disconnect EHR system: %s", e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to disconnect EHR system: {e!s}",
        ) from e


@router.get("/supported-systems")
async def get_supported_ehr_systems() -> dict[str, Any]:
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
                "capabilities": ["patient_data", "clinical_notes", "medications", "allergies"],
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
