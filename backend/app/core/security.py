"""
Security utilities for authentication and authorization
"""
from datetime import datetime, timedelta
from typing import Optional, Union
from jose import JWTError, jwt
from passlib.context import CryptContext
from fastapi import HTTPException, status
from app.core.config import settings

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against its hash."""
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    """Hash a password."""
    return pwd_context.hash(password)


def validate_password_strength(password: str) -> tuple[bool, str]:
    """
    Validate password meets policy requirements.
    Returns (is_valid, error_message)
    """
    if len(password) < settings.PASSWORD_MIN_LENGTH:
        return False, f"Password must be at least {settings.PASSWORD_MIN_LENGTH} characters"
    
    if settings.PASSWORD_REQUIRE_UPPERCASE and not any(c.isupper() for c in password):
        return False, "Password must contain at least one uppercase letter"
    
    if settings.PASSWORD_REQUIRE_LOWERCASE and not any(c.islower() for c in password):
        return False, "Password must contain at least one lowercase letter"
    
    if settings.PASSWORD_REQUIRE_NUMBERS and not any(c.isdigit() for c in password):
        return False, "Password must contain at least one number"
    
    if settings.PASSWORD_REQUIRE_SPECIAL:
        special_chars = "!@#$%^&*"
        if not any(c in special_chars for c in password):
            return False, "Password must contain at least one special character (!@#$%^&*)"
    
    return True, ""


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """Create JWT access token."""
    to_encode = data.copy()
    
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    
    to_encode.update({"exp": expire, "type": "access"})
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return encoded_jwt


def create_refresh_token(data: dict) -> str:
    """Create JWT refresh token."""
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
    to_encode.update({"exp": expire, "type": "refresh"})
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return encoded_jwt


def decode_token(token: str) -> Optional[dict]:
    """Decode and validate JWT token."""
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        return payload
    except JWTError:
        return None


def generate_verification_code() -> str:
    """Generate 6-digit verification code."""
    import random
    return "".join([str(random.randint(0, 9)) for _ in range(6)])


def generate_backup_codes() -> list[str]:
    """Generate 10 backup codes for MFA."""
    import secrets
    return [secrets.token_hex(4) for _ in range(10)]


# Role-based permissions
ROLE_PERMISSIONS = {
    "learner": [
        "view_own_profile",
        "edit_own_profile",
        "take_lessons",
        "view_own_progress",
    ],
    "teacher": [
        "view_own_profile",
        "edit_own_profile",
        "view_class_students",
        "view_class_progress",
        "view_student_progress",
        "create_intervention",
        "assign_lessons",
        "export_reports",
        "view_class_analytics",
    ],
    "parent": [
        "view_own_profile",
        "edit_own_profile",
        "view_child_progress",
        "view_bridge_progress",
        "create_coop_challenge",
    ],
    "admin": [
        "view_all_users",
        "edit_any_user",
        "delete_user",
        "create_content",
        "edit_content",
        "delete_content",
        "approve_content",
        "create_badges",
        "view_all_progress",
        "view_all_analytics",
        "system_settings",
    ],
    "earc_officer": [
        "view_assigned_schools",
        "view_assigned_learners",
        "sync_offline_data",
        "manage_offline_packs",
    ],
}


def check_permission(user_role: str, permission: str) -> bool:
    """Check if role has specific permission."""
    if user_role == "admin":
        return True
    return permission in ROLE_PERMISSIONS.get(user_role, [])


class AuthError(HTTPException):
    """Authentication/Authorization error."""
    def __init__(self, detail: str = "Authentication failed"):
        super().__init__(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=detail,
            headers={"WWW-Authenticate": "Bearer"},
        )
