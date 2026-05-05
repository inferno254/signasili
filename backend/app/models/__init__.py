"""
SignAsili Database Models
All SQLAlchemy models for the KSL education platform
"""

from app.models.user import User
from app.models.learner import Learner
from app.models.teacher import Teacher
from app.models.parent import Parent
from app.models.school import School
from app.models.content import (
    Zone, Quest, Lesson, ExerciseType, Sign, Story,
    Badge, LearnerBadge
)
from app.models.progress import (
    LessonProgress, SLOMastery, SignMastery, StoryProgress,
    Streak, StreakFreeze, XPLog
)
from app.models.bridge import (
    BridgeZone, BridgeProgress, KSLCard, KSLCardVerification
)
from app.models.bridge_programme import (
    BridgeZone as BridgeProgrammeZone, BridgeProgress as BridgeProgrammeProgress,
    KSLCard as KSLCardDetail, KSLCardVerification as KSLCardVerify,
    ParentChildConnection, CoOpChallenge, HomeSigningGuide, BridgeAchievement
)
from app.models.emotional_learning import (
    EmotionalCompetency, SELProgress, NMMExercise, NMMProgress,
    EmotionalVocabulary, SocialScenario, ScenarioProgress
)
from app.models.safeguarding import (
    DataProtectionLog, ConsentRecord, ContentReview, IncidentReport,
    AccessibilityPreference, BiometricDataHandling, DignityCommitment,
    TeacherObservation
)
from app.models.six_phase_lesson import (
    LessonPhaseTemplate, LessonPhase, ExerciseType, LessonExercise,
    ExerciseAttempt, LessonModuleType, HabitTracking, ZoneOfProximalDevelopment
)
from app.models.community import (
    CommunityCircle, CommunityCircleMember, CommunitySignDayEvent
)
from app.models.analytics import AnalyticsEvent, AuditLog, UserFeedback

__all__ = [
    "User",
    "Learner",
    "Teacher",
    "Parent",
    "School",
    "Zone",
    "Quest",
    "Lesson",
    "ExerciseType",
    "Sign",
    "Story",
    "Badge",
    "LearnerBadge",
    "LessonProgress",
    "SLOMastery",
    "SignMastery",
    "StoryProgress",
    "Streak",
    "StreakFreeze",
    "XPLog",
    "BridgeZone",
    "BridgeProgress",
    "KSLCard",
    "KSLCardVerification",
    "BridgeProgrammeZone",
    "BridgeProgrammeProgress",
    "KSLCardDetail",
    "KSLCardVerify",
    "ParentChildConnection",
    "CoOpChallenge",
    "HomeSigningGuide",
    "BridgeAchievement",
    "EmotionalCompetency",
    "SELProgress",
    "NMMExercise",
    "NMMProgress",
    "EmotionalVocabulary",
    "SocialScenario",
    "ScenarioProgress",
    "DataProtectionLog",
    "ConsentRecord",
    "ContentReview",
    "IncidentReport",
    "AccessibilityPreference",
    "BiometricDataHandling",
    "DignityCommitment",
    "TeacherObservation",
    "LessonPhaseTemplate",
    "LessonPhase",
    "ExerciseType",
    "LessonExercise",
    "ExerciseAttempt",
    "LessonModuleType",
    "HabitTracking",
    "ZoneOfProximalDevelopment",
    "CommunityCircle",
    "CommunityCircleMember",
    "CommunitySignDayEvent",
    "AnalyticsEvent",
    "AuditLog",
    "UserFeedback",
]
