"""
Learner API Endpoints - Progress, lessons, badges, practice
"""
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import func
from app.core.database import get_db
from app.core.security import decode_token, oauth2_scheme
from app.models.user import User
from app.models.learner import Learner, XPLog
from app.models.progress import LessonProgress, SLOMastery, SignMastery, StoryProgress
from app.models.content import Lesson, Zone, Quest, Sign, Story, Badge, LearnerBadge
from app.schemas.learner import (
    LearnerProfile, LearnerProfileUpdate, ProgressResponse,
    LessonDetail, LessonCompleteRequest, LessonCompleteResponse,
    StreakInfo, BadgeList, LeaderboardEntry
)

router = APIRouter()


def get_current_learner(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)) -> Learner:
    """Get current authenticated learner."""
    payload = decode_token(token)
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token"
        )
    
    user_id = payload.get("user_id")
    user = db.query(User).filter(User.id == user_id).first()
    
    if not user or user.role != "learner":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized as learner"
        )
    
    learner = db.query(Learner).filter(Learner.user_id == user_id).first()
    if not learner:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Learner profile not found"
        )
    
    return learner


@router.get("/profile", response_model=LearnerProfile)
async def get_profile(learner: Learner = Depends(get_current_learner)):
    """Get learner profile with progress stats."""
    return {
        "id": str(learner.user_id),
        "email": learner.user.email,
        "full_name": learner.user.full_name,
        "grade_level": learner.grade_level,
        "deaf_status": learner.deaf_status,
        "enrolled_at": learner.enrolled_at,
        "current_streak": learner.current_streak,
        "longest_streak": learner.longest_streak,
        "total_xp": learner.total_xp,
        "total_lessons_completed": learner.total_lessons_completed,
        "total_slos_mastered": learner.total_slos_mastered,
        "average_score": learner.average_score,
        "last_active": learner.last_active,
        "preferred_hand": learner.preferred_hand,
    }


@router.put("/profile")
async def update_profile(
    update_data: LearnerProfileUpdate,
    learner: Learner = Depends(get_current_learner),
    db: Session = Depends(get_db)
):
    """Update learner profile."""
    if update_data.full_name:
        learner.user.full_name = update_data.full_name
    if update_data.preferences:
        learner.user.preferences.update(update_data.preferences)
    if update_data.accessibility_needs:
        learner.accessibility_needs = update_data.accessibility_needs
    if update_data.preferred_hand:
        learner.preferred_hand = update_data.preferred_hand
    
    db.commit()
    return {"message": "Profile updated successfully"}


@router.get("/progress", response_model=ProgressResponse)
async def get_progress(
    learner: Learner = Depends(get_current_learner),
    db: Session = Depends(get_db)
):
    """Get comprehensive progress data."""
    # Get all zones with progress
    zones = db.query(Zone).filter(Zone.is_active == True).order_by(Zone.order_number).all()
    
    zone_progress = []
    for zone in zones:
        # Count completed quests in zone
        completed_quests = db.query(LessonProgress).join(Lesson).join(Quest).filter(
            Quest.zone_id == zone.id,
            LessonProgress.learner_id == learner.user_id,
            LessonProgress.status == "completed"
        ).count()
        
        total_quests = len(zone.quests)
        
        zone_progress.append({
            "zone_id": zone.id,
            "name": zone.name,
            "grade_level": zone.grade_level,
            "completed_quests": completed_quests,
            "total_quests": total_quests,
            "is_locked": zone.minimum_streak_required > learner.current_streak,
            "progress_percentage": (completed_quests / total_quests * 100) if total_quests > 0 else 0
        })
    
    # Calculate SLO mastery rate
    slo_count = db.query(SLOMastery).filter(SLOMastery.learner_id == learner.user_id).count()
    mastered_slos = db.query(SLOMastery).filter(
        SLOMastery.learner_id == learner.user_id,
        SLOMastery.mastery_percentage >= 80
    ).count()
    
    slo_mastery_rate = (mastered_slos / slo_count * 100) if slo_count > 0 else 0
    
    # Weekly activity
    from datetime import datetime, timedelta
    week_ago = datetime.utcnow() - timedelta(days=7)
    weekly_xp = db.query(func.sum(XPLog.xp_earned)).filter(
        XPLog.learner_id == learner.user_id,
        XPLog.timestamp >= week_ago
    ).scalar() or 0
    
    return {
        "zones": zone_progress,
        "slo_mastery_rate": round(slo_mastery_rate, 1),
        "total_lessons_completed": learner.total_lessons_completed,
        "total_xp": learner.total_xp,
        "current_streak": learner.current_streak,
        "average_score": learner.average_score,
        "weekly_activity": {
            "xp_earned": weekly_xp,
            "days_active": learner.current_streak
        }
    }


