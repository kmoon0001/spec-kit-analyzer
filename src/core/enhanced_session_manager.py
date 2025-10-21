"""Enhanced session management with security features.

This module provides comprehensive session management including:
- Session timeout enforcement
- Concurrent session limits
- Session invalidation on password change
- Secure session storage
- Session activity tracking
"""

import logging
import time
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Set

logger = logging.getLogger(__name__)


@dataclass
class SessionInfo:
    """Information about a user session."""

    session_id: str
    user_id: int
    username: str
    created_at: datetime
    last_activity: datetime
    ip_address: str
    user_agent: str
    login_method: str
    is_active: bool = True
    activity_count: int = 0


class EnhancedSessionManager:
    """Enhanced session manager with security features."""

    def __init__(
        self,
        session_timeout_minutes: int = 30,
        max_concurrent_sessions: int = 3,
        max_inactive_minutes: int = 15,
        cleanup_interval_minutes: int = 5,
    ):
        self.session_timeout_minutes = session_timeout_minutes
        self.max_concurrent_sessions = max_concurrent_sessions
        self.max_inactive_minutes = max_inactive_minutes
        self.cleanup_interval_minutes = cleanup_interval_minutes

        # Session storage: session_id -> SessionInfo
        self._sessions: Dict[str, SessionInfo] = {}

        # User sessions: user_id -> Set[session_id]
        self._user_sessions: Dict[int, Set[str]] = defaultdict(set)

        # IP sessions: ip_address -> Set[session_id]
        self._ip_sessions: Dict[str, Set[str]] = defaultdict(set)

        self._last_cleanup = time.time()

    def create_session(
        self,
        user_id: int,
        username: str,
        ip_address: str,
        user_agent: str,
        login_method: str = "password",
    ) -> str:
        """Create a new session with security checks."""
        try:
            # Check concurrent session limit
            self._enforce_concurrent_session_limit(user_id)

            # Generate unique session ID
            session_id = self._generate_session_id()

            # Create session info
            now = datetime.utcnow()
            session_info = SessionInfo(
                session_id=session_id,
                user_id=user_id,
                username=username,
                created_at=now,
                last_activity=now,
                ip_address=ip_address,
                user_agent=user_agent,
                login_method=login_method,
            )

            # Store session
            self._sessions[session_id] = session_info
            self._user_sessions[user_id].add(session_id)
            self._ip_sessions[ip_address].add(session_id)

            # Cleanup old sessions if needed
            self._cleanup_if_needed()

            logger.info(
                f"Session created for user {username} (user_id={user_id}, session_id={session_id}, ip={ip_address})"
            )

            return session_id

        except Exception as e:
            logger.error(f"Failed to create session for user {user_id}: {e}")
            raise

    def validate_session(
        self, session_id: str, ip_address: str
    ) -> Optional[SessionInfo]:
        """Validate session and update activity."""
        try:
            session_info = self._sessions.get(session_id)
            if not session_info or not session_info.is_active:
                return None

            # Check if session is expired
            if self._is_session_expired(session_info):
                self._invalidate_session(session_id)
                return None

            # Check IP address (basic security check)
            if session_info.ip_address != ip_address:
                logger.warning(
                    f"Session IP mismatch: {session_id} (expected={session_info.ip_address}, actual={ip_address})"
                )
                # Don't invalidate immediately, but log for monitoring

            # Update activity
            session_info.last_activity = datetime.utcnow()
            session_info.activity_count += 1

            return session_info

        except Exception as e:
            logger.error(f"Session validation error: {e}")
            return None

    def invalidate_session(self, session_id: str) -> bool:
        """Invalidate a specific session."""
        return self._invalidate_session(session_id)

    def invalidate_user_sessions(
        self, user_id: int, keep_current: Optional[str] = None
    ) -> int:
        """Invalidate all sessions for a user, optionally keeping one."""
        try:
            user_session_ids = list(self._user_sessions.get(user_id, set()))
            invalidated_count = 0

            for session_id in user_session_ids:
                if keep_current and session_id == keep_current:
                    continue

                if self._invalidate_session(session_id):
                    invalidated_count += 1

            logger.info(f"Invalidated {invalidated_count} sessions for user {user_id}")
            return invalidated_count

        except Exception as e:
            logger.error(f"Failed to invalidate user sessions: {e}")
            return 0

    def invalidate_password_change_sessions(self, user_id: int) -> int:
        """Invalidate all sessions for a user after password change."""
        logger.info(
            f"Invalidating all sessions for user {user_id} due to password change"
        )
        return self.invalidate_user_sessions(user_id)

    def get_user_sessions(self, user_id: int) -> List[SessionInfo]:
        """Get all active sessions for a user."""
        try:
            user_session_ids = self._user_sessions.get(user_id, set())
            sessions = []

            for session_id in user_session_ids:
                session_info = self._sessions.get(session_id)
                if session_info and session_info.is_active:
                    sessions.append(session_info)

            return sessions

        except Exception as e:
            logger.error(f"Failed to get user sessions: {e}")
            return []

    def get_session_stats(self) -> Dict[str, int]:
        """Get session statistics."""
        try:
            active_sessions = sum(1 for s in self._sessions.values() if s.is_active)
            total_users = len(self._user_sessions)
            total_ips = len(self._ip_sessions)

            return {
                "active_sessions": active_sessions,
                "total_users": total_users,
                "total_ips": total_ips,
                "total_sessions": len(self._sessions),
            }

        except Exception as e:
            logger.error(f"Failed to get session stats: {e}")
            return {}

    def cleanup_expired_sessions(self) -> int:
        """Clean up expired sessions."""
        try:
            expired_sessions = []
            now = datetime.utcnow()

            for session_id, session_info in self._sessions.items():
                if not session_info.is_active:
                    continue

                # Check for timeout
                if now - session_info.created_at > timedelta(
                    minutes=self.session_timeout_minutes
                ):
                    expired_sessions.append(session_id)
                    continue

                # Check for inactivity
                if now - session_info.last_activity > timedelta(
                    minutes=self.max_inactive_minutes
                ):
                    expired_sessions.append(session_id)
                    continue

            # Invalidate expired sessions
            for session_id in expired_sessions:
                self._invalidate_session(session_id)

            if expired_sessions:
                logger.info(f"Cleaned up {len(expired_sessions)} expired sessions")

            return len(expired_sessions)

        except Exception as e:
            logger.error(f"Session cleanup error: {e}")
            return 0

    def _generate_session_id(self) -> str:
        """Generate a secure session ID."""
        import secrets

        return secrets.token_urlsafe(32)

    def _enforce_concurrent_session_limit(self, user_id: int):
        """Enforce concurrent session limit for a user."""
        user_session_ids = self._user_sessions.get(user_id, set())
        active_sessions = sum(
            1 for sid in user_session_ids if self._sessions.get(sid, {}).is_active
        )

        if active_sessions >= self.max_concurrent_sessions:
            # Invalidate oldest session
            oldest_session = None
            oldest_time = None

            for session_id in user_session_ids:
                session_info = self._sessions.get(session_id)
                if session_info and session_info.is_active:
                    if oldest_time is None or session_info.created_at < oldest_time:
                        oldest_time = session_info.created_at
                        oldest_session = session_id

            if oldest_session:
                self._invalidate_session(oldest_session)
                logger.info(
                    f"Invalidated oldest session {oldest_session} due to concurrent limit"
                )

    def _is_session_expired(self, session_info: SessionInfo) -> bool:
        """Check if session is expired."""
        now = datetime.utcnow()

        # Check absolute timeout
        if now - session_info.created_at > timedelta(
            minutes=self.session_timeout_minutes
        ):
            return True

        # Check inactivity timeout
        if now - session_info.last_activity > timedelta(
            minutes=self.max_inactive_minutes
        ):
            return True

        return False

    def _invalidate_session(self, session_id: str) -> bool:
        """Internal method to invalidate a session."""
        try:
            session_info = self._sessions.get(session_id)
            if not session_info:
                return False

            # Mark as inactive
            session_info.is_active = False

            # Remove from user sessions
            self._user_sessions[session_info.user_id].discard(session_id)

            # Remove from IP sessions
            self._ip_sessions[session_info.ip_address].discard(session_id)

            # Remove from main sessions dict
            del self._sessions[session_id]

            logger.debug(f"Session invalidated: {session_id}")
            return True

        except Exception as e:
            logger.error(f"Failed to invalidate session {session_id}: {e}")
            return False

    def _cleanup_if_needed(self):
        """Clean up expired sessions if cleanup interval has passed."""
        now = time.time()
        if now - self._last_cleanup > self.cleanup_interval_minutes * 60:
            self.cleanup_expired_sessions()
            self._last_cleanup = now


# Global session manager instance
_session_manager: Optional[EnhancedSessionManager] = None


def get_session_manager() -> EnhancedSessionManager:
    """Get global session manager instance."""
    global _session_manager
    if _session_manager is None:
        _session_manager = EnhancedSessionManager()
    return _session_manager


def initialize_session_manager(
    session_timeout_minutes: int = 30,
    max_concurrent_sessions: int = 3,
    max_inactive_minutes: int = 15,
) -> EnhancedSessionManager:
    """Initialize session manager with custom settings."""
    global _session_manager
    _session_manager = EnhancedSessionManager(
        session_timeout_minutes=session_timeout_minutes,
        max_concurrent_sessions=max_concurrent_sessions,
        max_inactive_minutes=max_inactive_minutes,
    )
    return _session_manager
