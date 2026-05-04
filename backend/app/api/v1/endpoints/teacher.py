"""
Teacher API Endpoints - Class management, student progress, interventions
"""
from typing import List, Optional
from datetime import date
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import func, desc
from app.core.database import get_db
from app.core.security import decode_token, oauth2_scheme, check_permission
from app.models.user import User
from app.models.teacher import Teacher
from app.models.learner import Learner
from app.models.progress import LessonProgress, SLOMastery
from app.models.content import Lesson, Quest, Zone

router = APIRouter()


def get_current_teacher(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)) -> Teacher:
    """Get current authenticated teacher."""
    payload = decode_token(token)
    if not payload:
        raise HTTPException(
            status_code=401,
            detail="Invalid token"
        )
    
    user_id = payload.get("user_id")
    user = db.query(User).filter(User.id == user_id).first()
    
    if not user or user.role != "teacher":
        raise HTTPException(
            status_code=403,
            detail="Not authorized as teacher"
        )
    
    teacher = db.query(Teacher).filter(Teacher.user_id == user_id).first()
    if not teacher:
        raise HTTPException(
            status_code=404,
            detail="Teacher profile not found"
        )
    
    return teacher


@router.get("/class/students")
async def get_class_students(
    grade: Optional[int] = None,
    at_risk_only: bool = False,
    teacher: Teacher = Depends(get_current_teacher),
    db: Session = Depends(get_db)
):
    """Get students in teacher's class(es)."""
    # Get learners in same school
    query = db.query(Learner).filter(Learner.school_id == teacher.school_id)
    
    if grade:
        query = query.filter(Learner.grade_level == grade)
    
    learners = query.all()
    
    students = []
    for learner in learners:
        # Check if at risk (3 consecutive lessons below 80%)
        recent_lessons = db.query(LessonProgress).filter(
            LessonProgress.learner_id == learner.user_id
        ).order_by(desc(LessonProgress.completed_at)).limit(3).all()
        
        at_risk = False
        if len(recent_lessons) >= 3:
            scores = [l.score for l in recent_lessons if l.score]
            if scores and all(s < 80 for s in scores):
                at_risk = True
        
        if at_risk_only and not at_risk:
            continue
        
        students.append({
            "id": str(learner.user_id),
            "full_name": learner.user.full_name,
            "grade_level": learner.grade_level,
            "current_streak": learner.current_streak,
            "total_xp": learner.total_xp,
            "slo_mastery_rate": learner.total_slos_mastered / max(learner.total_lessons_completed, 1) * 100,
            "last_active": learner.last_active.isoformat() if learner.last_active else None,
            "at_risk": at_risk,
        })
    
    return {"students": students, "total_count": len(students)}


@router.get("/class/slo-heatmap")
async def get_slo_heatmap(
    grade: Optional[int] = None,
    teacher: Teacher = Depends(get_current_teacher),
    db: Session = Depends(get_db)
):
    """Get SLO mastery heatmap for class."""
    # Get learners in school/grade
    query = db.query(Learner).filter(Learner.school_id == teacher.school_id)
    if grade:
        query = query.filter(Learner.grade_level == grade)
    
    learners = query.all()
    learner_ids = [l.user_id for l in learners]
    
    # Get all SLOs
    slos = db.query(Quest).join(Zone).filter(
        Zone.grade_level == (grade or 1)
    ).all()
    
    # Build heatmap data
    heatmap = []
    for slo in slos:
        slo_data = {
            "slo_id": slo.slo_id,
            "title": slo.title,
            "mastery_by_student": []
        }
        
        for learner in learners:
            mastery = db.query(SLOMastery).filter(
                SLOMastery.learner_id == learner.user_id,
                SLOMastery.slo_id == slo.slo_id
            ).first()
            
            slo_data["mastery_by_student"].append({
                "student_id": str(learner.user_id),
                "student_name": learner.user.full_name,
                "mastery_percentage": mastery.mastery_percentage if mastery else 0,
                "achieved": mastery.achieved_at if mastery else None,
            })
        
        heatmap.append(slo_data)
    
    # Calculate summary
    all_mastery = db.query(SLOMastery).filter(
        SLOMastery.learner_id.in_(learner_ids)
    ).all()
    
    avg_mastery = sum(m.mastery_percentage for m in all_mastery) / len(all_mastery) if all_mastery else 0
    
    return {
        "heatmap": heatmap,
        "summary": {
            "total_students": len(learners),
            "total_slos": len(slos),
            "average_mastery": round(avg_mastery, 1),
        }
    }


@router.get("/student/{student_id}/progress")
async def get_student_progress(
    student_id: str,
    teacher: Teacher = Depends(get_current_teacher),
    db: Session = Depends(get_db)
):
    """Get detailed progress for a specific student."""
    learner = db.query(Learner).filter(Learner.user_id == student_id).first()
    if not learner:
        raise HTTPException(status_code=404, detail="Student not found")
    
    # Verify teacher can access this student
    if learner.school_id != teacher.school_id:
        raise HTTPException(status_code=403, detail="Not authorized to view this student")
    
    # Get lesson history
    lesson_history = db.query(LessonProgress).filter(
        LessonProgress.learner_id == student_id
    ).order_by(desc(LessonProgress.completed_at)).limit(20).all()
    
    # Get SLO mastery
    slo_mastery = db.query(SLOMastery).filter(
        SLOMastery.learner_id == student_id
    ).all()
    
    # Get weak and strong signs (simplified)
    weak_signs = []
    strong_signs = []
    
    return {
        "profile": {
            "id": str(learner.user_id),
            "full_name": learner.user.full_name,
            "grade_level": learner.grade_level,
            "deaf_status": learner.deaf_status,
            "enrolled_at": learner.enrolled_at.isoformat(),
        },
        "progress_summary": {
            "total_xp": learner.total_xp,
            "current_streak": learner.current_streak,
            "lessons_completed": learner.total_lessons_completed,
            "slos_mastered": learner.total_slos_mastered,
            "average_score": learner.average_score,
        },
        "slo_mastery": [
            {
                "slo_id": m.slo_id,
                "percentage": m.mastery_percentage,
                "achieved": m.achieved_at.isoformat() if m.achieved_at else None,
            }
            for m in slo_mastery
        ],
        "lesson_history": [
            {
                "lesson_id": l.lesson_id,
                "status": l.status,
                "score": l.score,
                "completed_at": l.completed_at.isoformat() if l.completed_at else None,
                "attempts": l.attempts,
            }
            for l in lesson_history
        ],
        "weak_signs": weak_signs,
        "strong_signs": strong_signs,
    }