@router.get("/lessons/{lesson_id}", response_model=LessonDetail)
async def get_lesson(
    lesson_id: int,
    learner: Learner = Depends(get_current_learner),
    db: Session = Depends(get_db)
):
    """Get lesson content with learner progress."""
    lesson = db.query(Lesson).filter(Lesson.id == lesson_id).first()
    if not lesson:
        raise HTTPException(status_code=404, detail="Lesson not found")
    
    # Check if prerequisites are met
    progress = db.query(LessonProgress).filter(
        LessonProgress.learner_id == learner.user_id,
        LessonProgress.lesson_id == lesson_id
    ).first()
    
    # Get previous lesson score for adaptive difficulty
    previous_lesson = db.query(Lesson).filter(
        Lesson.quest_id == lesson.quest_id,
        Lesson.order_number < lesson.order_number
    ).order_by(Lesson.order_number.desc()).first()
    
    previous_score = None
    if previous_lesson:
        prev_progress = db.query(LessonProgress).filter(
            LessonProgress.learner_id == learner.user_id,
            LessonProgress.lesson_id == previous_lesson.id
        ).first()
        if prev_progress:
            previous_score = prev_progress.score
    
    return {
        "id": lesson.id,
        "title": lesson.title,
        "phase_number": lesson.phase_number,
        "lesson_type": lesson.lesson_type,
        "content": lesson.content_json,
        "video_url": lesson.video_url,
        "duration_seconds": lesson.duration_seconds,
        "xp_reward": lesson.xp_reward,
        "passing_score": lesson.passing_score,
        "prerequisites_met": progress is not None or lesson.phase_number == 1,
        "previous_lesson_score": previous_score,
        "status": progress.status if progress else "locked",
        "attempts": progress.attempts if progress else 0,
    }


