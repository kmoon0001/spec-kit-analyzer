"""Secure session management service.

This module provides secure session management capabilities including
session creation, validation, refresh, and cleanup.
"""

import logging
import secrets
import time
from datetime import datetime, timedelta
from typing import Any, Dict, Optional, Set

from jose import JWTError, jwt

from src.auth import get_auth_service
from src.database import models

logger = logging.getLogger(__name__)


class SessionManager:
    """Manages user sessions with security features."""

    def __init__(self, max_sessions_per_user: int = 5, session_timeout_minutes: int = 30):
        """
        Initialize session manager.

        Args:
            max_sessions_per_user: Maximum concurrent sessions per user
            session_timeout_minutes: Session timeout in minutes
        """
        self.max_sessions_per_user = max_sessions_per_user
        self.session_timeout_minutes = session_timeout_minutes
        self.auth_service = get_auth_service()

        # In-memory session storage (in production, use Redis or database)
        self._sessions: Dict[str, Dict[str, Any]] = {}
        self._user_sessions: Dict[int, Set[str]] = {}  # user_id -> session_ids

        # Session cleanup tracking
        self._last_cleanup = time.time()
        self._cleanup_interval = 300  # 5 minutes

    def create_session(self, user: models.User, client_info: Dict[str, Any]) -> str:
        """
        Create a new session for user.

        Args:
            user: User object
            client_info: Client information (IP, user agent, etc.)

        Returns:
            Session ID
        """
        # Clean up old sessions if needed
        self._cleanup_expired_sessions()

        # Check session limit
        user_sessions = self._user_sessions.get(user.id, set())
        if len(user_sessions) >= self.max_sessions_per_user:
            # Remove oldest session
            oldest_session_id = min(user_sessions, key=lambda sid: self._sessions[sid]['created_at'])
            self._remove_session(oldest_session_id)

        # Generate session ID
        session_id = secrets.token_urlsafe(32)

        # Create session data
        session_data = {
            'session_id': session_id,
            'user_id': user.id,
            'username': user.username,
            'created_at': time.time(),
            'last_activity': time.time(),
            'expires_at': time.time() + (self.session_timeout_minutes * 60),
            'client_info': client_info,
            'is_active': True,
            'refresh_count': 0,
        }

        # Store session
        self._sessions[session_id] = session_data

        # Track user sessions
        if user.id not in self._user_sessions:
            self._user_sessions[user.id] = set()
        self._user_sessions[user.id].add(session_id)

        logger.info(f"Session created for user {user.username}", extra={
            'session_id': session_id,
            'user_id': user.id,
            'client_ip': client_info.get('ip'),
            'user_agent': client_info.get('user_agent'),
        })

        return session_id

    def validate_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        """
        Validate session and return session data.

        Args:
            session_id: Session ID to validate

        Returns:
            Session data if valid, None otherwise
        """
        if not session_id or session_id not in self._sessions:
            return None

        session = self._sessions[session_id]

        # Check if session is active
        if not session['is_active']:
            return None

        # Check if session is expired
        if time.time() > session['expires_at']:
            self._remove_session(session_id)
            return None

        # Update last activity
        session['last_activity'] = time.time()

        return session

    def refresh_session(self, session_id: str) -> Optional[str]:
        """
        Refresh session expiration.

        Args:
            session_id: Session ID to refresh

        Returns:
            New session ID if refresh successful, None otherwise
        """
        session = self.validate_session(session_id)
        if not session:
            return None

        # Check refresh limit
        if session['refresh_count'] >= 10:  # Max 10 refreshes per session
            self._remove_session(session_id)
            return None

        # Extend expiration
        session['expires_at'] = time.time() + (self.session_timeout_minutes * 60)
        session['refresh_count'] += 1

        logger.info(f"Session refreshed for user {session['username']}", extra={
            'session_id': session_id,
            'user_id': session['user_id'],
            'refresh_count': session['refresh_count'],
        })

        return session_id

    def invalidate_session(self, session_id: str) -> bool:
        """
        Invalidate a specific session.

        Args:
            session_id: Session ID to invalidate

        Returns:
            True if session was invalidated, False if not found
        """
        if session_id not in self._sessions:
            return False

        session = self._sessions[session_id]
        user_id = session['user_id']

        # Remove from user sessions
        if user_id in self._user_sessions:
            self._user_sessions[user_id].discard(session_id)
            if not self._user_sessions[user_id]:
                del self._user_sessions[user_id]

        # Remove session
        del self._sessions[session_id]

        logger.info(f"Session invalidated for user {session['username']}", extra={
            'session_id': session_id,
            'user_id': user_id,
        })

        return True

    def invalidate_user_sessions(self, user_id: int) -> int:
        """
        Invalidate all sessions for a user.

        Args:
            user_id: User ID to invalidate sessions for

        Returns:
            Number of sessions invalidated
        """
        if user_id not in self._user_sessions:
            return 0

        session_ids = list(self._user_sessions[user_id])
        invalidated_count = 0

        for session_id in session_ids:
            if self.invalidate_session(session_id):
                invalidated_count += 1

        logger.info(f"Invalidated {invalidated_count} sessions for user {user_id}")
        return invalidated_count

    def get_user_sessions(self, user_id: int) -> list[Dict[str, Any]]:
        """
        Get all active sessions for a user.

        Args:
            user_id: User ID

        Returns:
            List of session data
        """
        if user_id not in self._user_sessions:
            return []

        sessions = []
        for session_id in self._user_sessions[user_id]:
            session = self._sessions.get(session_id)
            if session and session['is_active'] and time.time() <= session['expires_at']:
                # Return safe session data (without sensitive info)
                sessions.append({
                    'session_id': session['session_id'],
                    'created_at': session['created_at'],
                    'last_activity': session['last_activity'],
                    'expires_at': session['expires_at'],
                    'client_info': session['client_info'],
                    'refresh_count': session['refresh_count'],
                })

        return sessions

    def _remove_session(self, session_id: str) -> None:
        """Remove session from storage."""
        if session_id in self._sessions:
            session = self._sessions[session_id]
            user_id = session['user_id']

            # Remove from user sessions
            if user_id in self._user_sessions:
                self._user_sessions[user_id].discard(session_id)
                if not self._user_sessions[user_id]:
                    del self._user_sessions[user_id]

            # Remove session
            del self._sessions[session_id]

    def _cleanup_expired_sessions(self) -> None:
        """Clean up expired sessions."""
        current_time = time.time()

        # Only cleanup every 5 minutes
        if current_time - self._last_cleanup < self._cleanup_interval:
            return

        self._last_cleanup = current_time

        expired_sessions = []
        for session_id, session in self._sessions.items():
            if current_time > session['expires_at']:
                expired_sessions.append(session_id)

        for session_id in expired_sessions:
            self._remove_session(session_id)

        if expired_sessions:
            logger.info(f"Cleaned up {len(expired_sessions)} expired sessions")

    def get_session_stats(self) -> Dict[str, Any]:
        """Get session statistics."""
        active_sessions = sum(1 for s in self._sessions.values() if s['is_active'] and time.time() <= s['expires_at'])
        total_sessions = len(self._sessions)
        unique_users = len(self._user_sessions)

        return {
            'active_sessions': active_sessions,
            'total_sessions': total_sessions,
            'unique_users': unique_users,
            'max_sessions_per_user': self.max_sessions_per_user,
            'session_timeout_minutes': self.session_timeout_minutes,
        }


