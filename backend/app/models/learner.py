"""
Learner model - Extended profile for deaf/hard-of-hearing students
"""
from datetime import date, datetime
from sqlalchemy import Column, Integer, String, Boolean, Date, DateTime, Text, ForeignKey, ARRAY
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.core.database import Base


class Learner(Base):
    """Learner profile with learning progress and accessibility needs."""
    __tablename__ = "learners"
    
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), primary_key=True)
    
    # Academic info
    grade_level = Column(Integer)  # Grade 1-3 for CBC
    deaf_status = Column(String(50))  # deaf, hard_of_hearing, hearing, deafblind
    hearing_aid_usage = Column(Boolean, default=False)
    cochlear_implant = Column(Boolean, default=False)
    additional_needs = Column(ARRAY(String), default=[])
    enrolled_at = Column(Date, default=date.today)
    
    # Learning progress
    current_streak = Column(Integer, default=0)
    longest_streak = Column(Integer, default=0)
    total_xp = Column(Integer, default=0)
    total_lessons_completed = Column(Integer, default=0)
    total_slos_mastered = Column(Integer, default=0)
    average_score = Column(Integer, default=0)  # 0-100
    
    # Activity tracking
    last_active = Column(Date, default=date.today)
    learning_pace = Column(String(20), default="normal")  # slow, normal, fast, custom
    
    # Accessibility
    accessibility_needs = Column(ARRAY(String), default=[])
    preferred_hand = Column(String(10), default="right")  # right, left, ambidextrous
    
    # Notes
    notes = Column(Text)
    
    # Relationships
    user = relationship("User", back_populates="learner_profile")
    lesson_progress = relationship("LessonProgress", back_populates="learner", cascade="all, delete-orphan")
    slo_mastery = relationship("SLOMastery", back_populates="learner", cascade="all, delete-orphan")
    sign_mastery = relationship("SignMastery", back_populates="learner", cascade="all, delete-orphan")
    xp_logs = relationship("XPLog", back_populates="learner", cascade="all, delete-orphan")
    badges = relationship("LearnerBadge", back_populates="learner", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<Learner {self.user_id} (Grade {self.grade_level})>"
    
    def add_xp(self, amount: int, source: str, lesson_id: int = None, sign_id: int = None):
        """Add XP to learner."""
        self.total_xp += amount
        return XPLog(
            learner_id=self.user_id,
            xp_earned=amount,
            source=source,
            lesson_id=lesson_id,
            sign_id=sign_id,
        )
    
    def update_streak(self):
        """Update learning streak."""
        today = date.today()
        if self.last_active == today:
            return  # Already active today

        yesterday = today - date.resolution
        if self.last_active == yesterday:
            self.current_streak += 1
        else:
            # Streak broken
            if self.current_streak > 0:
                # Save ended streak
                pass  # Would create Streak record
            self.current_streak = 1

        if self.current_streak > self.longest_streak:
            self.longest_streak = self.current_streak

        self.last_active = today
