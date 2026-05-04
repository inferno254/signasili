"""
Authentication Pydantic Schemas
"""
from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, EmailStr, Field, validator
import re


class UserBase(BaseModel):
    """Base user schema."""
    email: EmailStr
    full_name: str = Field(..., min_length=2, max_length=255)
    role: str = Field(..., pattern="^(learner|teacher|parent|admin|earc_officer)$")
    phone_number: Optional[str] = None
    region: Optional[str] = None
    county: Optional[str] = None


class UserCreate(UserBase):
    """User registration schema."""
    password: str = Field(..., min_length=12)
    school_id: Optional[str] = None
    
    @validator("password")
    def validate_password(cls, v):
        """Validate password strength."""
        if not re.search(r"[A-Z]", v):
            raise ValueError("Password must contain at least one uppercase letter")
        if not re.search(r"[a-z]", v):
            raise ValueError("Password must contain at least one lowercase letter")
        if not re.search(r"\d", v):
            raise ValueError("Password must contain at least one number")
        if not re.search(r"[!@#$%^&*]", v):
            raise ValueError("Password must contain at least one special character (!@#$%^&*)")
        return v


class UserLogin(BaseModel):
    """User login schema."""
    email: EmailStr
    password: str
    device_name: Optional[str] = None


class UserResponse(UserBase):
    """User response schema."""
    id: str
    is_active: bool
    is_verified: bool
    created_at: datetime
    last_login: Optional[datetime] = None
    preferences: dict
    
    class Config:
        from_attributes = True


class TokenResponse(BaseModel):
    """Token response after login."""
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int  # seconds
    user: UserResponse


class PasswordResetRequest(BaseModel):
    """Password reset request schema."""
    email: EmailStr


class PasswordReset(BaseModel):
    """Password reset schema."""
    token: str
    new_password: str = Field(..., min_length=12)
    
    @validator("new_password")
    def validate_password(cls, v):
        """Validate password strength."""
        if not re.search(r"[A-Z]", v):
            raise ValueError("Password must contain at least one uppercase letter")
        if not re.search(r"[a-z]", v):
            raise ValueError("Password must contain at least one lowercase letter")
        if not re.search(r"\d", v):
            raise ValueError("Password must contain at least one number")
        if not re.search(r"[!@#$%^&*]", v):
            raise ValueError("Password must contain at least one special character (!@#$%^&*)")
        return v


class ChangePassword(BaseModel):
    """Change password schema."""
    old_password: str
    new_password: str = Field(..., min_length=12)
    
    @validator("new_password")
    def validate_password(cls, v):
        """Validate password strength."""
        if not re.search(r"[A-Z]", v):
            raise ValueError("Password must contain at least one uppercase letter")
        if not re.search(r"[a-z]", v):
            raise ValueError("Password must contain at least one lowercase letter")
        if not re.search(r"\d", v):
            raise ValueError("Password must contain at least one number")
        if not re.search(r"[!@#$%^&*]", v):
            raise ValueError("Password must contain at least one special character (!@#$%^&*)")
        return v


class EmailVerification(BaseModel):
    """Email verification schema."""
    token: str


class MFASetup(BaseModel):
    """MFA setup response schema."""
    secret: str
    qr_code_url: str
    backup_codes: List[str]


class MFAVerify(BaseModel):
    """MFA verification schema."""
    code: str


class MFALogin(BaseModel):
    """Login with MFA schema."""
    email: EmailStr
    password: str
    code: str


class SessionInfo(BaseModel):
    """Active session info."""
    device_name: Optional[str]
    last_active: datetime
    ip_address: Optional[str]


class SessionList(BaseModel):
    """List of active sessions."""
    sessions: List[SessionInfo]


class RefreshToken(BaseModel):
    """Refresh token schema."""
    refresh_token: str
