# Therapy Compliance Analyzer - API Documentation

## Table of Contents

1. [Overview](#overview)
2. [Authentication](#authentication)
3. [Endpoints](#endpoints)
4. [Error Handling](#error-handling)
5. [Rate Limiting](#rate-limiting)
6. [Examples](#examples)

## Overview

The Therapy Compliance Analyzer API is a RESTful API built with FastAPI that provides comprehensive endpoints for analyzing clinical therapy documentation for compliance with Medicare and regulatory guidelines.

### Base URL

```
http://localhost:8000/api
```

### Interactive Documentation

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc
- **OpenAPI Schema**: http://localhost:8000/openapi.json

### Key Features

- ✅ JWT-based authentication
- ✅ Multi-format document support (PDF, DOCX, TXT)
- ✅ AI-powered compliance analysis
- ✅ Real-time chat assistance
- ✅ Historical analytics dashboard
- ✅ Custom rubric management
- ✅ HIPAA-compliant local processing

## Authentication

### Login

Obtain a JWT access token for API authentication.

**Endpoint:** `POST /auth/token`

**Request:**
```http
POST /auth/token HTTP/1.1
Content-Type: application/x-www-form-urlencoded

username=therapist1&password=SecurePass123
```

**Response:**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer"
}
```

**Error Responses:**
- `401 Unauthorized`: Invalid credentials
- `403 Forbidden`: Account inactive

### Using the Token

Include the token in the Authorization header for all authenticated requests:

```http
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

### Change Password

**Endpoint:** `POST /auth/users/change-password`

**Request:**
```json
{
  "current_password": "OldPass123",
  "new_password": "NewSecurePass456"
}
```

**Response:**
```json
{
  "message": "Password changed successfully."
}
```

**Password Requirements:**
- Minimum 8 characters
- At least one uppercase letter
- At least one lowercase letter
- At least one digit

## Endpoints

### Health Check

#### Get System Health

**Endpoint:** `GET /health`

**Description:** Check API health and AI model status.

**Response:**
```json
{
  "status": "healthy",
  "timestamp": "2025-01-01T12:00:00Z",
  "ai_models_ready": true,
  "database_connected": true
}
```

### Analysis

#### Upload and Analyze Document

**Endpoint:** `POST /analysis/analyze`

**Description:** Upload a clinical document for compliance analysis.

**Request:**
```http
POST /analysis/analyze HTTP/1.1
Authorization: Bearer <token>
Content-Type: multipart/form-data

file: <binary file data>
discipline: pt
analysis_mode: rubric
```

**Parameters:**
- `file` (required): Document file (PDF, DOCX, or TXT)
- `discipline` (optional): Therapy discipline (`pt`, `ot`, `slp`). Default: `pt`
- `analysis_mode` (optional): Analysis mode (`rubric`, `checklist`, `hybrid`). Default: `rubric`

**Response:**
```json
{
  "task_id": "abc123def456",
  "status": "processing"
}
```

**Error Responses:**
- `400 Bad Request`: Invalid file type or parameters
- `413 Payload Too Large`: File exceeds 50MB limit
- `503 Service Unavailable`: Analysis service not ready

#### Get Analysis Status

**Endpoint:** `GET /analysis/status/{task_id}`

**Description:** Retrieve the status and results of an analysis task.

**Response (Processing):**
```json
{
  "status": "processing",
  "filename": "patient_note.pdf"
}
```

**Response (Completed):**
```json
{
  "status": "completed",
  "filename": "patient_note.pdf",
  "result": {
    "compliance_score": 85,
    "document_type": "Progress Note",
    "discipline": "PT",
    "findings": [
      {
        "risk": "HIGH",
        "text": "Patient tolerated treatment well",
        "issue_title": "Missing objective measurements",
        "personalized_tip": "Include specific measurements...",
        "confidence": 0.92
      }
    ],
    "summary": "Document shows good compliance overall..."
  }
}
```

**Response (Failed):**
```json
{
  "status": "failed",
  "filename": "patient_note.pdf",
  "error": "Analysis failed: Invalid document format"
}
```

#### Export Report to PDF

**Endpoint:** `POST /analysis/export-pdf/{task_id}`

**Description:** Export completed analysis report to PDF format.

**Response:**
```json
{
  "task_id": "abc123def456",
  "pdf_info": {
    "success": true,
    "pdf_path": "temp/reports/compliance_report_patient_note_20250101_120000.pdf",
    "filename": "compliance_report_patient_note_20250101_120000.pdf",
    "file_size": 524288,
    "file_size_mb": 0.5,
    "generated_at": "2025-01-01T12:00:00Z",
    "purge_at": "2025-01-02T12:00:00Z"
  },
  "message": "PDF exported successfully"
}
```

#### List Exported PDFs

**Endpoint:** `GET /analysis/pdfs`

**Description:** List all exported PDF reports.

**Response:**
```json
{
  "pdfs": [
    {
      "filename": "compliance_report_patient_note_20250101_120000.pdf",
      "path": "temp/reports/compliance_report_patient_note_20250101_120000.pdf",
      "size_bytes": 524288,
      "size_mb": 0.5,
      "created_at": "2025-01-01T12:00:00Z",
      "modified_at": "2025-01-01T12:00:00Z"
    }
  ],
  "count": 1
}
```

#### Purge Old PDFs

**Endpoint:** `POST /analysis/purge-old-pdfs`

**Description:** Manually trigger purge of old PDF reports.

**Response:**
```json
{
  "message": "Purge completed",
  "statistics": {
    "purged": 5,
    "total_size_mb": 2.5,
    "cutoff_time": "2024-12-31T12:00:00Z"
  }
}
```

### Dashboard

#### Get Dashboard Data

**Endpoint:** `GET /dashboard/data`

**Description:** Retrieve historical compliance analytics and trends.

**Query Parameters:**
- `start_date` (optional): Start date for filtering (ISO 8601)
- `end_date` (optional): End date for filtering (ISO 8601)
- `discipline` (optional): Filter by discipline

**Response:**
```json
{
  "total_analyses": 150,
  "average_compliance_score": 82.5,
  "trend_data": [
    {
      "date": "2025-01-01",
      "compliance_score": 85,
      "findings_count": 3
    }
  ],
  "findings_by_category": {
    "Documentation Quality": 45,
    "Medical Necessity": 30,
    "Treatment Frequency": 25
  }
}
```

### Chat

#### Send Chat Message

**Endpoint:** `POST /chat/message`

**Description:** Send a message to the AI compliance assistant.

**Request:**
```json
{
  "message": "What are the requirements for documenting treatment frequency?",
  "context": {
    "document_type": "Progress Note",
    "discipline": "PT"
  }
}
```

**Response:**
```json
{
  "response": "Treatment frequency should be documented in every progress note...",
  "confidence": 0.95,
  "sources": [
    "Medicare Guidelines Section 220.1",
    "APTA Documentation Standards"
  ]
}
```

#### Get Chat History

**Endpoint:** `GET /chat/history`

**Description:** Retrieve chat conversation history.

**Query Parameters:**
- `limit` (optional): Maximum number of messages to return. Default: 50

**Response:**
```json
{
  "messages": [
    {
      "id": 1,
      "message": "What are the requirements...",
      "response": "Treatment frequency should be...",
      "timestamp": "2025-01-01T12:00:00Z"
    }
  ],
  "count": 1
}
```

### Compliance

#### List Rubrics

**Endpoint:** `GET /compliance/rubrics`

**Description:** List all available compliance rubrics.

**Response:**
```json
{
  "rubrics": [
    {
      "id": 1,
      "name": "PT Compliance Rubric",
      "discipline": "PT",
      "version": "1.0",
      "rule_count": 45,
      "created_at": "2025-01-01T00:00:00Z"
    }
  ],
  "count": 1
}
```

#### Get Rubric Details

**Endpoint:** `GET /compliance/rubrics/{rubric_id}`

**Description:** Get detailed information about a specific rubric.

**Response:**
```json
{
  "id": 1,
  "name": "PT Compliance Rubric",
  "discipline": "PT",
  "version": "1.0",
  "rules": [
    {
      "id": "rule_001",
      "title": "Treatment Frequency Documentation",
      "description": "Treatment frequency must be documented...",
      "severity": "HIGH",
      "regulation": "Medicare Guidelines 220.1"
    }
  ]
}
```

#### Create Custom Rubric

**Endpoint:** `POST /compliance/rubrics`

**Description:** Create a new custom compliance rubric.

**Request:**
```json
{
  "name": "Custom PT Rubric",
  "discipline": "PT",
  "version": "1.0",
  "rules": [
    {
      "id": "custom_001",
      "title": "Custom Rule",
      "description": "Custom compliance requirement...",
      "severity": "MEDIUM"
    }
  ]
}
```

**Response:**
```json
{
  "id": 2,
  "name": "Custom PT Rubric",
  "message": "Rubric created successfully"
}
```

### Admin

#### List Users

**Endpoint:** `GET /admin/users`

**Description:** List all users (admin only).

**Response:**
```json
{
  "users": [
    {
      "id": 1,
      "username": "therapist1",
      "is_admin": false,
      "is_active": true,
      "created_at": "2025-01-01T00:00:00Z"
    }
  ],
  "count": 1
}
```

#### Create User

**Endpoint:** `POST /admin/users`

**Description:** Create a new user account (admin only).

**Request:**
```json
{
  "username": "newtherapist",
  "password": "SecurePass123",
  "is_admin": false,
  "license_key": "LICENSE-KEY-123"
}
```

**Response:**
```json
{
  "id": 2,
  "username": "newtherapist",
  "message": "User created successfully"
}
```

#### Delete User

**Endpoint:** `DELETE /admin/users/{user_id}`

**Description:** Delete a user account (admin only).

**Response:**
```json
{
  "message": "User deleted successfully"
}
```

## Error Handling

### Standard Error Response

All errors follow a consistent format:

```json
{
  "detail": "Error message describing what went wrong"
}
```

### HTTP Status Codes

- `200 OK`: Request successful
- `201 Created`: Resource created successfully
- `202 Accepted`: Request accepted for processing
- `400 Bad Request`: Invalid request parameters
- `401 Unauthorized`: Authentication required or failed
- `403 Forbidden`: Insufficient permissions
- `404 Not Found`: Resource not found
- `413 Payload Too Large`: File size exceeds limit
- `422 Unprocessable Entity`: Validation error
- `429 Too Many Requests`: Rate limit exceeded
- `500 Internal Server Error`: Server error
- `503 Service Unavailable`: Service temporarily unavailable

### Common Error Scenarios

#### Invalid File Type
```json
{
  "detail": "File type not allowed. Allowed types: .pdf, .docx, .txt, .doc"
}
```

#### File Too Large
```json
{
  "detail": "File size exceeds maximum allowed size of 50MB"
}
```

#### Invalid Credentials
```json
{
  "detail": "Incorrect username or password"
}
```

#### Rate Limit Exceeded
```json
{
  "detail": "Rate limit exceeded. Please try again later."
}
```

## Rate Limiting

### Default Limits

- **100 requests per minute** per IP address
- Applies to all authenticated endpoints
- Excludes health check and documentation endpoints

### Rate Limit Headers

Response headers include rate limit information:

```http
X-RateLimit-Limit: 100
X-RateLimit-Remaining: 95
X-RateLimit-Reset: 1640995200
```

### Handling Rate Limits

When rate limit is exceeded, wait for the reset time before retrying:

```python
import time
import requests

response = requests.post(url, headers=headers)

if response.status_code == 429:
    reset_time = int(response.headers.get('X-RateLimit-Reset', 0))
    wait_seconds = reset_time - int(time.time())
    time.sleep(max(wait_seconds, 0))
    # Retry request
```

## Examples

### Python Client Example

```python
import requests
from pathlib import Path

# Base URL
BASE_URL = "http://localhost:8000/api"

# 1. Login
login_response = requests.post(
    f"{BASE_URL}/auth/token",
    data={
        "username": "therapist1",
        "password": "SecurePass123"
    }
)
token = login_response.json()["access_token"]

# 2. Upload and analyze document
headers = {"Authorization": f"Bearer {token}"}
files = {"file": open("patient_note.pdf", "rb")}
data = {
    "discipline": "pt",
    "analysis_mode": "rubric"
}

analyze_response = requests.post(
    f"{BASE_URL}/analysis/analyze",
    headers=headers,
    files=files,
    data=data
)
task_id = analyze_response.json()["task_id"]

# 3. Check analysis status
import time
while True:
    status_response = requests.get(
        f"{BASE_URL}/analysis/status/{task_id}",
        headers=headers
    )
    status_data = status_response.json()
    
    if status_data["status"] == "completed":
        print("Analysis complete!")
        print(f"Compliance Score: {status_data['result']['compliance_score']}")
        break
    elif status_data["status"] == "failed":
        print(f"Analysis failed: {status_data['error']}")
        break
    
    time.sleep(2)

# 4. Export to PDF
pdf_response = requests.post(
    f"{BASE_URL}/analysis/export-pdf/{task_id}",
    headers=headers
)
pdf_info = pdf_response.json()["pdf_info"]
print(f"PDF generated: {pdf_info['filename']}")

# 5. Chat with AI assistant
chat_response = requests.post(
    f"{BASE_URL}/chat/message",
    headers=headers,
    json={
        "message": "What are the key compliance requirements for PT progress notes?",
        "context": {"discipline": "PT"}
    }
)
print(f"AI Response: {chat_response.json()['response']}")
```

### cURL Examples

#### Login
```bash
curl -X POST "http://localhost:8000/api/auth/token" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=therapist1&password=SecurePass123"
```

#### Upload Document
```bash
curl -X POST "http://localhost:8000/api/analysis/analyze" \
  -H "Authorization: Bearer <token>" \
  -F "file=@patient_note.pdf" \
  -F "discipline=pt" \
  -F "analysis_mode=rubric"
```

#### Check Status
```bash
curl -X GET "http://localhost:8000/api/analysis/status/abc123" \
  -H "Authorization: Bearer <token>"
```

#### Export PDF
```bash
curl -X POST "http://localhost:8000/api/analysis/export-pdf/abc123" \
  -H "Authorization: Bearer <token>"
```

### JavaScript/TypeScript Example

```typescript
// API Client
class ComplianceAnalyzerAPI {
  private baseURL = 'http://localhost:8000/api';
  private token: string | null = null;

  async login(username: string, password: string): Promise<void> {
    const formData = new URLSearchParams();
    formData.append('username', username);
    formData.append('password', password);

    const response = await fetch(`${this.baseURL}/auth/token`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
      body: formData
    });

    const data = await response.json();
    this.token = data.access_token;
  }

  async analyzeDocument(file: File, discipline: string = 'pt'): Promise<string> {
    const formData = new FormData();
    formData.append('file', file);
    formData.append('discipline', discipline);
    formData.append('analysis_mode', 'rubric');

    const response = await fetch(`${this.baseURL}/analysis/analyze`, {
      method: 'POST',
      headers: { 'Authorization': `Bearer ${this.token}` },
      body: formData
    });

    const data = await response.json();
    return data.task_id;
  }

  async getAnalysisStatus(taskId: string): Promise<any> {
    const response = await fetch(`${this.baseURL}/analysis/status/${taskId}`, {
      headers: { 'Authorization': `Bearer ${this.token}` }
    });

    return await response.json();
  }

  async exportToPDF(taskId: string): Promise<any> {
    const response = await fetch(`${this.baseURL}/analysis/export-pdf/${taskId}`, {
      method: 'POST',
      headers: { 'Authorization': `Bearer ${this.token}` }
    });

    return await response.json();
  }
}

// Usage
const api = new ComplianceAnalyzerAPI();
await api.login('therapist1', 'SecurePass123');

const fileInput = document.querySelector('input[type="file"]') as HTMLInputElement;
const file = fileInput.files[0];

const taskId = await api.analyzeDocument(file, 'pt');
console.log('Analysis started:', taskId);

// Poll for completion
const checkStatus = async () => {
  const status = await api.getAnalysisStatus(taskId);
  
  if (status.status === 'completed') {
    console.log('Analysis complete!', status.result);
    const pdfInfo = await api.exportToPDF(taskId);
    console.log('PDF exported:', pdfInfo);
  } else if (status.status === 'processing') {
    setTimeout(checkStatus, 2000);
  }
};

checkStatus();
```

## Best Practices

### 1. Always Handle Errors
```python
try:
    response = requests.post(url, headers=headers, json=data)
    response.raise_for_status()
    return response.json()
except requests.exceptions.HTTPError as e:
    print(f"HTTP Error: {e.response.status_code} - {e.response.json()['detail']}")
except requests.exceptions.RequestException as e:
    print(f"Request failed: {e}")
```

### 2. Implement Retry Logic
```python
from tenacity import retry, stop_after_attempt, wait_exponential

@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
def make_api_request(url, headers, data):
    response = requests.post(url, headers=headers, json=data)
    response.raise_for_status()
    return response.json()
```

### 3. Use Connection Pooling
```python
session = requests.Session()
session.headers.update({"Authorization": f"Bearer {token}"})

# Reuse session for multiple requests
response1 = session.post(url1, json=data1)
response2 = session.post(url2, json=data2)
```

### 4. Validate Input Before Sending
```python
from src.core.security_validator import SecurityValidator

# Validate before API call
is_valid, error = SecurityValidator.validate_filename(filename)
if not is_valid:
    print(f"Invalid filename: {error}")
    return

# Proceed with API call
```

## Support

For additional help:
- Interactive API docs: http://localhost:8000/docs
- ReDoc documentation: http://localhost:8000/redoc
- GitHub Issues: [Project Repository]
- Email: support@example.com

## Changelog

### Version 1.0.0 (2025-01-01)
- Initial API release
- Document analysis endpoints
- PDF export functionality
- Dashboard analytics
- AI chat integration
- Rubric management
- Admin operations
