"""
Safeguarding, Data Protection & Dignity models for SignAsili
Implements the safeguarding principles from the Foundation Framework
"""
from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, Text, ForeignKey, JSON, Boolean
from sqlalchemy.dialects.postgresql import UUID, INET
from sqlalchemy.orm import relationship
from app.core.database import Base


class DataProtectionLog(Base):
    """Audit log for data protection compliance."""
    __tablename__ = "data_protection_logs"
    
    id = Column(Integer, primary_key=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), index=True)
    
    # What happened
    action = Column(String(100), nullable=False)  # view, export, delete, etc.
    resource_type = Column(String(50))  # learner_data, progress, etc.
    resource_id = Column(String(100))
    
    # Legal basis
    legal_basis = Column(String(50))  # consent, legitimate_interest, legal_obligation
    consent_id = Column(Integer)  # Reference to consent record if applicable
    
    # Who and when
    performed_by = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    performed_at = Column(DateTime, default=datetime.utcnow)
    
    # Context
    ip_address = Column(INET)
    user_agent = Column(Text)
    reason = Column(Text)


class ConsentRecord(Base):
    """Track consent for data processing (GDPR/Kenya Data Protection Act compliance)."""
    __tablename__ = "consent_records"
    
    id = Column(Integer, primary_key=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True)
    
    # What was consented to
    consent_type = Column(String(100), nullable=False)  # data_processing, marketing, research
    consent_version = Column(String(20))  # Version of terms/privacy policy
    
    # Consent details
    granted = Column(Boolean, default=True)
    granted_at = Column(DateTime)
    revoked_at = Column(DateTime)
    
    # How consent was obtained
    method = Column(String(50))  # explicit_checkbox, parental_authority, etc.
    
    # For child accounts - parent consent
    parent_consent_id = Column(Integer, ForeignKey("consent_records.id"))
    verified_by = Column(UUID(as_uuid=True), ForeignKey("users.id"))  # Teacher/admin who verified


class ContentReview(Base):
    """Content safeguarding - reviews of lesson content before publication."""
    __tablename__ = "content_reviews"
    
    id = Column(Integer, primary_key=True)
    content_type = Column(String(50))  # lesson, story, scenario, image
    content_id = Column(Integer)
    
    # Review status
    status = Column(String(50), default="pending")  # pending, approved, rejected, needs_revision
    
    # Review dimensions
    cultural_appropriateness = Column(String(20))  # pass, fail, needs_work
    emotional_safety = Column(String(20))
    age_appropriateness = Column(String(20))
    ksl_accuracy = Column(String(20))
    
    # Reviewers
    ksl_consultant_id = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    curriculum_reviewer_id = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    
    # Review dates
    submitted_at = Column(DateTime, default=datetime.utcnow)
    reviewed_at = Column(DateTime)
    
    # Notes
    reviewer_notes = Column(Text)
    revision_requests = Column(JSON, default=[])


class IncidentReport(Base):
    """Safeguarding incident reports."""
    __tablename__ = "incident_reports"
    
    id = Column(Integer, primary_key=True)
    reporter_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    
    # Incident details
    incident_type = Column(String(100))  # bullying, inappropriate_content, safety_concern
    severity = Column(String(20))  # low, medium, high, critical
    
    # Who was involved
    affected_user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    
    # What happened
    description = Column(Text, nullable=False)
    context = Column(JSON, default={})  # Screenshots, URLs, etc.
    
    # When
    incident_date = Column(DateTime)
    reported_at = Column(DateTime, default=datetime.utcnow)
    
    # Response
    status = Column(String(50), default="reported")  # reported, investigating, resolved, closed
    assigned_to = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    resolution = Column(Text)
    resolved_at = Column(DateTime)