@router.post("/lessons/{lesson_id}/complete", response_model=LessonCompleteResponse)
async def complete_lesson(
    lesson_id: int,
    completion: LessonCompleteRequest,
    learner: Learner = Depends(get_current_learner),
    db: Session = Depends(get_db)
):
    """Submit lesson completion and calculate rewards."""
    lesson = db.query(Lesson).filter(Lesson.id == lesson_id).first()
    if not lesson:
        raise HTTPException(status_code=404, detail="Lesson not found")
    
    # Get or create progress
    progress = db.query(LessonProgress).filter(
        LessonProgress.learner_id == learner.user_id,
        LessonProgress.lesson_id == lesson_id
    ).first()
    
    if not progress:
        progress = LessonProgress(
            learner_id=learner.user_id,
            lesson_id=lesson_id,
            status="in_progress",
            started_at=datetime.utcnow()
        )
        db.add(progress)
    
    # Update progress
    from datetime import datetime
    progress.status = "completed"
    progress.score = completion.score
    progress.attempts += 1
    progress.completed_at = datetime.utcnow()
    progress.time_spent_seconds = completion.time_spent_seconds
    progress.exercise_results = completion.exercise_results
    
    # Award XP
    xp_earned = lesson.xp_reward
    if completion.score >= 90:
        xp_earned = int(xp_earned * 1.5)  # Bonus for high score
    
    xp_log = XPLog(
        learner_id=learner.user_id,
        xp_earned=xp_earned,
        source="lesson_complete",
        lesson_id=lesson_id
    )
    db.add(xp_log)
    
    # Update learner stats
    learner.total_xp += xp_earned
    learner.total_lessons_completed += 1
    learner.update_streak()
    
    # Check for SLO mastery
    slo_mastered = False
    if completion.score >= 80:
        # Check if all lessons in quest are completed
        quest_lessons = db.query(Lesson).filter(Lesson.quest_id == lesson.quest_id).count()
        completed_lessons = db.query(LessonProgress).join(Lesson).filter(
            Lesson.quest_id == lesson.quest_id,
            LessonProgress.learner_id == learner.user_id,
            LessonProgress.status == "completed"
        ).count()
        
        if completed_lessons >= quest_lessons:
            slo_mastered = True
            learner.total_slos_mastered += 1
            
            # Update SLO mastery record
            slo = db.query(SLOMastery).filter(
                SLOMastery.learner_id == learner.user_id,
                SLOMastery.slo_id == lesson.quest.slo_id
            ).first()
            
            if not slo:
                slo = SLOMastery(
                    learner_id=learner.user_id,
                    slo_id=lesson.quest.slo_id,
                    mastery_percentage=100,
                    achieved_at=datetime.utcnow()
                )
                db.add(slo)
            else:
                slo.mastery_percentage = 100
                slo.achieved_at = datetime.utcnow()
    
    # Check for new badges
    new_badges = []
    badges = db.query(Badge).all()
    for badge in badges:
        # Check if already earned
        existing = db.query(LearnerBadge).filter(
            LearnerBadge.learner_id == learner.user_id,
            LearnerBadge.badge_id == badge.id
        ).first()
        
        if not existing and check_badge_eligibility(learner, badge, db):
            learner_badge = LearnerBadge(
                learner_id=learner.user_id,
                badge_id=badge.id
            )
            db.add(learner_badge)
            new_badges.append({
                "id": badge.id,
                "name": badge.name,
                "icon_url": badge.icon_url
            })
            
            # Award badge XP
            badge_xp = XPLog(
                learner_id=learner.user_id,
                xp_earned=badge.points_reward,
                source="badge_earned",
                source_id=str(badge.id)
            )
            db.add(badge_xp)
            learner.total_xp += badge.points_reward
    
    # Find next lesson
    next_lesson = db.query(Lesson).filter(
        Lesson.quest_id == lesson.quest_id,
        Lesson.order_number > lesson.order_number
    ).order_by(Lesson.order_number).first()
    
    if not next_lesson:
        # Move to next quest
        next_quest = db.query(Quest).filter(
            Quest.zone_id == lesson.quest.zone_id,
            Quest.order_number > lesson.quest.order_number
        ).order_by(Quest.order_number).first()
        
        if next_quest:
            next_lesson = db.query(Lesson).filter(
                Lesson.quest_id == next_quest.id
            ).order_by(Lesson.order_number).first()
    
    db.commit()
    
    return {
        "slo_mastered": slo_mastered,
        "xp_earned": xp_earned,
        "new_badges": new_badges,
        "next_lesson_id": next_lesson.id if next_lesson else None,
        "unlocked_quests": []  # Would calculate based on progression
    }


def check_badge_eligibility(learner: Learner, badge: Badge, db: Session) -> bool:
    """Check if learner is eligible for a badge."""
    import json
    req = badge.requirement
    
    if req.get("type") == "streak":
        return learner.current_streak >= req.get("days", 0)
    
    if req.get("type") == "zone":
        # Check if all quests in zone completed
        return False  # Simplified
    
    if req.get("type") == "signs":
        mastered = db.query(SignMastery).filter(
            SignMastery.learner_id == learner.user_id,
            SignMastery.mastered == True
        ).count()
        return mastered >= req.get("count", 0)
    
    if req.get("type") == "bridge":
        return False  # Check bridge progress
    
    return False


@router.get("/streak")
async def get_streak(learner: Learner = Depends(get_current_learner)):
    """Get current streak information."""
    from datetime import date
    
    return {
        "current_streak": learner.current_streak,
        "longest_streak": learner.longest_streak,
        "last_activity": learner.last_active.isoformat() if learner.last_active else None,
        "streak_freezes_available": 1,  # Would query from StreakFreeze table
        "today_completed": learner.last_active == date.today()
    }


@router.get("/badges", response_model=BadgeList)
async def get_badges(
    learner: Learner = Depends(get_current_learner),
    db: Session = Depends(get_db)
):
    """Get all badges with learner's progress."""
    badges = db.query(Badge).order_by(Badge.order_priority).all()
    
    earned_ids = {b.badge_id for b in learner.badges}
    
    earned = []
    in_progress = []
    locked = []
    
    for badge in badges:
        badge_data = {
            "id": badge.id,
            "name": badge.name,
            "description": badge.description,
            "icon_url": badge.icon_url,
            "category": badge.badge_category,
            "points_reward": badge.points_reward,
        }
        
        if badge.id in earned_ids:
            earned_badge = next(b for b in learner.badges if b.badge_id == badge.id)
            badge_data["earned_at"] = earned_badge.earned_at
            earned.append(badge_data)
        elif check_badge_eligibility(learner, badge, db):
            in_progress.append(badge_data)
        else:
            locked.append(badge_data)
    
    return {
        "earned": earned,
        "in_progress": in_progress,
        "locked": locked
    }


