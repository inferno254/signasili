"""
Six-Phase Lesson Model for SignAsili
Full specification as per Foundation Framework Section 7
"""
from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, Text, ForeignKey, JSON, Boolean, Numeric
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.core.database import Base


class LessonPhaseTemplate(Base):
    """
    Templates for the six phases of every SignAsili lesson.
    Phase 1: Warm-Up (Attunes the learner, reviews prior knowledge)
    Phase 2: Vocabulary Introduction (Introduces 3-5 new signs via IMARA)
    Phase 3: Practice (Multiple exercise types, receptive then productive)
    Phase 4: Challenge (Application in new context, meaningful choice)
    Phase 5: Story Mode (Extended comprehensible input)
    Phase 6: Cool Down (Celebration, progress, preview)
    """
    __tablename__ = "lesson_phase_templates"
    
    id = Column(Integer, primary_key=True)
    phase_number = Column(Integer, nullable=False)  # 1-6
    phase_name = Column(String(100), nullable=False)
    
    # Phase description
    description = Column(Text)
    learning_objective = Column(Text)
    
    # Duration guidance (minutes)
    min_duration_minutes = Column(Numeric(3, 1), default=0.5)
    max_duration_minutes = Column(Numeric(3, 1), default=2.0)
    
    # Component requirements
    required_components = Column(JSON, default=[])
    optional_components = Column(JSON, default=[])
    
    # UI/UX specifications
    imara_expression = Column(String(50))  # e.g., "welcoming", "explaining", "celebrating"
    background_theme = Column(String(50))  # visual theme for this phase
    
    # Audio policy (per trauma-informed practice)
    has_background_music = Column(Boolean, default=False)
    music_style = Column(String(50))  # If music is used
    
    # Accessibility
    supports_extended_time = Column(Boolean, default=True)
    hint_availability = Column(String(50), default="always")  # always, on_request, none


class LessonPhase(Base):
    """
    Actual lesson phase instances - specific content for a lesson.
    """
    __tablename__ = "lesson_phases"
    
    id = Column(Integer, primary_key=True)
    lesson_id = Column(Integer, ForeignKey("lessons.id", ondelete="CASCADE"), nullable=False, index=True)
    phase_template_id = Column(Integer, ForeignKey("lesson_phase_templates.id"), nullable=False)
    
    # Phase number (1-6)
    phase_number = Column(Integer, nullable=False)
    
    # Content
    title = Column(String(255))
    instructions_ksl = Column(Text)  # KSL gloss instructions
    instructions_english = Column(Text)
    instructions_kiswahili = Column(Text)
    
    # Media
    imara_video_url = Column(Text)  # IMARA demonstration
    background_video_url = Column(Text)
    
    # Interactive content
    exercise_data = Column(JSON, default={})  # Exercise configuration
    story_content = Column(JSON, default={})  # For Phase 5 Story Mode
    
    # Phase 6 specific - celebration
    celebration_type = Column(String(50))  # star_reveal, zone_complete, streak_milestone
    xp_awarded = Column(Integer, default=0)
    
    # Order within phase (for multi-part phases)
    sequence_order = Column(Integer, default=1)
    
    # Duration tracking
    expected_duration_seconds = Column(Integer)


class ExerciseType(Base):
    """
    Exercise types used in Phase 3 (Practice) and Phase 4 (Challenge).
    Per Foundation Framework: multiple exercise types for different learning objectives.
    """
    __tablename__ = "exercise_types"
    
    id = Column(Integer, primary_key=True)
    
    # Basic info
    name = Column(String(100), unique=True, nullable=False)
    code = Column(String(50), unique=True, nullable=False)  # e.g., "receptive_choice", "production_camera"
    
    # Description
    description = Column(Text)
    pedagogical_purpose = Column(Text)
    
    # Template configuration
    template_schema = Column(JSON, default={})  # JSON schema for exercise data
    
    # Difficulty multipliers
    base_difficulty = Column(Numeric(3, 2), default=1.0)
    
    # UI configuration
    ui_component = Column(String(100))  # React component name
    requires_camera = Column(Boolean, default=False)
    requires_audio = Column(Boolean, default=False)  # Should always be False per UDL
    
    # Feedback configuration
    correct_feedback_type = Column(String(50), default="celebration")  # celebration, simple, none
    incorrect_feedback_type = Column(String(50), default="gentle_hint")  # gentle_hint, explanation, retry
    
    # Hints
    supports_hints = Column(Boolean, default=True)
    hint_type = Column(String(50))  # imara_thinking, visual_clue, text_hint


class LessonExercise(Base):
    """
    Individual exercises within lesson phases.
    Per design principle: max 5 new signs per lesson, 3+ exposures per sign.
    """
    __tablename__ = "lesson_exercises"
    
    id = Column(Integer, primary_key=True)
    lesson_phase_id = Column(Integer, ForeignKey("lesson_phases.id", ondelete="CASCADE"), nullable=False, index=True)
    exercise_type_id = Column(Integer, ForeignKey("exercise_types.id"), nullable=False)
    
    # Content
    title = Column(String(255))
    instructions = Column(Text)
    
    # Question/Answer data
    question_data = Column(JSON, nullable=False)  # Exercise-specific data
    correct_answer = Column(JSON, nullable=False)
    distractors = Column(JSON, default=[])  # Wrong answers for multiple choice
    
    # Signs involved
    target_signs = Column(JSON, default=[])  # Signs this exercise teaches/practices
    prerequisite_signs = Column(JSON, default=[])  # Signs learner should already know
    
    # Difficulty
    difficulty_level = Column(Integer, default=1)  # 1-3
    points_value = Column(Integer, default=10)
    
    # Hints
    hint_data = Column(JSON, default={})
    imara_hint_video_url = Column(Text)
    
    # Order
    sequence_order = Column(Integer, default=1)
    
    # Time limit (None per trauma-informed practice, but track time)
    expected_time_seconds = Column(Integer)


