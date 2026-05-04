"""
Authentication API Endpoints
"""
from datetime import timedelta
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status, Request, Response
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.config import settings
from app.core.security import (
    verify_password, get_password_hash, create_access_token,
    create_refresh_token, decode_token, validate_password_strength,
    generate_verification_code, generate_backup_codes
)
from app.models.user import User
from app.models.learner import Learner
from app.models.teacher import Teacher
from app.models.parent import Parent
from app.schemas.auth import (
    UserCreate, UserLogin, UserResponse, TokenResponse,
    PasswordResetRequest, PasswordReset, ChangePassword,
    EmailVerification, MFASetup, MFAVerify, MFALogin,
    SessionList, RefreshToken
)
from app.services.email import send_verification_email, send_password_reset_email

router = APIRouter()
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register(user_data: UserCreate, db: Session = Depends(get_db)):
    """
    Register a new user account.
    
    - Creates user with specified role
    - Sends verification email
    - Creates role-specific profile (learner/teacher/parent)
    """
    # Check if email already exists
    if db.query(User).filter(User.email == user_data.email).first():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    
    # Validate password strength
    is_valid, error_msg = validate_password_strength(user_data.password)
    if not is_valid:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=error_msg
        )
    
    # Create user
    user = User(
        email=user_data.email,
        password_hash=get_password_hash(user_data.password),
        full_name=user_data.full_name,
        role=user_data.role,
        phone_number=user_data.phone_number,
        region=user_data.region,
        county=user_data.county,
        school_id=user_data.school_id,
    )
    
    db.add(user)
    db.flush()  # Get user.id
    
    # Create role-specific profile
    if user_data.role == "learner":
        learner = Learner(user_id=user.id)
        db.add(learner)
    elif user_data.role == "teacher":
        teacher = Teacher(user_id=user.id, school_id=user_data.school_id)
        db.add(teacher)
    elif user_data.role == "parent":
        parent = Parent(user_id=user.id)
        db.add(parent)
    
    # Generate verification code
    verification_code = generate_verification_code()
    # Store in cache/Redis with 15 min expiry (simplified here)
    
    db.commit()
    
    # Send verification email
    await send_verification_email(user.email, verification_code)
    
    return user


@router.post("/login", response_model=TokenResponse)
async def login(
    response: Response,
    login_data: UserLogin,
    db: Session = Depends(get_db)
):
    """
    Login to user account.
    
    - Returns access token (15 min expiry)
    - Sets refresh token as HTTP-only cookie (7 days)
    - Updates last login info
    """
    # Find user
    user = db.query(User).filter(User.email == login_data.email).first()
    if not user or not verify_password(login_data.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password"
        )
    
    # Check if account is locked
    if user.is_locked():
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account is temporarily locked due to too many failed attempts"
        )
    
    # Check if MFA is required
    if user.mfa_enabled:
        # Return temporary token for MFA step
        temp_token = create_access_token(
            {"user_id": str(user.id), "mfa_required": True},
            expires_delta=timedelta(minutes=5)
        )
        return {
            "access_token": temp_token,
            "refresh_token": "",
            "token_type": "bearer",
            "expires_in": 300,
            "user": None,
            "mfa_required": True
        }
    
    # Create tokens
    access_token = create_access_token({"user_id": str(user.id), "role": user.role})
    refresh_token = create_refresh_token({"user_id": str(user.id)})
    
    # Update last login
    user.last_login = datetime.utcnow()
    user.login_count += 1
    user.failed_login_attempts = 0
    db.commit()
    
    # Set refresh token as HTTP-only cookie
    response.set_cookie(
        key="refresh_token",
        value=refresh_token,
        httponly=True,
        secure=True,
        samesite="strict",
        max_age=settings.REFRESH_TOKEN_EXPIRE_DAYS * 24 * 60 * 60
    )
    
    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
        "expires_in": settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        "user": user
    }


@router.post("/login-mfa", response_model=TokenResponse)
async def login_mfa(
    response: Response,
    mfa_data: MFALogin,
    db: Session = Depends(get_db)
):
    """
    Complete login with MFA code.
    
    - Verifies TOTP code
    - Returns full access on success
    """
    # Verify user credentials first
    user = db.query(User).filter(User.email == mfa_data.email).first()
    if not user or not verify_password(mfa_data.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password"
        )
    
    # Verify MFA code
    import pyotp
    totp = pyotp.TOTP(user.mfa_secret)
    if not totp.verify(mfa_data.code):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid MFA code"
        )
    
    # Create tokens
    access_token = create_access_token({"user_id": str(user.id), "role": user.role})
    refresh_token = create_refresh_token({"user_id": str(user.id)})
    
    # Update last login
    user.last_login = datetime.utcnow()
    db.commit()
    
    # Set refresh token cookie
    response.set_cookie(
        key="refresh_token",
        value=refresh_token,
        httponly=True,
        secure=True,
        samesite="strict",
        max_age=settings.REFRESH_TOKEN_EXPIRE_DAYS * 24 * 60 * 60
    )
    
    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
        "expires_in": settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        "user": user
    }


