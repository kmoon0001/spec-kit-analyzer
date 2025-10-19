from datetime import UTC, datetime, timedelta
from functools import lru_cache

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt  # type: ignore[import-untyped]
from passlib.context import CryptContext  # type: ignore[import-untyped]
from sqlalchemy.ext.asyncio import AsyncSession

from src.config import get_settings
from src.database import crud, models, schemas
from src.database.database import get_async_db

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/token")


class AuthService:
    def __init__(self):
        settings = get_settings()
        # Ensure a non-empty secret key to prevent runtime failures
        if not settings.auth.secret_key:
            raise ValueError("AUTH_SECRET_KEY environment variable must be set for security")
        self.secret_key = settings.auth.secret_key.get_secret_value()
        self.algorithm = settings.auth.algorithm
        self.access_token_expire_minutes = settings.auth.access_token_expire_minutes

    def create_access_token(self, data: dict, expires_delta: timedelta | None = None):
        to_encode = data.copy()
        if expires_delta:
            expire = datetime.now(UTC) + expires_delta
        else:
            expire = datetime.now(UTC) + timedelta(minutes=self.access_token_expire_minutes)
        to_encode.update({"exp": expire})
        encoded_jwt = jwt.encode(to_encode, self.secret_key, algorithm=self.algorithm)
        return encoded_jwt

    @staticmethod
    def verify_password(plain_password, hashed_password):
        """Verify password using bcrypt. No fallback to weak hashing."""
        try:
            return pwd_context.verify(plain_password, hashed_password)
        except (ValueError, TypeError) as e:
            # Log the error for security monitoring
            import logging
            logger = logging.getLogger(__name__)
            logger.warning(f"Password verification failed: {e}")

            # Force password reset instead of fallback
            raise ValueError(
                "Password format outdated or invalid. Please reset your password."
            )

    @staticmethod
    def get_password_hash(password: str) -> str:
        # bcrypt passwords must be 72 bytes or less. Truncate if necessary.
        # passlib handles encoding to bytes internally, so we truncate the string.
        truncated_password = password[:72]
        return pwd_context.hash(truncated_password)


@lru_cache
def get_auth_service() -> AuthService:
    return AuthService()


async def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_async_db),
    auth_service: AuthService = Depends(get_auth_service),
) -> models.User:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, auth_service.secret_key, algorithms=[auth_service.algorithm])
        username: str | None = payload.get("sub")
        if username is None:
            raise credentials_exception
        token_data = schemas.TokenData(username=username)
    except JWTError:
        raise credentials_exception from None

    if token_data.username is None:
        raise credentials_exception from None

    user = await crud.get_user_by_username(db, username=token_data.username)
    if user is None:
        raise credentials_exception from None
    return user


async def get_current_active_user(current_user: models.User = Depends(get_current_user)) -> models.User:
    if not current_user.is_active:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Inactive user")
    return current_user


async def get_current_admin_user(current_user: models.User = Depends(get_current_active_user)) -> models.User:
    if not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="The user does not have administrative privileges."
        )
    return current_user
