"""
Enterprise Copilot API Router
Provides AI-powered enterprise assistance and automation capabilities.
"""

import logging
from typing import Dict, List, Any, Optional
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks, Query
from pydantic import BaseModel, Field

from src.auth import get_current_user
from src.database.models import User
from src.core.enterprise_copilot_service import enterprise_copilot_service
from src.core.ml_trend_predictor import ml_trend_predictor
from src.core.workflow_automation import workflow_automation
from src.core.enhanced_error_handler import enhanced_error_handler
from src.core.performance_monitor import performance_monitor
from src.core.multi_agent_orchestrator import multi_agent_orchestrator

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/copilot", tags=["Enterprise Copilot"])


class CopilotQuery(BaseModel):
    """Enterprise copilot query."""
    query: str = Field(..., description="Natural language query or request")
    context: Optional[Dict[str, Any]] = Field(default=None, description="Additional context")
    department: Optional[str] = Field(default=None, description="Department context")
    priority: str = Field(default="normal", description="Query priority (low, normal, high, urgent)")


class WorkflowAutomationRequest(BaseModel):
    """Workflow automation request."""
    workflow_type: str = Field(..., description="Type of workflow to automate")
    parameters: Dict[str, Any] = Field(..., description="Workflow parameters")
    schedule: Optional[str] = Field(default=None, description="Cron schedule for recurring workflows")
    enabled: bool = Field(default=True, description="Whether the workflow is enabled")


class ComplianceInsightRequest(BaseModel):
    """Compliance insight generation request."""
    analysis_period_days: int = Field(default=30, description="Period for analysis in days")
    departments: Optional[List[str]] = Field(default=None, description="Specific departments to analyze")
    insight_types: List[str] = Field(default=["trends", "patterns", "recommendations"], 
                                   description="Types of insights to generate")


@router.post("/ask")
async def ask_copilot(
    query: CopilotQuery,
    current_user: User = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Ask the Enterprise Copilot a question or request assistance.
    
    The copilot can help with compliance questions, workflow automation,
    data analysis, and general healthcare documentation guidance.
    """
    try:
        logger.info(f"Copilot query from {current_user.username}: {query.query[:100]}...")
        
        # Process the query through the enhanced enterprise copilot service with performance monitoring
        with performance_monitor.track_operation("enterprise_copilot", "process_query"):
            response = await enterprise_copilot_service.process_query(
                query=query.query,
                context=query.context or {},
                user_id=current_user.id,
                department=query.department,
                priority=query.priority
            )
        
        return {
            "success": True,
            "response": response.get("answer", "I'm sorry, I couldn't process that request."),
            "confidence": response.get("confidence", 0.0),
            "sources": response.get("sources", []),
            "suggested_actions": response.get("suggested_actions", []),
            "follow_up_questions": response.get("follow_up_questions", []),
            "processing_time_ms": response.get("processing_time_ms", 0),
            "query_id": response.get("query_id")
        }
        
    except Exception as e:
        logger.error(f"Copilot query failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Copilot query failed: {str(e)}"
        )


@router.get("/capabilities")
async def get_copilot_capabilities() -> Dict[str, Any]:
    """Get the current capabilities of the Enterprise Copilot."""
    return {
        "capabilities": [
            {
                "category": "Compliance Assistance",
                "features": [
                    "Medicare compliance guidance",
                    "Regulatory requirement explanations",
                    "Documentation best practices",
                    "Audit preparation assistance"
                ]
            },
            {
                "category": "Data Analysis",
                "features": [
                    "Compliance trend analysis",
                    "Performance metrics interpretation",
                    "Risk assessment insights",
                    "Comparative analysis"
                ]
            },
            {
                "category": "Workflow Optimization",
                "features": [
                    "Process improvement suggestions",
                    "Automation recommendations",
                    "Efficiency analysis",
                    "Resource optimization"
                ]
            },
            {
                "category": "Predictive Analytics",
                "features": [
                    "Compliance trend predictions",
                    "Risk forecasting",
                    "Performance projections",
                    "Anomaly detection"
                ]
            },
            {
                "category": "Knowledge Management",
                "features": [
                    "Policy and procedure guidance",
                    "Training recommendations",
                    "Best practice sharing",
                    "Regulatory updates"
                ]
            }
        ],
        "supported_languages": ["English"],
        "response_formats": ["text", "structured_data", "recommendations"],
        "integration_points": ["EHR_systems", "compliance_databases", "analytics_platforms"]
    }


@router.post("/insights/compliance")
async def generate_compliance_insights(
    request: ComplianceInsightRequest,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Generate comprehensive compliance insights using AI analysis.
    
    This endpoint provides deep insights into compliance patterns,
    trends, and recommendations based on historical data.
    """
    try:
        insight_task_id = f"insights_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        # Start background insight generation
        background_tasks.add_task(
            enterprise_copilot_service.generate_compliance_insights,
            task_id=insight_task_id,
            analysis_period_days=request.analysis_period_days,
            departments=request.departments,
            insight_types=request.insight_types,
            user_id=str(current_user.id)
        )
        
        logger.info(f"Started compliance insights generation: {insight_task_id}")
        
        return {
            "success": True,
            "message": "Compliance insights generation started",
            "task_id": insight_task_id,
            "estimated_duration": "3-10 minutes",
            "status_endpoint": f"/copilot/insights/{insight_task_id}/status",
            "analysis_period_days": request.analysis_period_days,
            "departments": request.departments,
            "insight_types": request.insight_types
        }
    
    except Exception as e:
        logger.error(f"Failed to start compliance insights generation: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate compliance insights: {str(e)}"
        )


@router.get("/insights/{task_id}/status")
async def get_insights_status(
    task_id: str,
    current_user: User = Depends(get_current_user)
) -> Dict[str, Any]:
    """Get the status of a compliance insights generation task."""
    try:
        status_info = await enterprise_copilot_service.get_insights_status(task_id)
        
        if not status_info:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Insights task {task_id} not found"
            )
        
        return status_info
    
    except Exception as e:
        logger.error(f"Failed to get insights status: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get insights status: {str(e)}"
        )


