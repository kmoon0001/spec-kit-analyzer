"""
Analysis Error Handler - User-friendly error messaging and recovery system.

This module provides comprehensive error handling with clear, actionable
error messages and recovery suggestions for analysis workflow failures.
"""

import re
from typing import Dict, List, Optional
from enum import Enum
from dataclasses import dataclass


class ErrorCategory(Enum):
    """Categories of analysis errors."""
    API_CONNECTION = "api_connection"
    AI_MODEL_LOADING = "ai_model_loading"
    FILE_PROCESSING = "file_processing"
    ANALYSIS_TIMEOUT = "analysis_timeout"
    BACKEND_PROCESSING = "backend_processing"
    AUTHENTICATION = "authentication"
    SYSTEM_RESOURCES = "system_resources"
    UNKNOWN = "unknown"


@dataclass
class ErrorSolution:
    """Represents a solution for an error."""
    title: str
    description: str
    action: Optional[str] = None
    priority: int = 1  # 1 = high, 2 = medium, 3 = low


@dataclass
class AnalysisError:
    """Comprehensive error information with solutions."""
    category: ErrorCategory
    title: str
    message: str
    technical_details: str
    solutions: List[ErrorSolution]
    severity: str  # "critical", "warning", "info"
    icon: str


class AnalysisErrorHandler:
    """
    Comprehensive error handler for analysis workflow.
    
    Categorizes errors and provides user-friendly messages with
    actionable solutions and troubleshooting guidance.
    """
    
    def __init__(self):
        self.error_patterns = self._initialize_error_patterns()
    
    def categorize_and_handle_error(self, error_message: str, context: Optional[Dict] = None) -> AnalysisError:
        """
        Categorize an error and provide comprehensive handling information.
        
        Args:
            error_message: The raw error message
            context: Additional context about the error
            
        Returns:
            AnalysisError with categorization and solutions
        """
        # Normalize error message for pattern matching
        normalized_error = error_message.lower().strip()
        
        # Try to match against known error patterns
        for category, patterns in self.error_patterns.items():
            for pattern in patterns:
                if re.search(pattern, normalized_error):
                    return self._create_error_response(category, error_message, context)
        
        # If no pattern matches, return unknown error
        return self._create_error_response(ErrorCategory.UNKNOWN, error_message, context)
    
    def _initialize_error_patterns(self) -> Dict[ErrorCategory, List[str]]:
        """Initialize regex patterns for error categorization."""
        return {
            ErrorCategory.API_CONNECTION: [
                r"connection.*refused",
                r"failed to establish.*connection",
                r"cannot connect to.*server",
                r"api.*not.*accessible",
                r"network.*unreachable",
                r"timeout.*connecting",
                r"connection.*timed out",
                r"no route to host"
            ],
            ErrorCategory.AI_MODEL_LOADING: [
                r"model.*not.*loaded",
                r"ai.*model.*failed",
                r"model.*initialization.*error",
                r"transformers.*error",
                r"model.*not.*ready",
                r"loading.*model.*failed",
                r"cuda.*error",
                r"out of memory.*model"
            ],
            ErrorCategory.FILE_PROCESSING: [
                r"file.*not.*found",
                r"permission.*denied.*file",
                r"cannot.*read.*file",
                r"invalid.*file.*format",
                r"file.*corrupted",
                r"unsupported.*format",
                r"file.*too.*large",
                r"empty.*file",
                r"parsing.*error"
            ],
            ErrorCategory.ANALYSIS_TIMEOUT: [
                r"analysis.*timed out",
                r"timeout.*analysis",
                r"request.*timeout",
                r"operation.*timed out",
                r"exceeded.*time.*limit",
                r"analysis.*taking.*too.*long"
            ],
            ErrorCategory.BACKEND_PROCESSING: [
                r"internal.*server.*error",
                r"500.*error",
                r"backend.*error",
                r"processing.*failed",
                r"analysis.*engine.*error",
                r"server.*error",
                r"service.*unavailable",
                r"502.*bad.*gateway",
                r"503.*service.*unavailable"
            ],
            ErrorCategory.AUTHENTICATION: [
                r"unauthorized",
                r"authentication.*failed",
                r"invalid.*token",
                r"access.*denied",
                r"401.*error",
                r"forbidden",
                r"403.*error",
                r"login.*required"
            ],
            ErrorCategory.SYSTEM_RESOURCES: [
                r"out of memory",
                r"insufficient.*memory",
                r"disk.*full",
                r"no.*space.*left",
                r"resource.*exhausted",
                r"system.*overloaded",
                r"cpu.*limit.*exceeded"
            ]
        }
    
    def _create_error_response(self, category: ErrorCategory, original_error: str, context: Optional[Dict] = None) -> AnalysisError:
        """Create a comprehensive error response for a specific category."""
        
        error_configs = {
            ErrorCategory.API_CONNECTION: {
                "title": "Cannot Connect to Analysis Service",
                "message": "The application cannot connect to the backend analysis service. This is required for document analysis to work.",
                "solutions": [
                    ErrorSolution(
                        title="Start the API Server",
                        description="The backend service may not be running",
                        action="Use Tools → Start API Server or run: python scripts/run_api.py",
                        priority=1
                    ),
                    ErrorSolution(
                        title="Check Network Connection",
                        description="Verify your network connection is working",
                        action="Try accessing other network resources",
                        priority=2
                    ),
                    ErrorSolution(
                        title="Restart the Application",
                        description="Sometimes a fresh start resolves connection issues",
                        action="Close and reopen the application",
                        priority=3
                    )
                ],
                "severity": "critical",
                "icon": "🔌"
            },
            
            ErrorCategory.AI_MODEL_LOADING: {
                "title": "AI Models Not Ready",
                "message": "The AI models required for analysis are not loaded or failed to initialize. This may take a few minutes on first startup.",
                "solutions": [
                    ErrorSolution(
                        title="Wait for Model Loading",
                        description="AI models are still loading in the background",
                        action="Wait 2-3 minutes and try again",
                        priority=1
                    ),
                    ErrorSolution(
                        title="Check System Resources",
                        description="AI models require sufficient memory to load",
                        action="Close other applications to free up memory",
                        priority=2
                    ),
                    ErrorSolution(
                        title="Restart the API Server",
                        description="Restart the backend service to reload models",
                        action="Stop and restart the API server",
                        priority=3
                    )
                ],
                "severity": "warning",
                "icon": "🤖"
            },
            
            ErrorCategory.FILE_PROCESSING: {
                "title": "Document Processing Error",
                "message": "There was a problem processing your document. The file may be corrupted, in an unsupported format, or inaccessible.",
                "solutions": [
                    ErrorSolution(
                        title="Check File Format",
                        description="Ensure your file is in a supported format",
                        action="Use PDF, DOCX, or TXT files only",
                        priority=1
                    ),
                    ErrorSolution(
                        title="Try a Different File",
                        description="Test with a different document to isolate the issue",
                        action="Select another document and try again",
                        priority=2
                    ),
                    ErrorSolution(
                        title="Check File Size",
                        description="Very large files may cause processing issues",
                        action="Try with a smaller file (under 50MB)",
                        priority=3
                    )
                ],
                "severity": "warning",
                "icon": "📄"
            },
            
            ErrorCategory.ANALYSIS_TIMEOUT: {
                "title": "Analysis Timed Out",
                "message": "The analysis is taking longer than expected and has timed out. This may indicate a system overload or processing issue.",
                "solutions": [
                    ErrorSolution(
                        title="Try Again",
                        description="The system may have been temporarily overloaded",
                        action="Wait a moment and retry the analysis",
                        priority=1
                    ),
                    ErrorSolution(
                        title="Use a Smaller Document",
                        description="Large documents take longer to process",
                        action="Try with a shorter document first",
                        priority=2
                    ),
                    ErrorSolution(
                        title="Check System Resources",
                        description="Ensure your system has adequate resources",
                        action="Close other applications and try again",
                        priority=3
                    )
                ],
                "severity": "warning",
                "icon": "⏰"
            },
            
            ErrorCategory.BACKEND_PROCESSING: {
                "title": "Analysis Service Error",
                "message": "The backend analysis service encountered an error while processing your document. This is usually a temporary issue.",
                "solutions": [
                    ErrorSolution(
                        title="Retry the Analysis",
                        description="Backend errors are often temporary",
                        action="Wait a moment and try the analysis again",
                        priority=1
                    ),
                    ErrorSolution(
                        title="Check Server Logs",
                        description="Look for detailed error information",
                        action="Check the API server console for error details",
                        priority=2
                    ),
                    ErrorSolution(
                        title="Restart the Backend",
                        description="Restart the analysis service",
                        action="Stop and restart the API server",
                        priority=3
                    )
                ],
                "severity": "critical",
                "icon": "⚙️"
            },
            
            ErrorCategory.AUTHENTICATION: {
                "title": "Authentication Error",
                "message": "There was a problem with user authentication. You may need to log in again or check your credentials.",
                "solutions": [
                    ErrorSolution(
                        title="Restart the Application",
                        description="Refresh your authentication session",
                        action="Close and reopen the application",
                        priority=1
                    ),
                    ErrorSolution(
                        title="Check User Credentials",
                        description="Verify your username and password are correct",
                        action="Try logging in again with correct credentials",
                        priority=2
                    )
                ],
                "severity": "warning",
                "icon": "🔐"
            },
            
            ErrorCategory.SYSTEM_RESOURCES: {
                "title": "System Resource Issue",
                "message": "Your system is running low on resources (memory, disk space, or CPU). This can prevent analysis from completing.",
                "solutions": [
                    ErrorSolution(
                        title="Free Up Memory",
                        description="Close unnecessary applications",
                        action="Close other programs to free up RAM",
                        priority=1
                    ),
                    ErrorSolution(
                        title="Check Disk Space",
                        description="Ensure you have adequate free disk space",
                        action="Free up disk space if needed",
                        priority=2
                    ),
                    ErrorSolution(
                        title="Restart Your Computer",
                        description="A restart can free up system resources",
                        action="Restart your computer and try again",
                        priority=3
                    )
                ],
                "severity": "warning",
                "icon": "💻"
            },
            
            ErrorCategory.UNKNOWN: {
                "title": "Unexpected Error",
                "message": "An unexpected error occurred during analysis. This may be a temporary issue or a bug in the system.",
                "solutions": [
                    ErrorSolution(
                        title="Try Again",
                        description="Many errors are temporary and resolve on retry",
                        action="Wait a moment and retry the operation",
                        priority=1
                    ),
                    ErrorSolution(
                        title="Run Diagnostics",
                        description="Check system health and identify issues",
                        action="Use Tools → Run Diagnostics to check system status",
                        priority=2
                    ),
                    ErrorSolution(
                        title="Restart the Application",
                        description="A fresh start often resolves unexpected issues",
                        action="Close and reopen the application",
                        priority=3
                    )
                ],
                "severity": "warning",
                "icon": "❓"
            }
        }
        
        config = error_configs.get(category, error_configs[ErrorCategory.UNKNOWN])
        
        return AnalysisError(
            category=category,
            title=config["title"],
            message=config["message"],
            technical_details=original_error,
            solutions=config["solutions"],
            severity=config["severity"],
            icon=config["icon"]
        )
    
    def format_error_message(self, error: AnalysisError, include_technical: bool = False) -> str:
        """
        Format an error for display to the user.
        
        Args:
            error: The AnalysisError to format
            include_technical: Whether to include technical details
            
        Returns:
            Formatted error message string
        """
        message = f"{error.icon} {error.title}\n\n"
        message += f"{error.message}\n\n"
        
        if error.solutions:
            message += "💡 Recommended Solutions:\n\n"
            for i, solution in enumerate(error.solutions, 1):
                message += f"{i}. {solution.title}\n"
                message += f"   {solution.description}\n"
                if solution.action:
                    message += f"   → {solution.action}\n"
                message += "\n"
        
        if include_technical and error.technical_details:
            message += f"🔧 Technical Details:\n{error.technical_details}\n"
        
        return message.strip()


# Global error handler instance
error_handler = AnalysisErrorHandler()