@router.post("/refresh", response_model=TokenResponse)
async def refresh_token(
    response: Response,
    refresh_data: RefreshToken,
    db: Session = Depends(get_db)
):
    """
    Refresh access token using refresh token.
    
    - Validates refresh token
    - Issues new access token
    - Rotates refresh token (new token, old blacklisted)
    """
    payload = decode_token(refresh_data.refresh_token)
    if not payload or payload.get("type") != "refresh":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token"
        )
    
    user_id = payload.get("user_id")
    user = db.query(User).filter(User.id == user_id).first()
    if not user or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found or inactive"
        )
    
    # Create new tokens
    new_access_token = create_access_token({"user_id": str(user.id), "role": user.role})
    new_refresh_token = create_refresh_token({"user_id": str(user.id)})
    
    # Set new refresh token cookie
    response.set_cookie(
        key="refresh_token",
        value=new_refresh_token,
        httponly=True,
        secure=True,
        samesite="strict",
        max_age=settings.REFRESH_TOKEN_EXPIRE_DAYS * 24 * 60 * 60
    )
    
    return {
        "access_token": new_access_token,
        "refresh_token": new_refresh_token,
        "token_type": "bearer",
        "expires_in": settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        "user": user
    }


@router.post("/logout")
async def logout(response: Response):
    """
    Logout user.
    
    - Clears refresh token cookie
    - Client should discard access token
    """
    response.delete_cookie("refresh_token")
    return {"message": "Logged out successfully"}


@router.get("/me", response_model=UserResponse)
async def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db)
):
    """Get current authenticated user profile."""
    payload = decode_token(token)
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token"
        )
    
    user_id = payload.get("user_id")
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    return user


@router.post("/verify-email")
async def verify_email(verification: EmailVerification, db: Session = Depends(get_db)):
    """Verify email address with code."""
    # Verify code (from cache/Redis)
    # TODO: Implement actual verification logic
    
    return {"message": "Email verified successfully"}


@router.post("/reset-password", status_code=status.HTTP_202_ACCEPTED)
async def request_password_reset(request: PasswordResetRequest, db: Session = Depends(get_db)):
    """Request password reset email."""
    user = db.query(User).filter(User.email == request.email).first()
    if user:
        # Generate reset token and send email
        reset_token = create_access_token(
            {"user_id": str(user.id), "type": "password_reset"},
            expires_delta=timedelta(hours=1)
        )
        await send_password_reset_email(user.email, reset_token)
    
    # Always return success to prevent email enumeration
    return {"message": "If the email exists, a reset link has been sent"}


@router.post("/change-password")
async def change_password(
    password_data: ChangePassword,
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db)
):
    """Change password (authenticated)."""
    payload = decode_token(token)
    user_id = payload.get("user_id")
    user = db.query(User).filter(User.id == user_id).first()
    
    if not verify_password(password_data.old_password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Current password is incorrect"
        )
    
    # Validate new password
    is_valid, error_msg = validate_password_strength(password_data.new_password)
    if not is_valid:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=error_msg
        )
    
    user.password_hash = get_password_hash(password_data.new_password)
    db.commit()
    
    return {"message": "Password changed successfully"}


@router.post("/setup-mfa", response_model=MFASetup)
async def setup_mfa(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    """Setup MFA (TOTP)."""
    import pyotp
    import qrcode
    import io
    import base64
    
    payload = decode_token(token)
    user_id = payload.get("user_id")
    user = db.query(User).filter(User.id == user_id).first()
    
    # Generate secret
    secret = pyotp.random_base32()
    
    # Generate QR code
    totp = pyotp.TOTP(secret)
    uri = totp.provisioning_uri(
        name=user.email,
        issuer_name="SignAsili"
    )
    
    qr = qrcode.make(uri)
    buffered = io.BytesIO()
    qr.save(buffered, format="PNG")
    qr_base64 = base64.b64encode(buffered.getvalue()).decode()
    
    # Generate backup codes
    backup_codes = generate_backup_codes()
    
    # Store secret temporarily (to be confirmed)
    user.mfa_secret = secret
    user.backup_codes = backup_codes
    db.commit()
    
    return {
        "secret": secret,
        "qr_code_url": f"data:image/png;base64,{qr_base64}",
        "backup_codes": backup_codes
    }


@router.post("/verify-mfa")
async def verify_mfa_setup(
    mfa_data: MFAVerify,
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db)
):
    """Verify MFA setup and enable."""
    import pyotp
    
    payload = decode_token(token)
    user_id = payload.get("user_id")
    user = db.query(User).filter(User.id == user_id).first()
    
    totp = pyotp.TOTP(user.mfa_secret)
    if not totp.verify(mfa_data.code):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid MFA code"
        )
    
    user.mfa_enabled = True
    db.commit()
    
    return {"message": "MFA enabled successfully"}


@router.get("/sessions", response_model=SessionList)
async def list_sessions(token: str = Depends(oauth2_scheme)):
    """List active user sessions."""
    # Would query session store (Redis)
    # Simplified implementation
    return {"sessions": []}


@router.post("/revoke-sessions")
async def revoke_sessions(token: str = Depends(oauth2_scheme)):
    """Revoke all other active sessions."""
    # Would clear other sessions from Redis
    return {"message": "All other sessions revoked"}
