"""
Bridge Programme models - For hearing parents learning KSL
"""
from datetime import datetime
from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text, ForeignKey, JSON
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.core.database import Base


class BridgeZone(Base):
    """Bridge Programme learning zones (B1-B6)."""
    __tablename__ = "bridge_zones_simple"

    id = Column(Integer, primary_key=True)
    zone_level = Column(String(10), unique=True, nullable=False)  # B1, B2, B3, B4, B5, B6
    title = Column(String(255), nullable=False)
    description = Column(Text)
    required_previous = Column(String(10))  # Previous zone required
    vocabulary_count = Column(Integer, default=20)
    xp_reward = Column(Integer, default=50)
    badge_reward = Column(String(100))
    order_number = Column(Integer)
    
    def __repr__(self):
        return f"<BridgeZone {self.zone_level}: {self.title}>"


class BridgeProgress(Base):
    """Parent progress through Bridge Programme."""
    __tablename__ = "bridge_progress_simple"

    id = Column(Integer, primary_key=True)
    learner_id = Column(UUID(as_uuid=True), ForeignKey("learners.user_id", ondelete="CASCADE"), nullable=False, index=True)
    bridge_zone_id = Column(Integer, ForeignKey("bridge_zones_simple.id", ondelete="CASCADE"), nullable=False, index=True)

    completion_status = Column(String(50), default="locked")  # locked, in_progress, completed, mastered
    score = Column(Integer)
    started_at = Column(DateTime)
    completed_at = Column(DateTime)
    attempts = Column(Integer, default=0)

    def __repr__(self):
        return f"<BridgeProgress {self.learner_id}:{self.bridge_zone_id}>"


class KSLCard(Base):
    """KSL proficiency card for parents (like a certificate)."""
    __tablename__ = "ksl_cards_simple"

    id = Column(Integer, primary_key=True)
    learner_id = Column(UUID(as_uuid=True), ForeignKey("learners.user_id", ondelete="CASCADE"), nullable=False, index=True)

    # Card data
    card_data = Column(JSON, nullable=False)  # {name, mastered_signs_count, zones_completed, date_issued}

    # Sharing
    shareable_link = Column(String(255), unique=True)
    share_count = Column(Integer, default=0)
    last_shared = Column(DateTime)
    is_public = Column(Boolean, default=True)
    expires_at = Column(DateTime)

    # Verification
    verified_at = Column(DateTime)
    verified_by = Column(UUID(as_uuid=True), ForeignKey("users.id"))

    def __repr__(self):
        return f"<KSLCard {self.learner_id}>"


class KSLCardVerification(Base):
    """Verification records for KSL cards by deaf community members."""
    __tablename__ = "ksl_card_verifications_simple"

    id = Column(Integer, primary_key=True)
    ksl_card_id = Column(Integer, ForeignKey("ksl_cards_simple.id", ondelete="CASCADE"), nullable=False, index=True)
    verifier_user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)

    verification_type = Column(String(50))  # deaf_peer, teacher, self, community
    verification_notes = Column(Text)
    verified_at = Column(DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f"<KSLCardVerification Card:{self.ksl_card_id} by {self.verifier_user_id}>"
