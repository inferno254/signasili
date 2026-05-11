"""
Email service for sending verification and password reset emails
"""
from typing import Optional
from fastapi import HTTPException


async def send_verification_email(email: str, verification_code: str):
    """Send verification email to user."""
    # TODO: Implement actual email sending logic
    print(f"Verification email sent to {email} with code: {verification_code}")
    return True


async def send_password_reset_email(email: str, reset_token: str):
    """Send password reset email to user."""
    # TODO: Implement actual email sending logic
    print(f"Password reset email sent to {email} with token: {reset_token}")
    return True
