"""
Bridge Programme models for SignAsili
The Bridge Learning Programme for hearing community members
"""
from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, Text, ForeignKey, JSON, Boolean
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.core.database import Base


class BridgeZone(Base):
    """Bridge Programme learning zones (B1-B6)."""
    __tablename__ = "bridge_zones"
    
    id = Column(Integer, primary_key=True)
    zone_level = Column(String(10), unique=True, nullable=False)  # B1, B2, B3, B4, B5, B6
    title = Column(String(255), nullable=False)
    title_kiswahili = Column(String(255))
    
    description = Column(Text)
    description_kiswahili = Column(Text)
    
    # Learning objectives
    learning_objectives = Column(JSON, default=[])
    
    # Prerequisites
    required_previous_zone = Column(String(10))  # Previous zone required
    
    # Content
    vocabulary_count = Column(Integer, default=20)
    xp_reward = Column(Integer, default=50)
    badge_reward = Column(String(100))
    
    # Difficulty
    estimated_hours = Column(Integer, default=5)
    difficulty_level = Column(Integer, default=1)  # 1-3
    
    # Order
    order_number = Column(Integer, nullable=False)
    
    # Media
    intro_video_url = Column(Text)
    thumbnail_url = Column(Text)


class BridgeProgress(Base):
    """Parent/Hearing learner progress through Bridge Programme."""
    __tablename__ = "bridge_progress"
    
    id = Column(Integer, primary_key=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    bridge_zone_id = Column(Integer, ForeignKey("bridge_zones.id", ondelete="CASCADE"), nullable=False, index=True)
    
    # Progress
    completion_status = Column(String(50), default="locked")  # locked, in_progress, completed, mastered
    progress_percentage = Column(Integer, default=0)
    
    # Scores
    assessment_score = Column(Integer)  # 0-100
    signs_mastered_count = Column(Integer, default=0)
    
    # Timestamps
    started_at = Column(DateTime)
    completed_at = Column(DateTime)
    last_activity_at = Column(DateTime)
    
    # Attempts
    attempts = Column(Integer, default=0)
    
    # Time tracking
    total_time_spent_minutes = Column(Integer, default=0)
    
    # Relationship to child (for parents)
    child_learner_id = Column(UUID(as_uuid=True), ForeignKey("learners.user_id"))
    
    # Weekly challenge tracking
    weekly_signs_learned = Column(JSON, default=[])  # Signs learned this week


class KSLCard(Base):
    """
    KSL proficiency card for Bridge learners.
    A shareable, publicly viewable summary of mastered signs.
    """
    __tablename__ = "ksl_cards"
    
    id = Column(Integer, primary_key=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    
    # Card content
    card_data = Column(JSON, nullable=False)  # {name, mastered_signs_count, zones_completed, date_issued}
    
    # Signs included on the card
    signs_included = Column(JSON, default=[])  # List of sign IDs
    
    # Sharing
    shareable_link = Column(String(255), unique=True, index=True)
    share_count = Column(Integer, default=0)
    last_shared_at = Column(DateTime)
    
    # Visibility
    is_public = Column(Boolean, default=True)
    expires_at = Column(DateTime)
    
    # Card design
    card_template = Column(String(50), default="standard")  # standard, colorful, minimal
    
    # Verification
    verified_at = Column(DateTime)
    verified_by = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    
    # QR code for easy sharing
    qr_code_url = Column(Text)


class KSLCardVerification(Base):
    """Verification of KSL cards by deaf community members."""
    __tablename__ = "ksl_card_verifications"
    
    id = Column(Integer, primary_key=True)
    ksl_card_id = Column(Integer, ForeignKey("ksl_cards.id", ondelete="CASCADE"), nullable=False, index=True)
    verifier_user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    
    # Verification details
    verification_type = Column(String(50))  # deaf_peer, teacher, self, community
    verification_method = Column(String(50))  # in_person, video_call, recorded
    
    # Feedback
    verification_notes = Column(Text)
    signs_verified_count = Column(Integer)
    
    # Rating
    communication_rating = Column(Integer)  # 1-5, how well they can communicate
    
    verified_at = Column(DateTime, default=datetime.utcnow)
    
    # For community building
    shared_publicly = Column(Boolean, default=False)


class ParentChildConnection(Base):
    """
    Track the connection between parent and child in Bridge Programme.
    Parent learns signs that child learned this week.
    """
    __tablename__ = "parent_child_connections"
    
    id = Column(Integer, primary_key=True)
    parent_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True)
    child_id = Column(UUID(as_uuid=True), ForeignKey("learners.user_id"), nullable=False, index=True)
    
    # Connection status
    status = Column(String(50), default="active")  # active, paused, disconnected
    
    # Weekly sync
    last_sync_at = Column(DateTime)
    signs_to_learn_this_week = Column(JSON, default=[])  # Signs child learned
    parent_learned_count = Column(Integer, default=0)
    
    # Progress
    total_shared_signs = Column(Integer, default=0)
    communication_sessions_count = Column(Integer, default=0)
    
    # Notifications
    notify_parent_on_child_progress = Column(Boolean, default=True)
    notify_child_on_parent_progress = Column(Boolean, default=True)
    
    created_at = Column(DateTime, default=datetime.utcnow)


class CoOpChallenge(Base):
    """Cooperative challenges between parent and child."""
    __tablename__ = "co_op_challenges"
    
    id = Column(Integer, primary_key=True)
    parent_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    child_id = Column(UUID(as_uuid=True), ForeignKey("learners.user_id"), nullable=False)
    
    # Challenge content
    signs = Column(JSON, default=[])  # Sign IDs to practice together
    scenario = Column(Text)  # Real-life scenario (e.g., "Practice at dinner time")
    
    # Timeline
    due_date = Column(DateTime)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Completion status
    parent_completed = Column(Boolean, default=False)
    parent_completed_at = Column(DateTime)
    
    child_completed = Column(Boolean, default=False)
    child_completed_at = Column(DateTime)
    
    both_completed = Column(Boolean, default=False)
    
    # Reward
    reward_xp = Column(Integer, default=50)
    reward_badge = Column(String(100))
    
    # Verification
    verified_by_teacher = Column(Boolean, default=False)
    teacher_notes = Column(Text)


class HomeSigningGuide(Base):
    """Printable home signing guides for families."""
    __tablename__ = "home_signing_guides"
    
    id = Column(Integer, primary_key=True)
    title = Column(String(255), nullable=False)
    
    # Content
    signs_included = Column(JSON, default=[])  # List of sign IDs
    scenarios = Column(JSON, default=[])  # Real-life scenarios
    
    # Target audience
    min_bridge_level = Column(String(10), default="B3")  # Available after completing B3
    
    # Media
    pdf_url = Column(Text)
    thumbnail_url = Column(Text)
    
    # Usage stats
    download_count = Column(Integer, default=0)
    
    # Categories
    category = Column(String(100))  # family_meals, bedtime, school_talk, etc.


class BridgeAchievement(Base):
    """Special achievements for Bridge Programme learners."""
    __tablename__ = "bridge_achievements"
    
    id = Column(Integer, primary_key=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    
    achievement_type = Column(String(100))  # first_conversation, family_signing_day, ksl_card_shared, etc.
    achievement_name = Column(String(255))
    description = Column(Text)
    
    earned_at = Column(DateTime, default=datetime.utcnow)
    xp_awarded = Column(Integer, default=25)
    
    # Context
    related_signs = Column(JSON, default=[])
    related_child_id = Column(UUID(as_uuid=True), ForeignKey("learners.user_id"))
