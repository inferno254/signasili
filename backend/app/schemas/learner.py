"""
Learner Pydantic Schemas
"""
from datetime import date, datetime
from typing import List, Optional, Dict, Any
from pydantic import BaseModel


class LearnerProfile(BaseModel):
    """Learner profile response."""
    id: str
    email: str
    full_name: str
    grade_level: Optional[int]
    deaf_status: Optional[str]
    enrolled_at: date
    current_streak: int
    longest_streak: int
    total_xp: int
    total_lessons_completed: int
    total_slos_mastered: int
    average_score: int
    last_active: Optional[date]
    preferred_hand: str

    class Config:
        from_attributes = True


class LearnerProfileUpdate(BaseModel):
    """Learner profile update request."""
    full_name: Optional[str] = None
    preferences: Optional[Dict[str, Any]] = None
    accessibility_needs: Optional[List[str]] = None
    preferred_hand: Optional[str] = None


class ZoneProgress(BaseModel):
    """Zone progress data."""
    zone_id: int
    name: str
    grade_level: Optional[int]
    completed_quests: int
    total_quests: int
    is_locked: bool
    progress_percentage: float


class ProgressResponse(BaseModel):
    """Comprehensive progress response."""
    zones: List[ZoneProgress]
    slo_mastery_rate: float
    total_lessons_completed: int
    total_xp: int
    current_streak: int
    average_score: int
    weekly_activity: Dict[str, Any]


class LessonDetail(BaseModel):
    """Lesson content with progress."""
    id: int
    title: Optional[str]
    phase_number: int
    lesson_type: str
    content: Dict[str, Any]
    video_url: Optional[str]
    duration_seconds: Optional[int]
    xp_reward: int
    passing_score: int
    prerequisites_met: bool
    previous_lesson_score: Optional[int]
    status: str
    attempts: int


class ExerciseResult(BaseModel):
    """Individual exercise result."""
    exercise_id: str
    correct: bool
    time_taken_seconds: int
    attempts: int


class LessonCompleteRequest(BaseModel):
    """Lesson completion submission."""
    score: int
    time_spent_seconds: int
    exercise_results: List[ExerciseResult]
    camera_data: Optional[Dict[str, Any]] = None


class BadgeInfo(BaseModel):
    """Badge information."""
    id: int
    name: str
    description: Optional[str]
    icon_url: Optional[str]
    category: str
    points_reward: int
    earned_at: Optional[datetime] = None


class LessonCompleteResponse(BaseModel):
    """Lesson completion response with rewards."""
    slo_mastered: bool
    xp_earned: int
    new_badges: List[Dict[str, Any]]
    next_lesson_id: Optional[int]
    unlocked_quests: List[int]


class StreakInfo(BaseModel):
    """Streak information."""
    current_streak: int
    longest_streak: int
    last_activity: Optional[str]
    streak_freezes_available: int
    today_completed: bool


class BadgeList(BaseModel):
    """List of badges by status."""
    earned: List[BadgeInfo]
    in_progress: List[BadgeInfo]
    locked: List[BadgeInfo]


class LeaderboardEntry(BaseModel):
    """Leaderboard entry."""
    rank: int
    user_id: str
    full_name: str
    total_xp: int
    is_current_user: bool


class LeaderboardResponse(BaseModel):
    """Leaderboard response."""
    rank: int
    points_ahead: int
    points_behind: int
    top_10: List[LeaderboardEntry]