@router.post("/workflow/automate")
async def create_workflow_automation(
    request: WorkflowAutomationRequest,
    current_user: User = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Create a new workflow automation.
    
    Supported workflow types:
    - compliance_monitoring: Automated compliance checks
    - report_generation: Scheduled report generation
    - data_sync: Automated data synchronization
    - alert_management: Automated alert processing
    - quality_assurance: Automated QA processes
    """
    if not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin privileges required for workflow automation"
        )
    
    try:
        automation_result = await workflow_automation.create_automation(
            workflow_type=request.workflow_type,
            parameters=request.parameters,
            schedule=request.schedule,
            enabled=request.enabled,
            created_by=current_user.id
        )
        
        logger.info(f"Created workflow automation: {automation_result.get('automation_id')}")
        
        return {
            "success": True,
            "message": "Workflow automation created successfully",
            "automation_id": automation_result.get("automation_id"),
            "workflow_type": request.workflow_type,
            "schedule": request.schedule,
            "enabled": request.enabled,
            "next_run": automation_result.get("next_run"),
            "created_at": datetime.now().isoformat()
        }
    
    except Exception as e:
        logger.error(f"Failed to create workflow automation: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create workflow automation: {str(e)}"
        )


@router.get("/workflow/automations")
async def list_workflow_automations(
    current_user: User = Depends(get_current_user)
) -> Dict[str, Any]:
    """List all workflow automations."""
    try:
        automations = await workflow_automation.list_automations(
            user_id=str(current_user.id) if not current_user.is_admin else None
        )
        
        return {
            "automations": automations,
            "total_count": len(automations),
            "active_count": len([a for a in automations if a.get("enabled", False)])
        }
    
    except Exception as e:
        logger.error(f"Failed to list workflow automations: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list workflow automations: {str(e)}"
        )


@router.post("/predictions/trends")
async def predict_compliance_trends(
    days_ahead: int = 30,
    departments: Optional[List[str]] = None,
    current_user: User = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Generate ML-based compliance trend predictions.
    
    Uses advanced machine learning algorithms to predict future
    compliance trends based on historical data patterns.
    """
    try:
        # Get historical data for predictions
        historical_data = await enterprise_copilot_service.get_historical_compliance_data(
            departments=departments,
            days_back=90  # Use 90 days of history for predictions
        )
        
        # Generate ML predictions
        predictions = await ml_trend_predictor.predict_compliance_trends(
            historical_data=historical_data,
            time_horizon_days=days_ahead
        )
        
        # Detect patterns
        patterns = await ml_trend_predictor.detect_compliance_patterns(historical_data)
        
        return {
            "success": True,
            "predictions": [
                {
                    "metric": pred.metric_name,
                    "current_value": pred.current_value,
                    "predicted_value": pred.predicted_value,
                    "confidence": pred.confidence_score,
                    "trend": pred.trend_direction,
                    "risk_level": pred.risk_level,
                    "recommendations": pred.recommendations,
                    "time_horizon_days": pred.time_horizon_days
                }
                for pred in predictions
            ],
            "patterns": [
                {
                    "type": pattern.pattern_type,
                    "frequency": pattern.frequency,
                    "severity": pattern.severity,
                    "description": pattern.description,
                    "confidence": pattern.confidence
                }
                for pattern in patterns
            ],
            "analysis_period": {
                "historical_days": 90,
                "prediction_days": days_ahead,
                "departments": departments
            },
            "generated_at": datetime.now().isoformat()
        }
    
    except Exception as e:
        logger.error(f"Failed to generate trend predictions: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate trend predictions: {str(e)}"
        )


@router.post("/recommendations/personalized")
async def get_personalized_recommendations(
    context: Dict[str, Any],
    current_user: User = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Get personalized recommendations based on user context and performance.
    
    Analyzes user's historical performance and provides tailored
    recommendations for improvement.
    """
    try:
        recommendations = await enterprise_copilot_service.generate_personalized_recommendations(
            user_id=str(current_user.id),
            context=context
        )
        
        return {
            "success": True,
            "recommendations": recommendations.get("recommendations", []),
            "priority_actions": recommendations.get("priority_actions", []),
            "learning_resources": recommendations.get("learning_resources", []),
            "performance_insights": recommendations.get("performance_insights", {}),
            "next_review_date": recommendations.get("next_review_date"),
            "generated_at": datetime.now().isoformat()
        }
    
    except Exception as e:
        logger.error(f"Failed to generate personalized recommendations: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate personalized recommendations: {str(e)}"
        )


@router.get("/analytics/performance")
async def get_performance_analytics(
    period_days: int = 30,
    department: Optional[str] = None,
    current_user: User = Depends(get_current_user)
) -> Dict[str, Any]:
    """Get comprehensive performance analytics."""
    try:
        analytics = await enterprise_copilot_service.get_performance_analytics(
            user_id=str(current_user.id) if not current_user.is_admin else None,
            period_days=period_days,
            department=department
        )
        
        return {
            "success": True,
            "analytics": analytics,
            "period_days": period_days,
            "department": department,
            "generated_at": datetime.now().isoformat()
        }
    
    except Exception as e:
        logger.error(f"Failed to get performance analytics: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get performance analytics: {str(e)}"
        )


@router.post("/feedback")
async def submit_copilot_feedback(
    query_id: str,
    rating: int = Query(..., ge=1, le=5, description="Rating from 1-5"),
    feedback: Optional[str] = None,
    current_user: User = Depends(get_current_user)
) -> Dict[str, Any]:
    """Submit feedback on a copilot response."""
    try:
        feedback_result = await enterprise_copilot_service.submit_feedback(
            query_id=query_id,
            user_id=str(current_user.id),
            rating=rating,
            feedback=feedback
        )
        
        return {
            "success": True,
            "message": "Feedback submitted successfully",
            "feedback_id": feedback_result.get("feedback_id"),
            "submitted_at": datetime.now().isoformat()
        }
    
    except Exception as e:
        logger.error(f"Failed to submit copilot feedback: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to submit feedback: {str(e)}"
        )


@router.get("/help/topics")
async def get_help_topics() -> Dict[str, Any]:
    """Get available help topics and examples."""
    return {
        "help_topics": [
            {
                "category": "Compliance Questions",
                "examples": [
                    "What are the Medicare documentation requirements for PT evaluations?",
                    "How should I document functional outcomes?",
                    "What are the billing compliance requirements for group therapy?",
                    "How do I ensure my progress notes meet CMS standards?"
                ]
            },
            {
                "category": "Data Analysis",
                "examples": [
                    "Show me compliance trends for the last 3 months",
                    "What are the most common documentation errors?",
                    "Compare my department's performance to benchmarks",
                    "Identify patterns in compliance violations"
                ]
            },
            {
                "category": "Workflow Optimization",
                "examples": [
                    "How can I improve documentation efficiency?",
                    "What automation opportunities exist in my workflow?",
                    "Suggest ways to reduce compliance errors",
                    "Optimize my daily documentation routine"
                ]
            },
            {
                "category": "Training & Education",
                "examples": [
                    "What training do I need for better compliance?",
                    "Recommend resources for Medicare documentation",
                    "Create a learning plan for my team",
                    "Find best practices for my specialty"
                ]
            }
        ],
        "query_tips": [
            "Be specific about your department or specialty",
            "Include relevant context (patient type, setting, etc.)",
            "Ask follow-up questions for clarification",
            "Use natural language - no special syntax required"
        ]
    }

@router
.post("/automate-workflow")
async def create_workflow_automation(
    request: WorkflowAutomationRequest,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Create or update a workflow automation.
    
    Allows users to automate repetitive tasks such as compliance checking,
    report generation, and data synchronization.
    """
    try:
        logger.info(f"Workflow automation request from {current_user.username}: {request.workflow_type}")
        
        # Create the workflow automation
        automation_result = await workflow_automation.create_automation(
            workflow_type=request.workflow_type,
            parameters=request.parameters,
            schedule=request.schedule,
            enabled=request.enabled,
            user_id=current_user.id
        )
        
        if automation_result.get("success"):
            # Start the workflow if it's enabled and has no schedule (immediate execution)
            if request.enabled and not request.schedule:
                background_tasks.add_task(
                    workflow_automation.execute_workflow,
                    automation_result["automation_id"]
                )
            
            return {
                "success": True,
                "message": "Workflow automation created successfully",
                "automation_id": automation_result["automation_id"],
                "workflow_type": request.workflow_type,
                "enabled": request.enabled,
                "scheduled": bool(request.schedule),
                "next_execution": automation_result.get("next_execution")
            }
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Failed to create workflow automation: {automation_result.get('error')}"
            )
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Workflow automation creation failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Workflow automation failed: {str(e)}"
        )


