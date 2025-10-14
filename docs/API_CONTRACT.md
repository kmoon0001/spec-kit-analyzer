
# API Contract

This document outlines the API contract for the backend service.

## Authentication

### `POST /register`

Register a new user.

**Request Body:**

```json
{
  "username": "string",
  "password": "string"
}
```

**Response Body:**

```json
{
  "id": "integer",
  "username": "string",
  "is_active": "boolean"
}
```

### `POST /token`

Login for an access token.

**Request Body (form-data):**

```
username: your_username
password: your_password
```

**Response Body:**

```json
{
  "access_token": "string",
  "token_type": "bearer"
}
```

### `POST /login` (Legacy)

Legacy endpoint for logging in. Same as `/token`.

### `POST /users/change-password`

Change the current user's password.

**Request Body:**

```json
{
  "new_password": "string"
}
```

**Response Body:**

```json
{
  "status": "ok"
}
```

### `PUT /users/me/password`

Update the current user's password.

**Request Body:**

```json
{
  "old_password": "string",
  "new_password": "string"
}
```

**Response:** `204 No Content`

## Analysis

### `POST /analysis/analyze`

Upload and analyze a document.

**Request Body (form-data):**

```
file: (binary file)
discipline: "string" (e.g., "pt", "ot", "slp")
analysis_mode: "string" (e.g., "rubric", "comprehensive")
```

**Response Body:**

```json
{
  "task_id": "string",
  "status": "processing"
}
```

### `POST /analysis/submit`

Alias for `/analysis/analyze`.

### `GET /analysis/status/{task_id}`

Get the status of an analysis task.

**Response Body:**

```json
{
  "status": "string",
  "filename": "string",
  "timestamp": "string",
  "progress": "integer",
  "status_message": "string",
  "result": "object" // (if completed)
}
```

### `GET /analysis/all-tasks`

Get all analysis tasks.

**Response Body:**

```json
{
  "task_id": {
    "status": "string",
    "filename": "string",
    "timestamp": "string"
  }
}
```

### `POST /analysis/export-pdf/{task_id}`

Export an analysis report to PDF.

**Response Body:**

```json
{
  "success": "boolean",
  "task_id": "string",
  "pdf_info": "object",
  "message": "string"
}
```

### `POST /analysis/feedback`

Submit feedback on an AI finding.

**Request Body:**

```json
{
  "finding_id": "integer",
  "is_correct": "boolean",
  "suggested_correction": "string",
  "comment": "string"
}
```

**Response Body:**

```json
{
  "id": "integer",
  "finding_id": "integer",
  "user_id": "integer",
  "is_correct": "boolean",
  "suggested_correction": "string",
  "comment": "string",
  "created_at": "string"
}
```

## Admin

### `GET /admin/dashboard`

Get the admin dashboard HTML.

**Response:** HTML content.

### `GET /admin/settings`

Get current application settings.

**Response Body:**

```json
{
  "setting_key": "setting_value"
}
```

### `POST /admin/settings`

Update application settings.

**Request Body:**

```json
{
  "setting_key": "new_setting_value"
}
```

**Response Body:**

```json
{
  "message": "string"
}
```

### `GET /admin/users`

Get a list of users.

**Response Body:**

```json
[
  {
    "id": "integer",
    "username": "string",
    "is_active": "boolean"
  }
]
```

### `POST /admin/users`

Create a new user.

**Request Body:**

```json
{
  "username": "string",
  "password": "string"
}
```

**Response Body:**

```json
{
  "id": "integer",
  "username": "string",
  "is_active": "boolean"
}
```

### `PUT /admin/users/{user_id}/activate`

Activate a user.

**Response Body:**

```json
{
  "id": "integer",
  "username": "string",
  "is_active": "boolean"
}
```

### `PUT /admin/users/{user_id}/deactivate`

Deactivate a user.

**Response Body:**

```json
{
  "id": "integer",
  "username": "string",
  "is_active": "boolean"
}
```

## Chat

### `POST /chat/`

Chat with the AI.

**Request Body:**

```json
{
  "history": [
    {
      "role": "string",
      "content": "string"
    }
  ]
}
```

**Response Body:**

```json
{
  "response": "string"
}
```

## Compliance

### `GET /compliance/rubrics`

Get available compliance rubrics.

**Response Body:**

```json
{
  "rubrics": [
    {
      "id": "string",
      "name": "string",
      "discipline": "string",
      "description": "string"
    }
  ]
}
```

### `POST /compliance/evaluate`

Evaluate a document for compliance.

**Request Body:**

```json
{
  "id": "string",
  "text": "string",
  "discipline": "string",
  "document_type": "string"
}
```

**Response Body:**

```json
{
  "document": "object",
  "findings": "array",
  "is_compliant": "boolean"
}
```

## Dashboard

... (and so on for all other endpoints)

## WebSocket

### `WS /ws/analysis/{task_id}`

WebSocket for real-time analysis progress.

### `WS /ws/health`

WebSocket for real-time system health monitoring.

### `WS /ws/logs`

WebSocket for real-time log streaming.
