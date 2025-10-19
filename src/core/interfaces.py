"""Core interfaces and type definitions for the Therapy Compliance Analyzer.

This module defines interfaces, protocols, and type definitions used throughout
the application to ensure type safety and maintainability.
"""

from abc import ABC, abstractmethod
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Protocol, Union
from uuid import UUID

from pydantic import BaseModel, Field


# ============================================================================
# Core Domain Types
# ============================================================================

class AnalysisStatus(str, Enum):
    """Analysis task status enumeration."""
    PENDING = "pending"
    PROCESSING = "processing"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class AnalysisMode(str, Enum):
    """Analysis mode enumeration."""
    COMPREHENSIVE = "comprehensive"
    RUBRIC = "rubric"
    QUICK = "quick"


class StrictnessLevel(str, Enum):
    """Analysis strictness level enumeration."""
    RELAXED = "relaxed"
    STANDARD = "standard"
    STRICT = "strict"
    ULTRA_STRICT = "ultra_strict"


class DisciplineType(str, Enum):
    """Therapy discipline enumeration."""
    PT = "pt"
    OT = "ot"
    SLP = "slp"
    GENERAL = "general"


class RiskLevel(str, Enum):
    """Risk level enumeration."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


# ============================================================================
# Core Interfaces
# ============================================================================

class AnalysisServiceInterface(Protocol):
    """Interface for analysis services."""

    async def analyze_document(
        self,
        content: bytes,
        filename: str,
        discipline: DisciplineType,
        analysis_mode: AnalysisMode,
        strictness: StrictnessLevel,
    ) -> Dict[str, Any]:
        """Analyze a document for compliance."""
        ...


class EncryptionServiceInterface(Protocol):
    """Interface for encryption services."""

    def encrypt(self, data: str) -> str:
        """Encrypt data."""
        ...

    def decrypt(self, encrypted_data: str) -> str:
        """Decrypt data."""
        ...


class SessionManagerInterface(Protocol):
    """Interface for session management."""

    def create_session(self, user_id: int, client_info: Dict[str, Any]) -> str:
        """Create a new session."""
        ...

    def validate_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Validate a session."""
        ...

    def invalidate_session(self, session_id: str) -> bool:
        """Invalidate a session."""
        ...