class ExerciseAttempt(Base):
    """
    Track learner attempts at exercises.
    Per trauma-informed practice: wrong answers are "data, not failures"
    """
    __tablename__ = "exercise_attempts"
    
    id = Column(Integer, primary_key=True)
    learner_id = Column(UUID(as_uuid=True), ForeignKey("learners.user_id", ondelete="CASCADE"), nullable=False, index=True)
    exercise_id = Column(Integer, ForeignKey("lesson_exercises.id", ondelete="CASCADE"), nullable=False)
    
    # Attempt details
    attempted_at = Column(DateTime, default=datetime.utcnow)
    
    # Response
    response_data = Column(JSON)
    is_correct = Column(Boolean)
    
    # Time taken (no pressure, just tracking)
    time_taken_seconds = Column(Integer)
    
    # Hints used
    hints_used = Column(Integer, default=0)
    hint_data_shown = Column(JSON, default=[])
    
    # Scoring
    points_earned = Column(Integer, default=0)
    xp_earned = Column(Integer, default=0)
    
    # Feedback given
    feedback_type = Column(String(50))  # celebration, gentle_correction, encouragement
    imara_response = Column(String(50))  # Which IMARA animation was shown
    
    # Learning analytics
    learning_moment = Column(Boolean, default=False)  # Flag if this was a significant learning moment
    notes = Column(Text)  # For qualitative feedback


class LessonModuleType(Base):
    """
    Five module types per Foundation Framework Section 6.3:
    1. Standard KSL Vocabulary Module
    2. Lip Sync & Mouth Morpheme Module
    3. Emotional Awareness Module
    4. Bridge Mode (Hearing Parents)
    5. Story Mode Module
    """
    __tablename__ = "lesson_module_types"
    
    id = Column(Integer, primary_key=True)
    
    code = Column(String(50), unique=True, nullable=False)
    name = Column(String(100), nullable=False)
    description = Column(Text)
    
    # Pedagogical focus
    learning_focus = Column(String(100))  # vocabulary, grammar, emotion, inclusion, narrative
    
    # Grade level appropriateness
    min_grade = Column(Integer, default=1)
    max_grade = Column(Integer, default=3)
    
    # Special features
    uses_camera = Column(Boolean, default=False)
    uses_lip_sync_scoring = Column(Boolean, default=False)
    is_narrative_based = Column(Boolean, default=False)
    is_community_focused = Column(Boolean, default=False)
    
    # Phase configuration
    phase_variations = Column(JSON, default={})  # How phases differ for this module type


class HabitTracking(Base):
    """
    Habit formation tracking based on Atomic Habits & Tiny Habits research.
    Per Foundation Framework Section 3.4
    """
    __tablename__ = "habit_tracking"
    
    id = Column(Integer, primary_key=True)
    learner_id = Column(UUID(as_uuid=True), ForeignKey("learners.user_id", ondelete="CASCADE"), nullable=False, index=True)
    
    # Habit type
    habit_type = Column(String(100), nullable=False)  # daily_lesson, streak_maintenance, review_practice
    
    # Atomic Habits principles
    cue_obvious = Column(Boolean, default=True)  # Home screen shows clear next action
    craving_attractive = Column(Integer)  # IMARA celebration appeal rating
    response_easy = Column(Boolean, default=True)  # 4-8 minute lessons
    reward_satisfying = Column(Integer)  # SLO mastery badge satisfaction
    
    # Tiny Habits tracking
    tiny_habit_anchor = Column(String(255))  # "After I eat breakfast, I will..."
    tiny_habit_behavior = Column(String(255))  # "...do one SignAsili lesson"
    tiny_habit_celebration = Column(String(255))  # "...and celebrate with IMARA"
    
    # Tracking
    current_streak = Column(Integer, default=0)
    longest_streak = Column(Integer, default=0)
    total_completions = Column(Integer, default=0)
    
    # Habit strength (0-100)
    habit_strength_score = Column(Integer, default=0)
    
    # Last activity
    last_completed_at = Column(DateTime)
    last_cue_encountered_at = Column(DateTime)


class ZoneOfProximalDevelopment(Base):
    """
    Track learner's ZPD (Vygotsky) for adaptive difficulty.
    Per Foundation Framework Section 5.4
    """
    __tablename__ = "zpd_tracking"
    
    id = Column(Integer, primary_key=True)
    learner_id = Column(UUID(as_uuid=True), ForeignKey("learners.user_id", ondelete="CASCADE"), nullable=False, index=True)
    
    # Current ZPD boundaries
    lower_bound_difficulty = Column(Integer, default=1)  # Too easy (boring)
    optimal_difficulty = Column(Integer, default=2)  # Just right (ZPD)
    upper_bound_difficulty = Column(Integer, default=3)  # Too hard (frustrating)
    
    # Calibration data
    recent_success_rate = Column(Numeric(5, 2), default=0.0)  # 0-100%
    recent_attempts_count = Column(Integer, default=0)
    
    # Adaptive recommendations
    recommended_lesson_difficulty = Column(Integer, default=2)
    recommended_hint_frequency = Column(String(20), default="normal")
    recommended_pace = Column(String(20), default="normal")  # slow, normal, fast
    
    # Last updated
    calculated_at = Column(DateTime, default=datetime.utcnow)
    
    # Recalibration trigger
    recalibrate_after_attempts = Column(Integer, default=10)
