"""
User model - Base user account for all roles
"""
import uuid
from datetime import datetime
from sqlalchemy import Column, String, Boolean, DateTime, Integer, JSON, ARRAY, Text
from sqlalchemy.dialects.postgresql import UUID, INET
from app.core.database import Base


class User(Base):
    """Base user model for learners, teachers, parents, admins, EARC officers."""
    __tablename__ = "users"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email = Column(String(255), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    full_name = Column(String(255), nullable=False)
    role = Column(String(50), nullable=False, index=True)  # learner, teacher, parent, admin, earc_officer
    phone_number = Column(String(20))
    region = Column(String(100))
    county = Column(String(50))
    school_id = Column(UUID(as_uuid=True), index=True)
    
    # Status flags
    is_active = Column(Boolean, default=True)
    is_verified = Column(Boolean, default=False)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    last_login = Column(DateTime)
    
    # Security
    last_login_ip = Column(INET)
    last_login_device = Column(Text)
    login_count = Column(Integer, default=0)
    failed_login_attempts = Column(Integer, default=0)
    locked_until = Column(DateTime)
    
    # Preferences
    preferences = Column(JSON, default={
        "language": "en",
        "dark_mode": False,
        "font_scale": 100,
        "high_contrast": False,
        "notifications": True,
        "auto_play_videos": True,
        "default_video_speed": 1.0,
    })
    
    # MFA
    mfa_enabled = Column(Boolean, default=False)
    mfa_secret = Column(Text)
    backup_codes = Column(ARRAY(String), default=[])
    
    # Device tokens for push notifications
    device_tokens = Column(JSON, default=[])
    
    def __repr__(self):
        return f"<User {self.email} ({self.role})>"
    
    def is_locked(self) -> bool:
        """Check if account is temporarily locked."""
        if self.locked_until and self.locked_until > datetime.utcnow():
            return True
        return False
    
    def get_preference(self, key: str, default=None):
        """Get user preference."""
        return self.preferences.get(key, default) if self.preferences else default