class StorageServiceInterface(Protocol):
    """Interface for storage services."""

    async def store_document(
        self,
        content: bytes,
        filename: str,
        user_id: int,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> str:
        """Store a document."""
        ...

    async def retrieve_document(self, doc_id: str, user_id: int) -> Optional[bytes]:
        """Retrieve a document."""
        ...

    async def delete_document(self, doc_id: str, user_id: int) -> bool:
        """Delete a document."""
        ...


# ============================================================================
# Request/Response Models
# ============================================================================

class AnalysisRequest(BaseModel):
    """Request model for document analysis."""
    filename: str = Field(..., description="Document filename")
    discipline: DisciplineType = Field(default=DisciplineType.PT, description="Therapy discipline")
    analysis_mode: AnalysisMode = Field(default=AnalysisMode.COMPREHENSIVE, description="Analysis mode")
    strictness: StrictnessLevel = Field(default=StrictnessLevel.STANDARD, description="Analysis strictness")
    metadata: Optional[Dict[str, Any]] = Field(default=None, description="Additional metadata")


class AnalysisResponse(BaseModel):
    """Response model for analysis results."""
    task_id: str = Field(..., description="Analysis task ID")
    status: AnalysisStatus = Field(..., description="Analysis status")
    progress: int = Field(ge=0, le=100, description="Analysis progress percentage")
    message: Optional[str] = Field(default=None, description="Status message")
    result: Optional[Dict[str, Any]] = Field(default=None, description="Analysis results")
    created_at: datetime = Field(..., description="Task creation timestamp")
    completed_at: Optional[datetime] = Field(default=None, description="Task completion timestamp")


class FindingModel(BaseModel):
    """Model for compliance findings."""
    id: str = Field(..., description="Finding ID")
    rule_id: str = Field(..., description="Compliance rule ID")
    risk_level: RiskLevel = Field(..., description="Risk level")
    title: str = Field(..., description="Finding title")
    description: str = Field(..., description="Finding description")
    personalized_tip: str = Field(..., description="Personalized improvement tip")
    problematic_text: str = Field(..., description="Problematic text excerpt")
    confidence_score: float = Field(ge=0.0, le=1.0, description="AI confidence score")
    line_number: Optional[int] = Field(default=None, description="Line number in document")
    character_range: Optional[tuple[int, int]] = Field(default=None, description="Character range")


class ComplianceReport(BaseModel):
    """Model for compliance analysis report."""
    document_id: str = Field(..., description="Document ID")
    filename: str = Field(..., description="Document filename")
    analysis_date: datetime = Field(..., description="Analysis timestamp")
    compliance_score: float = Field(ge=0.0, le=100.0, description="Overall compliance score")
    discipline: DisciplineType = Field(..., description="Therapy discipline")
    analysis_mode: AnalysisMode = Field(..., description="Analysis mode used")
    strictness: StrictnessLevel = Field(..., description="Strictness level used")
    findings: List[FindingModel] = Field(default_factory=list, description="Compliance findings")
    summary: Dict[str, Any] = Field(default_factory=dict, description="Analysis summary")
    recommendations: List[str] = Field(default_factory=list, description="Improvement recommendations")


class SessionInfo(BaseModel):
    """Model for session information."""
    session_id: str = Field(..., description="Session ID")
    user_id: int = Field(..., description="User ID")
    username: str = Field(..., description="Username")
    created_at: datetime = Field(..., description="Session creation time")
    last_activity: datetime = Field(..., description="Last activity time")
    expires_at: datetime = Field(..., description="Session expiration time")
    client_info: Dict[str, Any] = Field(..., description="Client information")
    is_active: bool = Field(..., description="Session active status")


class UserProfile(BaseModel):
    """Model for user profile information."""
    id: int = Field(..., description="User ID")
    username: str = Field(..., description="Username")
    email: Optional[str] = Field(default=None, description="Email address")
    is_active: bool = Field(..., description="Account active status")
    is_admin: bool = Field(..., description="Admin privileges")
    created_at: datetime = Field(..., description="Account creation time")
    last_login: Optional[datetime] = Field(default=None, description="Last login time")
    preferences: Dict[str, Any] = Field(default_factory=dict, description="User preferences")


# ============================================================================
# Configuration Interfaces
# ============================================================================

class DatabaseConfigInterface(Protocol):
    """Interface for database configuration."""

    @property
    def url(self) -> str:
        """Database connection URL."""
        ...

    @property
    def echo(self) -> bool:
        """Enable SQL query logging."""
        ...


class SecurityConfigInterface(Protocol):
    """Interface for security configuration."""

    @property
    def secret_key(self) -> str:
        """JWT secret key."""
        ...

    @property
    def access_token_expire_minutes(self) -> int:
        """Access token expiration time."""
        ...

    @property
    def encryption_key(self) -> str:
        """Encryption key."""
        ...


class AIConfigInterface(Protocol):
    """Interface for AI service configuration."""

    @property
    def model_name(self) -> str:
        """AI model name."""
        ...

    @property
    def max_tokens(self) -> int:
        """Maximum tokens for AI responses."""
        ...

    @property
    def temperature(self) -> float:
        """AI response temperature."""
        ...


# ============================================================================
# Service Interfaces
# ============================================================================

class TaskManagerInterface(Protocol):
    """Interface for task management."""

    async def start_task(
        self,
        task_id: str,
        task_func: callable,
        *args,
        **kwargs,
    ) -> None:
        """Start a background task."""
        ...

    async def get_task_status(self, task_id: str) -> Optional[Dict[str, Any]]:
        """Get task status."""
        ...

    async def cancel_task(self, task_id: str) -> bool:
        """Cancel a task."""
        ...


class NotificationServiceInterface(Protocol):
    """Interface for notification services."""

    async def send_notification(
        self,
        user_id: int,
        message: str,
        notification_type: str,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> bool:
        """Send a notification to a user."""
        ...


class AuditLoggerInterface(Protocol):
    """Interface for audit logging."""

    def log_event(
        self,
        event_type: str,
        user_id: Optional[int],
        details: Dict[str, Any],
        request_id: Optional[str] = None,
    ) -> None:
        """Log an audit event."""
        ...


# ============================================================================
# Error Interfaces
# ============================================================================

class ErrorHandlerInterface(Protocol):
    """Interface for error handling."""

    def handle_exception(
        self,
        exc: Exception,
        request_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Handle an exception and return error response."""
        ...


# ============================================================================
# Validation Interfaces
# ============================================================================

class ValidatorInterface(Protocol):
    """Interface for validation services."""

    def validate_input(self, data: Any, rules: Dict[str, Any]) -> tuple[bool, Optional[str]]:
        """Validate input data."""
        ...

    def validate_file(self, file_data: bytes, filename: str) -> tuple[bool, Optional[str]]:
        """Validate uploaded file."""
        ...


# ============================================================================
# Utility Types
# ============================================================================

class PaginationParams(BaseModel):
    """Pagination parameters."""
    page: int = Field(ge=1, default=1, description="Page number")
    size: int = Field(ge=1, le=100, default=20, description="Page size")
    sort_by: Optional[str] = Field(default=None, description="Sort field")
    sort_order: str = Field(default="asc", pattern="^(asc|desc)$", description="Sort order")


class PaginatedResponse(BaseModel):
    """Paginated response wrapper."""
    items: List[Any] = Field(..., description="Response items")
    total: int = Field(..., description="Total number of items")
    page: int = Field(..., description="Current page")
    size: int = Field(..., description="Page size")
    pages: int = Field(..., description="Total number of pages")


class HealthStatus(BaseModel):
    """Health status model."""
    status: str = Field(..., description="Health status")
    timestamp: datetime = Field(..., description="Check timestamp")
    version: str = Field(..., description="Application version")
    uptime_seconds: float = Field(..., description="Application uptime")
    services: Dict[str, Any] = Field(default_factory=dict, description="Service statuses")


# ============================================================================
# Type Aliases
# ============================================================================

TaskId = str
UserId = int
DocumentId = str
SessionId = str
RequestId = str

# Common response types
SuccessResponse = Dict[str, Union[str, bool, int, float]]
ErrorResponse = Dict[str, Union[str, int, Dict[str, Any]]]
DataResponse = Dict[str, Union[Any, SuccessResponse]]
