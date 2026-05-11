"""
Analytics and audit models - Tracking and monitoring
"""
from datetime import datetime
from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text, ForeignKey, JSON, Numeric
from sqlalchemy.dialects.postgresql import UUID, INET
from sqlalchemy.orm import relationship
from app.core.database import Base


class AnalyticsEvent(Base):
    """Analytics event tracking for usage metrics."""
    __tablename__ = "analytics_events"
    
    id = Column(Integer, primary_key=True)
    event_type = Column(String(100), nullable=False, index=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), index=True)
    session_id = Column(UUID(as_uuid=True))
    properties = Column(JSON)  # Event-specific data
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    
    def __repr__(self):
        return f"<AnalyticsEvent {self.event_type} at {self.created_at}>"


class AuditLog(Base):
    """Audit log for security and compliance."""
    __tablename__ = "audit_log"
    
    id = Column(Integer, primary_key=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), index=True)
    action = Column(String(100), nullable=False, index=True)
    resource_type = Column(String(50))  # user, lesson, content, etc.
    resource_id = Column(String(100))
    old_value = Column(JSON)
    new_value = Column(JSON)
    ip_address = Column(INET)
    user_agent = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    
    def __repr__(self):
        return f"<AuditLog {self.action} by {self.user_id}>"


class UserFeedback(Base):
    """User feedback and bug reports."""
    __tablename__ = "user_feedback"
    
    id = Column(Integer, primary_key=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), index=True)
    feedback_type = Column(String(50))  # bug, feature_request, content_suggestion, accessibility, general
    feedback_text = Column(Text, nullable=False)
    screenshot_url = Column(Text)
    status = Column(String(50), default="pending")  # pending, reviewed, implemented, rejected, in_progress
    created_at = Column(DateTime, default=datetime.utcnow)
    resolved_at = Column(DateTime)
    resolved_by = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    
    def __repr__(self):
        return f"<UserFeedback {self.feedback_type} from {self.user_id}>"


class Assessment(Base):
    """Formal assessments and quizzes."""
    __tablename__ = "assessments"
    
    id = Column(Integer, primary_key=True)
    learner_id = Column(UUID(as_uuid=True), ForeignKey("learners.user_id", ondelete="CASCADE"), nullable=False, index=True)
    assessment_type = Column(String(50))  # lesson_challenge, zone_quiz, diagnostic, bridge_test
    results = Column(JSON, nullable=False)
    score = Column(Integer)  # 0-100
    passed_80 = Column(Boolean, default=False)
    started_at = Column(DateTime)
    completed_at = Column(DateTime)
    time_limit_seconds = Column(Integer)
    questions_answered = Column(Integer)
    questions_correct = Column(Integer)
    
    def __repr__(self):
        return f"<Assessment {self.learner_id} ({self.assessment_type}): {self.score}%>"


class MLFeedback(Base):
    """Feedback on ML predictions for model improvement."""
    __tablename__ = "ml_feedback"
    
    id = Column(Integer, primary_key=True)
    sign_id = Column(Integer, ForeignKey("signs.id", ondelete="CASCADE"), nullable=False, index=True)
    frame_data = Column(JSON)  # Keypoint data for analysis
    predicted_label = Column(String(100))
    predicted_confidence = Column(Integer)  # 0-100
    correct_label = Column(String(100))
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    
    # Device info for debugging
    device_model = Column(String(100))
    device_os_version = Column(String(50))
    lighting_condition = Column(String(50))  # bright, dim, dark
    camera_angle = Column(String(50))  # front, side, angle
    distance_cm = Column(Integer)
    
    timestamp = Column(DateTime, default=datetime.utcnow)
    is_used_for_retraining = Column(Boolean, default=False, index=True)
    
    def __repr__(self):
        return f"<MLFeedback {self.sign_id}: predicted={self.predicted_label}, correct={self.correct_label}>"


class OfflinePack(Base):
    """Offline content packs for download."""
    __tablename__ = "offline_packs"
    
    id = Column(Integer, primary_key=True)
    zone_id = Column(Integer, ForeignKey("zones.id"), nullable=False, index=True)
    version = Column(Integer, nullable=False)
    size_bytes = Column(Integer)
    download_url = Column(Text)
    checksum = Column(String(64))  # SHA256
    created_at = Column(DateTime, default=datetime.utcnow)
    is_active = Column(Boolean, default=True)
    
    def __repr__(self):
        return f"<OfflinePack Zone {self.zone_id} v{self.version}>"


class NotificationQueue(Base):
    """Queued notifications for async delivery."""
    __tablename__ = "notification_queue"
    
    id = Column(Integer, primary_key=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True)
    type = Column(String(50))  # email, sms, push, in_app
    title = Column(String(255))
    body = Column(Text)
    data = Column(JSON)  # Additional payload
    scheduled_for = Column(DateTime)
    sent_at = Column(DateTime)
    status = Column(String(50), default="pending")  # pending, sent, failed, cancelled
    retry_count = Column(Integer, default=0)
    error_message = Column(Text)
    
    def __repr__(self):
        return f"<NotificationQueue {self.type} to {self.user_id}: {self.status}>"


class Geolocation(Base):
    """Geographic data for offline pack distribution."""
    __tablename__ = "geolocation"
    
    id = Column(Integer, primary_key=True)
    county = Column(String(50), unique=True, nullable=False)
    latitude = Column(Numeric(10, 8))
    longitude = Column(Numeric(11, 8))
    offline_pack_url = Column(Text)
    network_quality = Column(String(50))  # excellent, good, fair, poor
    last_updated = Column(DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f"<Geolocation {self.county}>"


class MPesaTransaction(Base):
    """M-PESA payment transactions."""
    __tablename__ = "mpesa_transactions"
    
    id = Column(Integer, primary_key=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), index=True)
    transaction_id = Column(String(100), unique=True)
    amount = Column(Numeric(10, 2))
    status = Column(String(50), default="pending")  # pending, completed, failed, refunded
    item_type = Column(String(50))  # premium, offline_pack, etc.
    item_id = Column(Integer)
    created_at = Column(DateTime, default=datetime.utcnow)
    completed_at = Column(DateTime)
    receipt_url = Column(Text)
    
    def __repr__(self):
        return f"<MPesaTransaction {self.transaction_id}: {self.status}>"
