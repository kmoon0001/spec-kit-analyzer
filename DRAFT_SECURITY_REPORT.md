## Security Audit Report

### 1. Hardcoded Admin Password in Logs

*   **Vulnerability:** Hardcoded Admin Password in Logs
*   **Severity:** Critical
*   **Location:** `src\core\create_db.py`
*   **Line Content:** `logging.info("Admin password: %s", admin_password)`
*   **Description:** The application logs the admin password in plain text when the database is created. This could allow an attacker who gains access to the logs to compromise the admin account.
*   **Recommendation:** Remove the line that logs the admin password. Never log passwords or other sensitive credentials.