class SessionSecurityValidator:
    """Validates session security and detects suspicious activity."""

    def __init__(self, session_manager: SessionManager):
        self.session_manager = session_manager
        self._failed_attempts: Dict[str, int] = {}  # IP -> count
        self._blocked_ips: Set[str] = set()
        self._max_failed_attempts = 5
        self._block_duration = 3600  # 1 hour

    def validate_session_security(self, session_id: str, client_info: Dict[str, Any]) -> bool:
        """
        Validate session security.

        Args:
            session_id: Session ID
            client_info: Client information

        Returns:
            True if session is secure, False otherwise
        """
        client_ip = client_info.get('ip', '')

        # Check if IP is blocked
        if client_ip in self._blocked_ips:
            logger.warning(f"Blocked IP attempted session access: {client_ip}")
            return False

        # Validate session
        session = self.session_manager.validate_session(session_id)
        if not session:
            self._record_failed_attempt(client_ip)
            return False

        # Check for suspicious activity
        if self._is_suspicious_activity(session, client_info):
            logger.warning(f"Suspicious activity detected for session {session_id}")
            self.session_manager.invalidate_session(session_id)
            return False

        # Reset failed attempts on successful validation
        if client_ip in self._failed_attempts:
            del self._failed_attempts[client_ip]

        return True

    def _record_failed_attempt(self, client_ip: str) -> None:
        """Record failed authentication attempt."""
        if client_ip not in self._failed_attempts:
            self._failed_attempts[client_ip] = 0

        self._failed_attempts[client_ip] += 1

        if self._failed_attempts[client_ip] >= self._max_failed_attempts:
            self._blocked_ips.add(client_ip)
            logger.warning(f"IP {client_ip} blocked due to too many failed attempts")

            # Schedule unblocking
            import threading
            def unblock():
                import time
                time.sleep(self._block_duration)
                self._blocked_ips.discard(client_ip)
                if client_ip in self._failed_attempts:
                    del self._failed_attempts[client_ip]
                logger.info(f"IP {client_ip} unblocked")

            threading.Thread(target=unblock, daemon=True).start()

    def _is_suspicious_activity(self, session: Dict[str, Any], client_info: Dict[str, Any]) -> bool:
        """Check for suspicious activity patterns."""
        # Check IP change
        if session['client_info'].get('ip') != client_info.get('ip'):
            return True

        # Check user agent change
        if session['client_info'].get('user_agent') != client_info.get('user_agent'):
            return True

        # Check for rapid session refreshes
        if session['refresh_count'] > 5:
            return True

        return False


# Global session manager instance
_session_manager: Optional[SessionManager] = None
_security_validator: Optional[SessionSecurityValidator] = None


def get_session_manager() -> SessionManager:
    """Get global session manager instance."""
    global _session_manager
    if _session_manager is None:
        _session_manager = SessionManager()
    return _session_manager


def get_session_security_validator() -> SessionSecurityValidator:
    """Get global session security validator instance."""
    global _security_validator
    if _security_validator is None:
        _security_validator = SessionSecurityValidator(get_session_manager())
    return _security_validator
