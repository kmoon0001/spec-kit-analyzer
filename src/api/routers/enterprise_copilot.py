"""Enterprise Copilot API Router - Clean Version

Provides AI-powered enterprise assistance and automation capabilities.
"""

import logging
from datetime import datetime
from typing import Any

import PIL
import requests
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from requests.exceptions import HTTPError

from src.auth import get_current_user
from src.core.enterprise_copilot_service import enterprise_copilot_service
from src.core.performance_monitor import performance_monitor
from src.database.models import User

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/enterprise-copilot")


class CopilotQuery(BaseModel):
    """Enterprise copilot query."""

    query: str = Field(..., description="Natural language query or request")
    context: dict[str, Any] | None = Field(default=None, description="Additional context")
    department: str | None = Field(default=None, description="User department")
    priority: str = Field(default="normal", description="Query priority (low, normal, high)")


class WorkflowAutomationRequest(BaseModel):
    """Workflow automation request."""

    workflow_type: str = Field(..., description="Type of workflow to automate")
    parameters: dict[str, Any] = Field(..., description="Workflow parameters")
    schedule: str | None = Field(default=None, description="Automation schedule")


@router.post("/ask")
async def ask_copilot(
    query: CopilotQuery,
    current_user: User = Depends(get_current_user)) -> dict[str, Any]:
    """Ask the Enterprise Copilot a question or request assistance.

    The copilot can help with compliance questions, workflow automation,
    data analysis, and general healthcare documentation guidance.
    """
    try:
        logger.info("Copilot query from %s: {query.query[:100]}...", current_user.username)

        # Process the query through the enhanced enterprise copilot service with performance monitoring
        with performance_monitor.track_operation("enterprise_copilot", "process_query"):
            response = await enterprise_copilot_service.process_query(
                query=query.query,
                context=query.context or {},
                user_id=current_user.id,
                department=query.department,
                priority=query.priority)

        return {
            "success": True,
            "response": response.get("answer", "I'm sorry, I couldn't process that request."),
            "confidence": response.get("confidence", 0.0),
            "sources": response.get("sources", []),
            "suggested_actions": response.get("suggested_actions", []),
            "follow_up_questions": response.get("follow_up_questions", []),
            "processing_time_ms": response.get("processing_time_ms", 0),
            "query_id": response.get("query_id"),
        }

    except (requests.RequestException, ConnectionError, TimeoutError, HTTPError) as e:
        logger.exception("Copilot query failed: %s", e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Copilot query failed: {e!s}") from e


@router.get("/capabilities")
async def get_copilot_capabilities() -> dict[str, Any]:
    """Get the current capabilities of the Enterprise Copilot."""
    return {
        "capabilities": [
            {
                "name": "Compliance Guidance",
                "description": "Provides expert guidance on healthcare compliance requirements",
                "examples": ["What are the Medicare documentation requirements for PT?"],
            },
            {
                "name": "Workflow Automation",
                "description": "Automates repetitive compliance and documentation tasks",
                "examples": ["Automate daily compliance checks", "Schedule report generation"],
            },
            {
                "name": "Data Analysis",
                "description": "Analyzes compliance data to identify trends and insights",
                "examples": ["Show me compliance trends for the last quarter"],
            },
            {
                "name": "Best Practices",
                "description": "Recommends industry best practices for documentation",
                "examples": ["What are best practices for progress note documentation?"],
            },
        ],
        "supported_queries": [
            "compliance questions",
            "documentation guidance",
            "workflow automation",
            "data analysis requests",
            "best practice recommendations",
            "regulatory updates",
        ],
        "response_formats": [
            "text_answer",
            "structured_data",
            "action_items",
            "recommendations",
        ],
    }


@router.post("/workflow/automate")
async def create_workflow_automation(
    request: WorkflowAutomationRequest,
    current_user: User = Depends(get_current_user)) -> dict[str, Any]:
    """Create a new workflow automation.

    Supported workflow types:
    - compliance_monitoring: Automated compliance checks
    - report_generation: Scheduled report creation
    - data_synchronization: Automated data sync processes
    - alert_management: Automated alert processing
    - quality_assurance: Automated QA processes
    """
    if not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Workflow automation requires admin privileges")

    try:
        logger.info("Creating workflow automation: %s", request.workflow_type)

        # Create the automation through the copilot service
        automation_result = await enterprise_copilot_service.create_workflow_automation(
            workflow_type=request.workflow_type,
            parameters=request.parameters,
            schedule=request.schedule,
            user_id=current_user.id)

        return {
            "success": True,
            "automation_id": automation_result.get("automation_id"),
            "status": "created",
            "workflow_type": request.workflow_type,
            "schedule": request.schedule,
            "next_run": automation_result.get("next_run"),
            "message": f"Workflow automation '{request.workflow_type}' created successfully",
        }

    except (requests.RequestException, ConnectionError, TimeoutError, HTTPError) as e:
        logger.exception("Failed to create workflow automation: %s", e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create workflow automation: {e!s}") from e


@router.get("/workflow/list")
async def list_workflow_automations(
    current_user: User = Depends(get_current_user)) -> dict[str, Any]:
    """List all workflow automations."""
    try:
        automations = await enterprise_copilot_service.list_workflow_automations(
            user_id=current_user.id,
            include_system=current_user.is_admin)

        return {
            "success": True,
            "automations": automations,
            "total_count": len(automations),
        }

    except (PIL.UnidentifiedImageError, OSError, ValueError) as e:
        logger.exception("Failed to list workflow automations: %s", e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list workflow automations: {e!s}") from e


@router.get("/help/topics")
async def get_help_topics() -> dict[str, Any]:
    """Get available help topics and examples."""
    return {
        "help_topics": [
            {
                "category": "Compliance Questions",
                "examples": [
                    "What are the Medicare documentation requirements for physical therapy?",
                    "How should I document functional outcomes?",
                    "What compliance issues should I watch for in progress notes?",
                ],
            },
            {
                "category": "Workflow Automation",
                "examples": [
                    "Automate daily compliance checks for my department",
                    "Schedule weekly compliance reports",
                    "Set up alerts for documentation deadlines",
                ],
            },
            {
                "category": "Data Analysis",
                "examples": [
                    "Show me compliance trends for the last quarter",
                    "Analyze documentation quality metrics",
                    "Compare performance across departments",
                ],
            },
            {
                "category": "Best Practices",
                "examples": [
                    "What are best practices for progress note documentation?",
                    "How can I improve my documentation efficiency?",
                    "What templates should I use for evaluations?",
                ],
            },
        ],
        "quick_actions": [
            "Check compliance status",
            "Generate compliance report",
            "Review documentation guidelines",
            "Get improvement recommendations",
        ],
    }


@router.get("/status")
async def get_copilot_status() -> dict[str, Any]:
    """Get Enterprise Copilot system status."""
    try:
        status_info = await enterprise_copilot_service.get_system_status()

        return {
            "status": "operational",
            "version": "1.0.0",
            "uptime": status_info.get("uptime", "unknown"),
            "active_sessions": status_info.get("active_sessions", 0),
            "total_queries_today": status_info.get("total_queries_today", 0),
            "average_response_time_ms": status_info.get("average_response_time_ms", 0),
            "capabilities_enabled": True,
            "last_updated": datetime.now().isoformat(),
        }

    except (requests.RequestException, ConnectionError, TimeoutError, HTTPError) as e:
        logger.exception("Failed to get copilot status: %s", e)
        return {
            "status": "error",
            "error": str(e),
            "last_updated": datetime.now().isoformat(),
        }
