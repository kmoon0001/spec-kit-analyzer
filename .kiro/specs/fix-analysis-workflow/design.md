# Design Document - Fix Analysis Workflow

## Overview

This design outlines the technical approach to diagnose and fix the analysis workflow issue where document analysis starts but never completes. The solution involves comprehensive logging, error handling improvements, and workflow verification.

## Architecture

### Analysis Workflow Components

```
GUI (MainWindow) → AnalysisStarterWorker → FastAPI Backend → AI Services
     ↓                                           ↓
SingleAnalysisPollingWorker ← Task Status ← Analysis Engine
     ↓
Results Display (Summary/Details tabs)
```

### Key Integration Points
1. **Frontend Analysis Trigger**: `_start_analysis()` method in MainWindow
2. **Worker Thread Management**: AnalysisStarterWorker and SingleAnalysisPollingWorker
3. **API Communication**: FastAPI endpoints for analysis submission and status polling
4. **Result Processing**: Analysis result handling and display

## Components and Interfaces

### 1. Enhanced Logging System

**Purpose**: Comprehensive logging to identify where the workflow fails

**Implementation**:
```python
# Add detailed logging to each workflow step
class AnalysisWorkflowLogger:
    def log_analysis_start(self, file_path: str, rubric: str)
    def log_api_request(self, endpoint: str, payload: dict)
    def log_api_response(self, status_code: int, response: dict)
    def log_polling_attempt(self, task_id: str, attempt: int)
    def log_workflow_completion(self, success: bool, duration: float)
```

### 2. Analysis Status Tracker

**Purpose**: Track analysis progress and detect hanging processes

**Implementation**:
```python
class AnalysisStatusTracker:
    def __init__(self):
        self.current_analysis = None
        self.start_time = None
        self.last_update = None
        self.timeout_threshold = 120  # 2 minutes
    
    def start_tracking(self, task_id: str)
    def update_status(self, status: str, progress: int)
    def check_timeout(self) -> bool
    def reset(self)
```

### 3. Enhanced Error Handling

**Purpose**: Catch and properly handle all possible failure points

**Components**:
- API connection error handling
- AI model loading verification
- File processing error detection
- Timeout detection and recovery
- User-friendly error messages

### 4. Analysis Workflow Diagnostics

**Purpose**: Built-in diagnostics to identify common issues

**Features**:
- API connectivity test
- AI model status verification
- File format validation
- System resource checks
- Backend service health check

## Data Models

### AnalysisRequest
```python
@dataclass
class AnalysisRequest:
    file_path: str
    rubric_id: str
    user_id: str
    timestamp: datetime
    options: Dict[str, Any]
```

### AnalysisStatus
```python
@dataclass
class AnalysisStatus:
    task_id: str
    status: str  # 'pending', 'processing', 'completed', 'failed'
    progress: int  # 0-100
    message: str
    error_details: Optional[str]
    started_at: datetime
    updated_at: datetime
```

### DiagnosticResult
```python
@dataclass
class DiagnosticResult:
    component: str
    status: str  # 'healthy', 'warning', 'error'
    message: str
    details: Dict[str, Any]
```

## Error Handling

### Error Categories and Responses

1. **API Connection Errors**
   - Detection: Request timeout or connection refused
   - Response: "Cannot connect to analysis service. Please check if the backend is running."
   - Recovery: Suggest restarting the API server

2. **AI Model Loading Errors**
   - Detection: Model initialization failures
   - Response: "AI models are not ready. Please wait for models to load or restart the application."
   - Recovery: Provide model loading status and retry option

3. **File Processing Errors**
   - Detection: File read/parse failures
   - Response: "Cannot process the selected document. Please check the file format and try again."
   - Recovery: Suggest supported file formats

4. **Analysis Timeout Errors**
   - Detection: No progress updates for 2+ minutes
   - Response: "Analysis is taking longer than expected. This may indicate a system issue."
   - Recovery: Offer to cancel and retry

5. **Backend Processing Errors**
   - Detection: API returns error status
   - Response: Display specific error message from backend
   - Recovery: Suggest troubleshooting steps based on error type

## Testing Strategy

### Unit Tests
- Test each workflow component in isolation
- Mock API responses for different scenarios
- Verify error handling for all failure modes
- Test timeout detection and recovery

### Integration Tests
- End-to-end analysis workflow testing
- API communication verification
- Error propagation testing
- Performance and timeout testing

### Manual Testing Scenarios
1. **Normal Operation**: Upload document, run analysis, verify completion
2. **API Offline**: Test with backend stopped
3. **Model Loading**: Test during AI model initialization
4. **Large Files**: Test with various document sizes
5. **Network Issues**: Test with simulated network problems
6. **Concurrent Analyses**: Test multiple simultaneous analyses

## Implementation Plan

### Phase 1: Diagnostic Infrastructure
- Add comprehensive logging throughout workflow
- Implement analysis status tracking
- Create diagnostic health checks
- Add timeout detection

### Phase 2: Error Handling Enhancement
- Improve error messages and user feedback
- Add recovery mechanisms
- Implement cancel/retry functionality
- Enhance progress indicators

### Phase 3: Workflow Verification
- Verify API endpoint functionality
- Test worker thread communication
- Validate result processing
- Ensure proper cleanup

### Phase 4: User Experience Improvements
- Add analysis progress visualization
- Implement better status messages
- Provide troubleshooting guidance
- Add diagnostic tools for users

## Success Criteria

1. **Analysis Completion**: 95% of analyses complete successfully within 2 minutes
2. **Error Detection**: All failure modes are detected and reported within 10 seconds
3. **User Feedback**: Clear, actionable error messages for all failure scenarios
4. **Recovery**: Users can retry failed analyses without restarting the application
5. **Diagnostics**: Built-in tools help identify and resolve common issues

## Risk Mitigation

- **Backward Compatibility**: Ensure changes don't break existing functionality
- **Performance Impact**: Minimize logging overhead in production
- **Resource Usage**: Prevent memory leaks from failed analyses
- **User Experience**: Maintain responsive UI during analysis operations