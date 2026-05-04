"""
Content API Endpoints - Zones, Quests, Lessons, Signs, Stories
"""
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.security import decode_token, oauth2_scheme
from app.models.content import Zone, Quest, Lesson, Sign, Story, ExerciseType
from app.models.progress import LessonProgress

router = APIRouter()


def get_optional_user(token: Optional[str] = None):
    """Get user if token provided, otherwise return None."""
    if not token:
        return None
    payload = decode_token(token)
    if not payload:
        return None
    return payload.get("user_id")


@router.get("/zones")
async def list_zones(
    grade_level: Optional[int] = None,
    token: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """List all zones with optional filtering."""
    query = db.query(Zone).filter(Zone.is_active == True)
    
    if grade_level:
        query = query.filter(Zone.grade_level == grade_level)
    
    zones = query.order_by(Zone.order_number).all()
    
    user_id = get_optional_user(token)
    
    result = []
    for zone in zones:
        zone_data = {
            "id": zone.id,
            "name": zone.name,
            "grade_level": zone.grade_level,
            "description": zone.description,
            "thumbnail_url": zone.thumbnail_url,
            "total_quests": zone.total_quests,
            "is_locked": zone.minimum_streak_required > 0,  # Simplified
        }
        
        # Add progress if user is authenticated
        if user_id:
            completed = db.query(LessonProgress).join(Lesson).join(Quest).filter(
                Quest.zone_id == zone.id,
                LessonProgress.learner_id == user_id,
                LessonProgress.status == "completed"
            ).count()
            zone_data["progress"] = {
                "completed_quests": completed,
                "percentage": (completed / zone.total_quests * 100) if zone.total_quests > 0 else 0
            }
        
        result.append(zone_data)
    
    return {"zones": result}


@router.get("/zones/{zone_id}/quests")
async def get_zone_quests(
    zone_id: int,
    token: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """Get all quests in a zone."""
    zone = db.query(Zone).filter(Zone.id == zone_id).first()
    if not zone:
        raise HTTPException(status_code=404, detail="Zone not found")
    
    user_id = get_optional_user(token)
    
    quests = []
    for quest in zone.quests:
        quest_data = {
            "id": quest.id,
            "slo_id": quest.slo_id,
            "title": quest.title,
            "description": quest.description,
            "total_lessons": quest.total_lessons,
            "is_locked": False,  # Would check prerequisites
        }
        
        if user_id:
            completed = db.query(LessonProgress).join(Lesson).filter(
                Lesson.quest_id == quest.id,
                LessonProgress.learner_id == user_id,
                LessonProgress.status == "completed"
            ).count()
            quest_data["progress"] = {
                "completed_lessons": completed,
                "percentage": (completed / quest.total_lessons * 100) if quest.total_lessons > 0 else 0
            }
        
        quests.append(quest_data)
    
    return {"zone_id": zone_id, "quests": quests}


@router.get("/quests/{quest_id}/lessons")
async def get_quest_lessons(
    quest_id: int,
    token: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """Get all lessons in a quest."""
    quest = db.query(Quest).filter(Quest.id == quest_id).first()
    if not quest:
        raise HTTPException(status_code=404, detail="Quest not found")
    
    user_id = get_optional_user(token)
    
    lessons = []
    for lesson in quest.lessons:
        lesson_data = {
            "id": lesson.id,
            "phase_number": lesson.phase_number,
            "lesson_type": lesson.lesson_type,
            "title": lesson.title,
            "xp_reward": lesson.xp_reward,
            "is_locked": lesson.phase_number > 1 and user_id is None,
        }
        
        if user_id:
            progress = db.query(LessonProgress).filter(
                LessonProgress.learner_id == user_id,
                LessonProgress.lesson_id == lesson.id
            ).first()
            lesson_data["status"] = progress.status if progress else "locked"
        
        lessons.append(lesson_data)
    
    return {"quest_id": quest_id, "lessons": lessons}


@router.get("/lessons/{lesson_id}")
async def get_lesson_content(
    lesson_id: int,
    db: Session = Depends(get_db)
):
    """Get full lesson content."""
    lesson = db.query(Lesson).filter(Lesson.id == lesson_id).first()
    if not lesson:
        raise HTTPException(status_code=404, detail="Lesson not found")
    
    return {
        "id": lesson.id,
        "phase_number": lesson.phase_number,
        "title": lesson.title,
        "content": lesson.content_json,
        "video_url": lesson.video_url,
        "duration_seconds": lesson.duration_seconds,
        "xp_reward": lesson.xp_reward,
        "passing_score": lesson.passing_score,
        "prerequisites": [],  # Would determine based on previous lessons
    }


@router.get("/signs/search")
async def search_signs(
    q: Optional[str] = None,
    category: Optional[str] = None,
    difficulty: Optional[int] = None,
    limit: int = Query(default=20, le=100),
    db: Session = Depends(get_db)
):
    """Search signs by query, category, or difficulty."""
    query = db.query(Sign)
    
    if q:
        query = query.filter(
            (Sign.ksl_gloss.ilike(f"%{q}%")) |
            (Sign.english_translation.ilike(f"%{q}%")) |
            (Sign.kiswahili_translation.ilike(f"%{q}%"))
        )
    
    if category:
        query = query.filter(Sign.sign_group == category)
    
    if difficulty:
        query = query.filter(Sign.difficulty_level == difficulty)
    
    signs = query.limit(limit).all()
    
    return {
        "signs": [
            {
                "id": s.id,
                "ksl_gloss": s.ksl_gloss,
                "english": s.english_translation,
                "kiswahili": s.kiswahili_translation,
                "video_url": s.video_url,
                "thumbnail_url": s.thumbnail_url,
                "difficulty": s.difficulty_level,
                "category": s.sign_group,
            }
            for s in signs
        ]
    }


@router.get("/signs/{sign_id}")
async def get_sign_details(sign_id: int, db: Session = Depends(get_db)):
    """Get detailed sign information."""
    sign = db.query(Sign).filter(Sign.id == sign_id).first()
    if not sign:
        raise HTTPException(status_code=404, detail="Sign not found")
    
    return {
        "id": sign.id,
        "ksl_gloss": sign.ksl_gloss,
        "translations": {
            "english": sign.english_translation,
            "kiswahili": sign.kiswahili_translation,
            "somali": sign.somali_translation,
        },
        "video_url": sign.video_url,
        "nmm_required": sign.nmm_required,
        "linguistic": {
            "handshape": sign.handshape,
            "location": sign.location,
            "movement": sign.movement,
            "orientation": sign.orientation,
            "hand_type": sign.hand_type,
        },
        "related_signs": sign.related_signs,
        "example_sentences": {
            "ksl": sign.example_sentence_ksl,
            "english": sign.example_sentence_english,
            "kiswahili": sign.example_sentence_kiswahili,
        },
    }


@router.get("/stories")
async def list_stories(
    difficulty: Optional[int] = None,
    token: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """List KSL stories."""
    query = db.query(Story).filter(Story.is_active == True)
    
    if difficulty:
        query = query.filter(Story.difficulty_level == difficulty)
    
    stories = query.order_by(Story.view_count.desc()).all()
    
    return {
        "stories": [
            {
                "id": s.id,
                "title": s.title,
                "difficulty": s.difficulty_level,
                "thumbnail_url": s.thumbnail_url,
                "duration_seconds": s.duration_seconds,
                "view_count": s.view_count,
                "is_unlocked": True,  # Would check based on progress
            }
            for s in stories
        ]
    }


@router.get("/stories/{story_id}")
async def get_story(story_id: int, db: Session = Depends(get_db)):
    """Get story with comprehension questions."""
    story = db.query(Story).filter(Story.id == story_id).first()
    if not story:
        raise HTTPException(status_code=404, detail="Story not found")
    
    # Increment view count
    story.view_count += 1
    db.commit()
    
    return {
        "id": story.id,
        "title": story.title,
        "video_url": story.video_url,
        "comprehension_questions": story.comprehension_questions,
        "vocabulary_introduced": story.vocabulary_introduced,
    }


@router.get("/categories")
async def get_sign_categories(db: Session = Depends(get_db)):
    """Get all sign categories/groups."""
    categories = db.query(Sign.sign_group).distinct().all()
    return {"categories": [c[0] for c in categories if c[0]]}


@router.get("/exercise-types")
async def get_exercise_types(db: Session = Depends(get_db)):
    """Get all available exercise types."""
    types = db.query(ExerciseType).all()
    return {
        "exercise_types": [
            {
                "id": t.id,
                "name": t.name,
                "description": t.description,
                "difficulty_multiplier": float(t.difficulty_multiplier),
            }
            for t in types
        ]
    }