class AccessibilityPreference(Base):
    """Store accessibility preferences (UDL - Universal Design for Learning)."""
    __tablename__ = "accessibility_preferences"
    
    id = Column(Integer, primary_key=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, unique=True)
    
    # Multiple means of representation
    preferred_text_size = Column(Integer, default=100)  # percentage
    high_contrast_mode = Column(Boolean, default=False)
    reduce_animations = Column(Boolean, default=False)
    
    # Multiple means of action and expression
    preferred_input_method = Column(String(50), default="touch")  # touch, keyboard, switch
    extended_time_enabled = Column(Boolean, default=False)
    
    # Multiple means of engagement
    progress_visibility = Column(String(50), default="full")  # full, minimal, none
    celebration_style = Column(String(50), default="animated")  # animated, simple, none
    
    # Deaf-specific preferences
    preferred_video_speed = Column(String(20), default="1.0")  # 0.5, 0.75, 1.0, 1.25
    sign_language_variant = Column(String(50), default="standard_ksl")  # standard, mombasa, kisumu
    show_nmms_always = Column(Boolean, default=True)
    
    # Cognitive support
    reading_level = Column(String(20), default="standard")  # simple, standard, advanced
    hint_frequency = Column(String(20), default="normal")  # minimal, normal, frequent


class BiometricDataHandling(Base):
    """
    Track how biometric data (lip sync camera) is handled.
    Per safeguarding: no biometric data stored on servers, only scores.
    """
    __tablename__ = "biometric_data_handling"
    
    id = Column(Integer, primary_key=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True)
    
    # Session info
    session_id = Column(String(100), nullable=False)
    device_id = Column(String(100))
    
    # What was processed
    processing_type = Column(String(50))  # lip_sync, face_detection
    
    # Data handling confirmation
    processed_on_device = Column(Boolean, default=True)
    landmarks_transmitted = Column(Boolean, default=False)  # Should always be False
    only_score_transmitted = Column(Boolean, default=True)  # Should always be True
    
    # Consent
    consent_recorded = Column(Boolean, default=True)
    consent_id = Column(Integer, ForeignKey("consent_records.id"))
    
    # Result
    score_generated = Column(Integer)
    processed_at = Column(DateTime, default=datetime.utcnow)
    
    # Audit
    ip_address = Column(INET)


class DignityCommitment(Base):
    """
    Track commitments to deaf community dignity principles.
    Per Foundation Framework Section 14.3
    """
    __tablename__ = "dignity_commitments"
    
    id = Column(Integer, primary_key=True)
    
    # The commitment text
    commitment_text = Column(Text, nullable=False)
    commitment_category = Column(String(100))  # language, employment, content, partnership
    
    # Who made the commitment
    organization_name = Column(String(255))
    committed_by_user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    
    # When
    committed_at = Column(DateTime, default=datetime.utcnow)
    review_date = Column(DateTime)
    
    # Status
    status = Column(String(50), default="active")  # active, fulfilled, ongoing
    
    # Evidence/progress
    evidence_links = Column(JSON, default=[])
    progress_notes = Column(Text)


class TeacherObservation(Base):
    """
    Teacher observation framework for signing assessment.
    Per Foundation Framework: no signing production scored by algorithm
    """
    __tablename__ = "teacher_observations"
    
    id = Column(Integer, primary_key=True)
    learner_id = Column(UUID(as_uuid=True), ForeignKey("learners.user_id"), nullable=False, index=True)
    teacher_id = Column(UUID(as_uuid=True), ForeignKey("teachers.user_id"), nullable=False)
    
    # Observation context
    observation_date = Column(DateTime, default=datetime.utcnow)
    quest_id = Column(Integer, ForeignKey("quests.id"))
    signs_observed = Column(JSON, default=[])
    
    # Assessment dimensions (rubric-based)
    handshape_accuracy = Column(Integer)  # 1-4 scale
    location_accuracy = Column(Integer)
    movement_accuracy = Column(Integer)
    orientation_accuracy = Column(Integer)
    nmm_production = Column(Integer)
    
    # Overall
    overall_rating = Column(String(50))  # developing, proficient, mastered
    notes = Column(Text)
    
    # Evidence
    video_recording_url = Column(Text)  # If teacher recorded the observation
    
    # For data protection - consent for recording
    recording_consent_id = Column(Integer, ForeignKey("consent_records.id"))