@router.get("/workflows")
async def list_workflow_automations(
    current_user: User = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    List all workflow automations for the current user.
    """
    try:
        logger.info(f"Listing workflow automations for {current_user.username}")
        
        automations = await workflow_automation.list_user_automations(current_user.id)
        
        return {
            "success": True,
            "total_automations": len(automations),
            "automations": automations
        }
        
    except Exception as e:
        logger.error(f"Failed to list workflow automations: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list workflow automations: {str(e)}"
        )


@router.post("/insights/compliance")
async def generate_compliance_insights(
    request: ComplianceInsightRequest,
    current_user: User = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Generate AI-powered compliance insights and recommendations.
    
    Analyzes historical compliance data to identify trends, patterns,
    and opportunities for improvement.
    """
    try:
        logger.info(f"Compliance insights request from {current_user.username}")
        
        # Generate insights using ML trend predictor
        insights = await ml_trend_predictor.generate_compliance_insights(
            analysis_period_days=request.analysis_period_days,
            departments=request.departments,
            insight_types=request.insight_types,
            user_id=current_user.id
        )
        
        return {
            "success": True,
            "insights": insights.get("insights", []),
            "trends": insights.get("trends", []),
            "recommendations": insights.get("recommendations", []),
            "risk_predictions": insights.get("risk_predictions", []),
            "analysis_period": request.analysis_period_days,
            "generated_at": datetime.now().isoformat(),
            "confidence_score": insights.get("confidence_score", 0.0)
        }
        
    except Exception as e:
        logger.error(f"Compliance insights generation failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Compliance insights generation failed: {str(e)}"
        )


@router.get("/suggestions")
async def get_contextual_suggestions(
    context: Optional[str] = Query(None, description="Current context or activity"),
    document_type: Optional[str] = Query(None, description="Type of document being worked on"),
    current_user: User = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Get contextual suggestions and tips based on current activity.
    
    Provides intelligent suggestions for documentation improvement,
    compliance best practices, and workflow optimization.
    """
    try:
        logger.info(f"Contextual suggestions request from {current_user.username}")
        
        # Generate contextual suggestions
        suggestions = await enterprise_copilot_service.get_contextual_suggestions(
            context=context,
            document_type=document_type,
            user_id=current_user.id
        )
        
        return {
            "success": True,
            "suggestions": suggestions.get("suggestions", []),
            "tips": suggestions.get("tips", []),
            "best_practices": suggestions.get("best_practices", []),
            "quick_actions": suggestions.get("quick_actions", []),
            "context": context,
            "document_type": document_type
        }
        
    except Exception as e:
        logger.error(f"Contextual suggestions failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Contextual suggestions failed: {str(e)}"
        )


@router.post("/feedback")
async def submit_copilot_feedback(
    feedback_data: Dict[str, Any],
    current_user: User = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Submit feedback about copilot responses to improve future interactions.
    """
    try:
        logger.info(f"Copilot feedback from {current_user.username}")
        
        # Process feedback through the enterprise copilot service
        feedback_result = await enterprise_copilot_service.process_feedback(
            feedback_data=feedback_data,
            user_id=current_user.id
        )
        
        return {
            "success": True,
            "message": "Feedback submitted successfully",
            "feedback_id": feedback_result.get("feedback_id"),
            "thank_you": "Thank you for helping improve the Enterprise Copilot!"
        }
        
    except Exception as e:
        logger.error(f"Copilot feedback submission failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Feedback submission failed: {str(e)}"
        )


@router.get("/capabilities")
async def get_copilot_capabilities(
    current_user: User = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Get information about Enterprise Copilot capabilities and features.
    """
    try:
        capabilities = {
            "natural_language_queries": {
                "description": "Ask questions in natural language about compliance, documentation, and workflows",
                "examples": [
                    "How do I document a patient's progress in PT?",
                    "What are the Medicare requirements for evaluation notes?",
                    "Show me compliance trends for the last month"
                ]
            },
            "workflow_automation": {
                "description": "Automate repetitive tasks and create scheduled workflows",
                "supported_workflows": [
                    "compliance_checking",
                    "report_generation", 
                    "data_synchronization",
                    "reminder_notifications"
                ]
            },
            "compliance_insights": {
                "description": "AI-powered analysis of compliance data and trends",
                "features": [
                    "Trend identification",
                    "Risk prediction",
                    "Performance recommendations",
                    "Comparative analysis"
                ]
            },
            "contextual_assistance": {
                "description": "Context-aware suggestions and guidance",
                "contexts": [
                    "document_creation",
                    "compliance_review",
                    "quality_improvement",
                    "training_support"
                ]
            }
        }
        
        return {
            "success": True,
            "capabilities": capabilities,
            "version": "2.1.0",
            "last_updated": "2024-01-15",
            "supported_languages": ["English"],
            "availability": "24/7"
        }
        
    except Exception as e:
        logger.error(f"Failed to get copilot capabilities: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get capabilities: {str(e)}"
        )
@route
r.post("/multi-agent-analysis")
async def run_multi_agent_analysis(
    document_content: str = Field(..., description="Document content to analyze"),
    rubric_data: Dict[str, Any] = Field(..., description="Compliance rubric data"),
    workflow_type: str = Field(default="comprehensive_analysis", description="Type of analysis workflow"),
    current_user: User = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Run multi-agent compliance analysis with enhanced context sharing.
    
    This endpoint leverages the multi-agent orchestrator to provide
    comprehensive compliance analysis with superior accuracy and insights.
    """
    try:
        logger.info(f"Multi-agent analysis request from {current_user.username}")
        
        # Prepare user preferences context
        user_preferences = {
            "user_id": current_user.id,
            "username": current_user.username,
            "is_admin": current_user.is_admin,
            "analysis_preferences": {
                "detailed_analysis": True,
                "include_recommendations": True,
                "confidence_threshold": 0.7
            }
        }
        
        # Execute multi-agent workflow with performance monitoring
        with performance_monitor.track_operation("multi_agent_orchestrator", "execute_workflow"):
            result = await multi_agent_orchestrator.execute_workflow(
                document_content=document_content,
                rubric_data=rubric_data,
                user_preferences=user_preferences,
                workflow_type=workflow_type
            )
        
        return {
            "success": True,
            "analysis_result": result,
            "workflow_type": workflow_type,
            "enhanced_features": [
                "Multi-agent collaboration",
                "Context sharing optimization",
                "Cross-validation quality assurance",
                "Performance monitoring"
            ]
        }
        
    except Exception as e:
        # Enhanced error handling
        enhanced_error = enhanced_error_handler.handle_error(
            e, 
            component="multi_agent_analysis",
            operation="execute_workflow",
            user_id=current_user.id
        )
        
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=enhanced_error.to_dict()
        )


@router.get("/performance-metrics")
async def get_performance_metrics(
    component: Optional[str] = Query(None, description="Specific component to analyze"),
    hours: int = Query(24, description="Hours of data to analyze"),
    current_user: User = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Get performance metrics and system health information.
    
    Provides insights into system performance, bottlenecks, and optimization opportunities.
    """
    try:
        logger.info(f"Performance metrics request from {current_user.username}")
        
        # Get system health
        system_health = performance_monitor.get_system_health()
        
        # Get component-specific performance if requested
        component_performance = None
        if component:
            component_performance = performance_monitor.get_component_performance(component, hours)
        
        # Get performance trends
        trends = performance_monitor.get_performance_trends(hours)
        
        # Get bottlenecks
        bottlenecks = performance_monitor.get_bottlenecks()
        
        return {
            "success": True,
            "system_health": {
                "timestamp": system_health.timestamp.isoformat(),
                "cpu_usage": system_health.cpu_usage,
                "memory_usage": system_health.memory_usage,
                "disk_usage": system_health.disk_usage,
                "active_threads": system_health.active_threads,
                "response_time_avg": system_health.response_time_avg,
                "error_rate": system_health.error_rate,
                "throughput": system_health.throughput
            },
            "component_performance": component_performance,
            "trends": trends,
            "bottlenecks": bottlenecks[:5],  # Top 5 bottlenecks
            "recommendations": [
                "Monitor high CPU usage components",
                "Consider caching for frequently accessed data",
                "Optimize slow operations identified in bottlenecks"
            ]
        }
        
    except Exception as e:
        enhanced_error = enhanced_error_handler.handle_error(
            e, 
            component="performance_monitoring",
            user_id=current_user.id
        )
        
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=enhanced_error.to_dict()
        )


@router.post("/export-pdf-report")
async def export_pdf_report(
    report_data: Dict[str, Any] = Field(..., description="Report data to export"),
    include_charts: bool = Field(default=True, description="Include charts in PDF"),
    watermark: Optional[str] = Field(default=None, description="Optional watermark text"),
    current_user: User = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Export compliance report to professional PDF format.
    
    Generates high-quality PDF reports suitable for printing and professional distribution.
    """
    try:
        logger.info(f"PDF export request from {current_user.username}")
        
        # Import PDF service here to avoid circular imports
        from src.core.pdf_export_service import pdf_export_service
        
        # Export to PDF with performance monitoring
        with performance_monitor.track_operation("pdf_export", "export_report"):
            pdf_bytes = await pdf_export_service.export_report_to_pdf(
                report_data=report_data,
                include_charts=include_charts,
                watermark=watermark
            )
        
        # Return base64 encoded PDF for API response
        import base64
        pdf_base64 = base64.b64encode(pdf_bytes).decode('utf-8')
        
        return {
            "success": True,
            "pdf_data": pdf_base64,
            "file_size_bytes": len(pdf_bytes),
            "include_charts": include_charts,
            "watermark": watermark,
            "export_timestamp": datetime.now().isoformat(),
            "features": [
                "Professional medical document formatting",
                "Print-optimized layout",
                "Interactive elements preserved as static content",
                "Accessibility compliant"
            ]
        }
        
    except Exception as e:
        enhanced_error = enhanced_error_handler.handle_error(
            e, 
            component="pdf_export",
            operation="export_report",
            user_id=current_user.id
        )
        
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=enhanced_error.to_dict()
        )