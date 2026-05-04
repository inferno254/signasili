"""
Content models - Curriculum structure and learning materials
"""
from datetime import datetime
from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text, ForeignKey, JSON, ARRAY, Numeric
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.core.database import Base


class Zone(Base):
    """Learning zone (equivalent to grade level in CBC)."""
    __tablename__ = "zones"
    
    id = Column(Integer, primary_key=True)
    name = Column(String(100), nullable=False)
    grade_level = Column(Integer)  # 1, 2, or 3
    order_number = Column(Integer, nullable=False)
    description = Column(Text)
    thumbnail_url = Column(Text)
    
    total_quests = Column(Integer, default=0)
    total_slos = Column(Integer, default=0)
    is_active = Column(Boolean, default=True)
    minimum_streak_required = Column(Integer, default=0)
    previous_zone_id = Column(Integer, ForeignKey("zones.id"))
    
    # Relationships
    quests = relationship("Quest", back_populates="zone", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<Zone {self.name} (Grade {self.grade_level})>"


class Quest(Base):
    """Quest (sub-strand/SLO) containing multiple lessons."""
    __tablename__ = "quests"
    
    id = Column(Integer, primary_key=True)
    zone_id = Column(Integer, ForeignKey("zones.id", ondelete="CASCADE"), nullable=False, index=True)
    slo_id = Column(String(50), nullable=False)  # Specific Learning Outcome ID
    title = Column(String(255), nullable=False)
    order_number = Column(Integer, nullable=False)
    description = Column(Text)
    total_lessons = Column(Integer, default=3)
    passing_score = Column(Integer, default=80)
    xp_reward = Column(Integer, default=100)
    
    zone = relationship("Zone", back_populates="quests")
    lessons = relationship("Lesson", back_populates="quest", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<Quest {self.title} (Zone {self.zone_id})>"


class Lesson(Base):
    """Individual lesson with 6-phase structure."""
    __tablename__ = "lessons"
    
    id = Column(Integer, primary_key=True)
    quest_id = Column(Integer, ForeignKey("quests.id", ondelete="CASCADE"), nullable=False, index=True)
    
    # Lesson metadata
    lesson_type = Column(String(50), nullable=False)  # standard_ksl, lip_sync, emotion, bridge, story
    phase_number = Column(Integer, nullable=False)  # 1-6
    title = Column(String(255))
    
    # Content (JSON structure with videos, exercises, etc.)
    content_json = Column(JSON, nullable=False)
    
    # Rewards
    xp_reward = Column(Integer, default=10)
    passing_score = Column(Integer, default=80)
    
    order_number = Column(Integer)
    video_url = Column(Text)
    duration_seconds = Column(Integer)
    
    # Versioning
    created_by = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    version = Column(Integer, default=1)
    is_active = Column(Boolean, default=True)
    
    quest = relationship("Quest", back_populates="lessons")
    progress = relationship("LessonProgress", back_populates="lesson", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<Lesson {self.id} (Quest {self.quest_id}, Phase {self.phase_number})>"


class ExerciseType(Base):
    """Types of exercises available in lessons."""
    __tablename__ = "exercise_types"
    
    id = Column(Integer, primary_key=True)
    name = Column(String(50), unique=True, nullable=False)
    description = Column(Text)
    template = Column(JSON)  # Exercise structure template
    difficulty_multiplier = Column(Numeric(3, 2), default=1.0)
    
    def __repr__(self):
        return f"<ExerciseType {self.name}>"


class Sign(Base):
    """KSL sign vocabulary entry."""
    __tablename__ = "signs"
    
    id = Column(Integer, primary_key=True)
    ksl_gloss = Column(String(100), nullable=False, index=True)  # KSL gloss notation
    english_translation = Column(Text)
    kiswahili_translation = Column(Text)
    somali_translation = Column(Text)  # For refugee communities
    
    # Media
    video_url = Column(Text, nullable=False)
    thumbnail_url = Column(Text)
    
    # Linguistic features
    nmm_required = Column(ARRAY(String), default=[])  # Non-manual markers
    handshape = Column(String(50))
    location = Column(String(50))
    movement = Column(String(100))
    orientation = Column(String(50))
    hand_type = Column(String(50))  # one-handed, two-handed, etc.
    difficulty_level = Column(Integer, default=1)  # 1-3
    sign_group = Column(String(50))  # greetings, family, school, etc.
    
    # Variations
    regional_variations = Column(JSON, default={})  # {nairobi: {...}, mombasa: {...}}
    frequency_rating = Column(Integer, default=50)  # 1-100 commonness
    
    # Relationships
    related_signs = Column(ARRAY(Integer), default=[])
    opposite_sign = Column(Integer, ForeignKey("signs.id"))
    
    # Examples
    example_sentence_ksl = Column(Text)
    example_sentence_english = Column(Text)
    example_sentence_kiswahili = Column(Text)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f"<Sign {self.ksl_gloss}>"


class Story(Base):
    """KSL story for comprehension practice."""
    __tablename__ = "stories"
    
    id = Column(Integer, primary_key=True)
    title = Column(String(255), nullable=False)
    description = Column(Text)
    difficulty_level = Column(Integer, default=1)
    
    video_url = Column(Text, nullable=False)
    thumbnail_url = Column(Text)
    duration_seconds = Column(Integer)
    
    comprehension_questions = Column(JSON, nullable=False)
    vocabulary_introduced = Column(ARRAY(Integer), default=[])  # Sign IDs
    
    is_active = Column(Boolean, default=True)
    created_by = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    created_at = Column(DateTime, default=datetime.utcnow)
    
    view_count = Column(Integer, default=0)
    like_count = Column(Integer, default=0)
    
    def __repr__(self):
        return f"<Story {self.title}>"


class Badge(Base):
    """Achievement badges for learners."""
    __tablename__ = "badges"
    
    id = Column(Integer, primary_key=True)
    name = Column(String(100), unique=True, nullable=False)
    description = Column(Text)
    requirement = Column(JSON, nullable=False)  # {type: "streak", days: 7}
    icon_url = Column(Text)
    badge_category = Column(String(50))  # streak, lessons, slo, bridge, social, special
    points_reward = Column(Integer, default=50)
    order_priority = Column(Integer)
    is_hidden = Column(Boolean, default=False)  # Secret badges
    
    learner_badges = relationship("LearnerBadge", back_populates="badge", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<Badge {self.name}>"


class LearnerBadge(Base):
    """Association table for learner earned badges."""
    __tablename__ = "learner_badges"
    
    learner_id = Column(UUID(as_uuid=True), ForeignKey("learners.user_id", ondelete="CASCADE"), primary_key=True)
    badge_id = Column(Integer, ForeignKey("badges.id", ondelete="CASCADE"), primary_key=True)
    earned_at = Column(DateTime, default=datetime.utcnow)
    notification_sent = Column(Boolean, default=False)
    
    learner = relationship("Learner", back_populates="badges")
    badge = relationship("Badge", back_populates="learner_badges")
    
    def __repr__(self):
        return f"<LearnerBadge {self.learner_id} - {self.badge_id}>"
