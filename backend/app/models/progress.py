"""
Progress tracking models - Lesson completion, SLO mastery, streaks
"""
from datetime import datetime, date
from sqlalchemy import Column, Integer, String, Boolean, DateTime, Date, ForeignKey, JSON, Numeric
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.core.database import Base


class LessonProgress(Base):
    """Track learner progress through each lesson."""
    __tablename__ = "lesson_progress"
    
    id = Column(Integer, primary_key=True)
    learner_id = Column(UUID(as_uuid=True), ForeignKey("learners.user_id", ondelete="CASCADE"), nullable=False, index=True)
    lesson_id = Column(Integer, ForeignKey("lessons.id", ondelete="CASCADE"), nullable=False, index=True)
    
    # Progress status
    status = Column(String(50), default="locked")  # locked, unlocked, in_progress, completed, mastered
    score = Column(Integer)  # 0-100
    attempts = Column(Integer, default=0)
    
    # Timestamps
    started_at = Column(DateTime)
    completed_at = Column(DateTime)
    last_resumed_at = Column(DateTime)
    
    # Metrics
    time_spent_seconds = Column(Integer, default=0)
    exercise_results = Column(JSON, default=[])  # [{exercise_id, correct, time_taken}]
    completion_streak = Column(Integer, default=0)  # Consecutive correct answers
    
    # Relationships
    learner = relationship("Learner", back_populates="lesson_progress")
    lesson = relationship("Lesson", back_populates="progress")
    
    __table_args__ = (
        # Unique constraint to prevent duplicate progress entries
        {'sqlite_autoincrement': True},
    )
    
    def __repr__(self):
        return f"<LessonProgress {self.learner_id}:{self.lesson_id} = {self.status}>"
    
    def is_passing(self) -> bool:
        """Check if score meets passing threshold."""
        if self.score is None:
            return False
        return self.score >= 80  # Default passing score


class SLOMastery(Base):
    """Track Specific Learning Outcome mastery per learner."""
    __tablename__ = "slo_mastery"
    
    id = Column(Integer, primary_key=True)
    learner_id = Column(UUID(as_uuid=True), ForeignKey("learners.user_id", ondelete="CASCADE"), nullable=False, index=True)
    slo_id = Column(String(50), nullable=False, index=True)
    
    mastery_percentage = Column(Numeric(5, 2), default=0)  # 0-100
    achieved_at = Column(DateTime)
    retry_count = Column(Integer, default=0)
    best_score = Column(Integer, default=0)
    last_attempt = Column(DateTime)
    time_to_mastery_seconds = Column(Integer)  # How long to achieve mastery
    
    __table_args__ = (
        # Composite unique index
        {'sqlite_autoincrement': True},
    )
    
    def __repr__(self):
        return f"<SLOMastery {self.learner_id}:{self.slo_id} = {self.mastery_percentage}%>"
    
    def update_mastery(self, lesson_score: int):
        """Update mastery based on lesson score."""
        if lesson_score > self.best_score:
            self.best_score = lesson_score
        
        # Mastery is 80% or above
        if lesson_score >= 80:
            if not self.achieved_at:
                self.achieved_at = datetime.utcnow()
            self.mastery_percentage = 100
        else:
            # Calculate partial mastery
            self.mastery_percentage = min(lesson_score, 79)
        
        self.last_attempt = datetime.utcnow()
        self.retry_count += 1


class SignMastery(Base):
    """Track individual sign recognition and production mastery."""
    __tablename__ = "sign_mastery"
    
    id = Column(Integer, primary_key=True)
    learner_id = Column(UUID(as_uuid=True), ForeignKey("learners.user_id", ondelete="CASCADE"), nullable=False, index=True)
    sign_id = Column(Integer, ForeignKey("signs.id", ondelete="CASCADE"), nullable=False, index=True)
    
    recognition_score = Column(Integer, default=0)  # Understanding the sign
    production_score = Column(Integer, default=0)  # Performing the sign
    
    last_practiced = Column(DateTime)
    practice_count = Column(Integer, default=0)
    
    mastered = Column(Boolean, default=False)
    mastered_at = Column(DateTime)
    
    def __repr__(self):
        return f"<SignMastery {self.learner_id}:{self.sign_id}>"
    
    def update_scores(self, recognition: int = None, production: int = None):
        """Update scores from practice."""
        if recognition is not None:
            self.recognition_score = max(self.recognition_score, recognition)
        if production is not None:
            self.production_score = max(self.production_score, production)
        
        self.practice_count += 1
        self.last_practiced = datetime.utcnow()
        
        # Mastery requires both recognition and production >= 80
        if self.recognition_score >= 80 and self.production_score >= 80:
            self.mastered = True
            if not self.mastered_at:
                self.mastered_at = datetime.utcnow()


class StoryProgress(Base):
    """Track story comprehension progress."""
    __tablename__ = "story_progress"

    id = Column(Integer, primary_key=True)
    learner_id = Column(UUID(as_uuid=True), ForeignKey("learners.user_id", ondelete="CASCADE"), nullable=False, index=True)
    story_id = Column(Integer, ForeignKey("stories.id", ondelete="CASCADE"), nullable=False, index=True)

    completed = Column(Boolean, default=False)
    score = Column(Integer)  # Comprehension score
    completed_at = Column(DateTime)
    questions_correct = Column(Integer)
    total_questions = Column(Integer)

    def __repr__(self):
        return f"<StoryProgress {self.learner_id}:{self.story_id}>"


class Streak(Base):
    """Track learner learning streaks (consecutive days of practice)."""
    __tablename__ = "streaks"

    id = Column(Integer, primary_key=True)
    learner_id = Column(UUID(as_uuid=True), ForeignKey("learners.user_id", ondelete="CASCADE"), nullable=False, index=True, unique=True)

    current_streak = Column(Integer, default=0)  # Current consecutive days
    longest_streak = Column(Integer, default=0)  # All-time best
    last_practice_date = Column(Date)

    def __repr__(self):
        return f"<Streak learner:{self.learner_id} current:{self.current_streak}>"


class StreakFreeze(Base):
    """Track streak freeze items (protect streak when missing a day)."""
    __tablename__ = "streak_freezes"

    id = Column(Integer, primary_key=True)
    learner_id = Column(UUID(as_uuid=True), ForeignKey("learners.user_id", ondelete="CASCADE"), nullable=False, index=True)
    count = Column(Integer, default=0)  # Number of freeze items available

    def __repr__(self):
        return f"<StreakFreeze learner:{self.learner_id} count:{self.count}>"


class XPLog(Base):
    """Track XP (experience points) earned by learners."""
    __tablename__ = "xp_logs"

    id = Column(Integer, primary_key=True)
    learner_id = Column(UUID(as_uuid=True), ForeignKey("learners.user_id", ondelete="CASCADE"), nullable=False, index=True)

    total_xp = Column(Integer, default=0)
    xp_earned = Column(Integer, default=0)  # XP from this entry
    source = Column(String(50))  # lesson, sign, badge, etc.
    source_id = Column(String(100))  # ID of the source
    earned_at = Column(DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f"<XPLog learner:{self.learner_id} +{self.xp_earned} from {self.source}>"
