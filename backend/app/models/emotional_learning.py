"""
Emotional & Social Learning (SEL) models for SignAsili
Based on CASEL framework adapted for deaf learners
"""
from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, Text, ForeignKey, JSON, Boolean
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.core.database import Base


class EmotionalCompetency(Base):
    """The five SEL competencies from CASEL framework."""
    __tablename__ = "emotional_competencies"
    
    id = Column(Integer, primary_key=True)
    name = Column(String(100), nullable=False)  # self_awareness, self_management, etc.
    description = Column(Text)
    grade_level = Column(Integer)  # 1, 2, or 3
    learning_objectives = Column(JSON, default=[])
    
    # Related signs for this competency
    related_signs = Column(JSON, default=[])
    
    # NMMs (Non-Manual Markers) associated with this competency
    required_nmms = Column(JSON, default=[])


class SELProgress(Base):
    """Track learner progress through SEL competencies."""
    __tablename__ = "sel_progress"
    
    id = Column(Integer, primary_key=True)
    learner_id = Column(UUID(as_uuid=True), ForeignKey("learners.user_id", ondelete="CASCADE"), nullable=False, index=True)
    competency_id = Column(Integer, ForeignKey("emotional_competencies.id"), nullable=False)
    
    # Progress tracking
    mastery_percentage = Column(Integer, default=0)  # 0-100
    status = Column(String(50), default="in_progress")  # locked, in_progress, completed
    
    # Achievement tracking
    emotions_identified = Column(Integer, default=0)
    social_scenarios_completed = Column(Integer, default=0)
    nmm_exercises_completed = Column(Integer, default=0)
    
    started_at = Column(DateTime, default=datetime.utcnow)
    completed_at = Column(DateTime)
    
    # Store specific achievements
    achievements = Column(JSON, default=[])


class NMMExercise(Base):
    """Non-Manual Markers exercises - facial expressions as grammar and emotion."""
    __tablename__ = "nmm_exercises"
    
    id = Column(Integer, primary_key=True)
    name = Column(String(100), nullable=False)
    nmm_type = Column(String(50))  # eyebrow_raise, furrowed_brow, mouth_morpheme, etc.
    grade_level = Column(Integer)
    
    # Exercise content
    video_url = Column(Text)
    description = Column(Text)
    
    # Which signs use this NMM
    related_signs = Column(JSON, default=[])
    
    # Difficulty progression
    difficulty = Column(Integer, default=1)  # 1-3
    
    # Whether this is grammar or emotional NMM
    nmm_category = Column(String(50))  # grammatical, emotional, both


class NMMProgress(Base):
    """Track learner mastery of Non-Manual Markers."""
    __tablename__ = "nmm_progress"
    
    id = Column(Integer, primary_key=True)
    learner_id = Column(UUID(as_uuid=True), ForeignKey("learners.user_id", ondelete="CASCADE"), nullable=False, index=True)
    nmm_exercise_id = Column(Integer, ForeignKey("nmm_exercises.id"), nullable=False)
    
    # Progress
    recognition_score = Column(Integer, default=0)  # Can identify the NMM
    production_score = Column(Integer, default=0)  # Can produce the NMM
    
    practice_count = Column(Integer, default=0)
    last_practiced = Column(DateTime)
    
    mastered = Column(Boolean, default=False)
    mastered_at = Column(DateTime)


class EmotionalVocabulary(Base):
    """Emotion vocabulary signs and their contexts."""
    __tablename__ = "emotional_vocabulary"
    
    id = Column(Integer, primary_key=True)
    sign_id = Column(Integer, ForeignKey("signs.id"))
    
    emotion_category = Column(String(50))  # happy, sad, angry, scared, surprised, disgusted
    intensity = Column(Integer, default=1)  # 1-3 (mild, moderate, strong)
    
    # Social scenarios where this emotion might appear
    scenario_contexts = Column(JSON, default=[])
    
    # Age-appropriateness
    grade_appropriate = Column(Integer)  # 1, 2, or 3
    
    # Related NMM
    required_nmm = Column(String(100))


class SocialScenario(Base):
    """Social scenario exercises for emotional learning."""
    __tablename__ = "social_scenarios"
    
    id = Column(Integer, primary_key=True)
    title = Column(String(255), nullable=False)
    description = Column(Text)
    
    # Scenario content
    video_url = Column(Text)
    scenario_text_ksl = Column(Text)
    scenario_text_english = Column(Text)
    
    # Target competencies
    target_competency_id = Column(Integer, ForeignKey("emotional_competencies.id"))
    
    # Resolution must be positive per safeguarding requirements
    has_positive_resolution = Column(Boolean, default=True)
    resolution_description = Column(Text)
    
    # Difficulty
    grade_level = Column(Integer)
    difficulty = Column(Integer, default=1)
    
    # Emotions involved
    emotions_involved = Column(JSON, default=[])


class ScenarioProgress(Base):
    """Track progress through social scenarios."""
    __tablename__ = "scenario_progress"
    
    id = Column(Integer, primary_key=True)
    learner_id = Column(UUID(as_uuid=True), ForeignKey("learners.user_id", ondelete="CASCADE"), nullable=False, index=True)
    scenario_id = Column(Integer, ForeignKey("social_scenarios.id"), nullable=False)
    
    completed = Column(Boolean, default=False)
    completed_at = Column(DateTime)
    
    # Reflection responses (if any)
    reflection_responses = Column(JSON, default=[])
    
    # Emotional response tracking (for research/trauma-informed practice)
    emotional_response_rating = Column(Integer)  # 1-5, optional self-report