@router.post("/student/{student_id}/intervention")
async def create_intervention(
    student_id: str,
    intervention: dict,
    teacher: Teacher = Depends(get_current_teacher),
    db: Session = Depends(get_db)
):
    """Create an intervention for a student."""
    learner = db.query(Learner).filter(Learner.user_id == student_id).first()
    if not learner:
        raise HTTPException(status_code=404, detail="Student not found")
    
    from app.models.teacher import Intervention
    
    new_intervention = Intervention(
        teacher_id=teacher.user_id,
        learner_id=student_id,
        intervention_type=intervention.get("type"),
        notes=intervention.get("notes"),
        assigned_remedial_lesson_id=intervention.get("assigned_remedial_lesson_id"),
        follow_up_date=intervention.get("follow_up_date"),
    )
    
    db.add(new_intervention)
    db.commit()
    
    return {
        "intervention_id": new_intervention.id,
        "message": "Intervention created successfully"
    }


@router.post("/class/assign-lesson")
async def bulk_assign_lesson(
    assignment: dict,
    teacher: Teacher = Depends(get_current_teacher),
    db: Session = Depends(get_db)
):
    """Bulk assign lesson to multiple students."""
    lesson_id = assignment.get("lesson_id")
    student_ids = assignment.get("student_ids", [])
    due_date = assignment.get("due_date")
    
    # Validate lesson exists
    lesson = db.query(Lesson).filter(Lesson.id == lesson_id).first()
    if not lesson:
        raise HTTPException(status_code=404, detail="Lesson not found")
    
    assigned_count = 0
    failed_students = []
    
    for student_id in student_ids:
        learner = db.query(Learner).filter(Learner.user_id == student_id).first()
        if not learner or learner.school_id != teacher.school_id:
            failed_students.append(student_id)
            continue
        
        # Create or update lesson progress
        progress = db.query(LessonProgress).filter(
            LessonProgress.learner_id == student_id,
            LessonProgress.lesson_id == lesson_id
        ).first()
        
        if not progress:
            from datetime import datetime
            progress = LessonProgress(
                learner_id=student_id,
                lesson_id=lesson_id,
                status="unlocked",
            )
            db.add(progress)
            assigned_count += 1
    
    db.commit()
    
    return {
        "assigned_count": assigned_count,
        "failed_students": failed_students
    }


@router.get("/class/at-risk")
async def get_at_risk_students(
    teacher: Teacher = Depends(get_current_teacher),
    db: Session = Depends(get_db)
):
    """Get students at risk of falling behind."""
    learners = db.query(Learner).filter(Learner.school_id == teacher.school_id).all()
    
    at_risk = []
    for learner in learners:
        # Get last 3 lessons
        recent = db.query(LessonProgress).filter(
            LessonProgress.learner_id == learner.user_id
        ).order_by(desc(LessonProgress.completed_at)).limit(3).all()
        
        if len(recent) >= 3:
            scores = [l.score for l in recent if l.score]
            if scores and all(s < 80 for s in scores):
                at_risk.append({
                    "id": str(learner.user_id),
                    "full_name": learner.user.full_name,
                    "grade_level": learner.grade_level,
                    "recent_scores": scores,
                    "days_inactive": (date.today() - learner.last_active).days if learner.last_active else None,
                })
    
    return {
        "threshold": "3 consecutive lessons below 80%",
        "count": len(at_risk),
        "students": at_risk
    }


@router.get("/analytics/class")
async def get_class_analytics(
    teacher: Teacher = Depends(get_current_teacher),
    db: Session = Depends(get_db)
):
    """Get class analytics dashboard."""
    learners = db.query(Learner).filter(Learner.school_id == teacher.school_id).all()
    learner_ids = [l.user_id for l in learners]
    
    # Retention cohort (simplified)
    active_last_7_days = sum(1 for l in learners if l.last_active and (date.today() - l.last_active).days <= 7)
    
    # Lesson completion funnel
    total_lessons_started = db.query(LessonProgress).filter(
        LessonProgress.learner_id.in_(learner_ids)
    ).count()
    
    total_lessons_completed = db.query(LessonProgress).filter(
        LessonProgress.learner_id.in_(learner_ids),
        LessonProgress.status == "completed"
    ).count()
    
    # Sign difficulty ranking (would be from ML feedback data)
    sign_difficulty = []
    
    # Engagement heatmap (hourly activity)
    engagement = []
    
    return {
        "retention": {
            "active_last_7_days": active_last_7_days,
            "total_students": len(learners),
            "retention_rate": active_last_7_days / len(learners) * 100 if learners else 0,
        },
        "completion_funnel": {
            "started": total_lessons_started,
            "completed": total_lessons_completed,
            "completion_rate": total_lessons_completed / total_lessons_started * 100 if total_lessons_started else 0,
        },
        "sign_difficulty_ranking": sign_difficulty,
        "engagement_heatmap": engagement,
    }