@router.get("/leaderboard")
async def get_leaderboard(
    learner: Learner = Depends(get_current_learner),
    db: Session = Depends(get_db)
):
    """Get school/class leaderboard."""
    # Get top learners by XP
    top_learners = db.query(Learner).order_by(Learner.total_xp.desc()).limit(10).all()
    
    leaderboard = []
    for i, l in enumerate(top_learners):
        leaderboard.append({
            "rank": i + 1,
            "user_id": str(l.user_id),
            "full_name": l.user.full_name,
            "total_xp": l.total_xp,
            "is_current_user": l.user_id == learner.user_id
        })
    
    # Find current user's rank
    user_rank = db.query(Learner).filter(Learner.total_xp > learner.total_xp).count() + 1
    
    return {
        "rank": user_rank,
        "points_ahead": top_learners[0].total_xp - learner.total_xp if top_learners else 0,
        "points_behind": learner.total_xp - top_learners[-1].total_xp if top_learners else 0,
        "top_10": leaderboard
    }


@router.get("/signs/practice/{sign_id}")
async def get_sign_for_practice(
    sign_id: int,
    learner: Learner = Depends(get_current_learner),
    db: Session = Depends(get_db)
):
    """Get sign with practice data and IMARA keypoints."""
    sign = db.query(Sign).filter(Sign.id == sign_id).first()
    if not sign:
        raise HTTPException(status_code=404, detail="Sign not found")
    
    # Get mastery info
    mastery = db.query(SignMastery).filter(
        SignMastery.learner_id == learner.user_id,
        SignMastery.sign_id == sign_id
    ).first()
    
    return {
        "sign": {
            "id": sign.id,
            "ksl_gloss": sign.ksl_gloss,
            "english": sign.english_translation,
            "kiswahili": sign.kiswahili_translation,
            "video_url": sign.video_url,
            "nmm_required": sign.nmm_required,
            "handshape": sign.handshape,
            "location": sign.location,
            "movement": sign.movement,
        },
        "imara_keypoints": None,  # Would be loaded from ML model
        "examples": [
            sign.example_sentence_ksl,
            sign.example_sentence_english,
            sign.example_sentence_kiswahili
        ],
        "common_mistakes": [],  # Would be populated from ML feedback data
        "mastery": {
            "recognition_score": mastery.recognition_score if mastery else 0,
            "production_score": mastery.production_score if mastery else 0,
            "practice_count": mastery.practice_count if mastery else 0,
            "mastered": mastery.mastered if mastery else False
        }
    }


@router.post("/signs/practice/{sign_id}/submit")
async def submit_sign_practice(
    sign_id: int,
    performance: dict,
    learner: Learner = Depends(get_current_learner),
    db: Session = Depends(get_db)
):
    """Submit sign practice attempt and get feedback."""
    # Get or create sign mastery record
    mastery = db.query(SignMastery).filter(
        SignMastery.learner_id == learner.user_id,
        SignMastery.sign_id == sign_id
    ).first()
    
    if not mastery:
        mastery = SignMastery(
            learner_id=learner.user_id,
            sign_id=sign_id
        )
        db.add(mastery)
    
    # Update scores
    score = performance.get("score", 0)
    mastery.update_scores(production=score)
    
    # Generate feedback based on score
    feedback = []
    if score < 50:
        feedback = ["Watch IMARA closely", "Try slower speed", "Focus on handshape"]
    elif score < 80:
        feedback = ["Good start!", "Check palm orientation", "Add facial expression"]
    else:
        feedback = ["Excellent!", "Sign recognized correctly"]
    
    db.commit()
    
    return {
        "score": score,
        "feedback": feedback,
        "improvements": performance.get("joint_scores", []),
        "next_tip": "Practice 3 more times to master this sign" if not mastery.mastered else None
    }
