"""
Parent API Endpoints - Bridge Programme, child progress, co-op challenges
"""
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.security import decode_token, oauth2_scheme
from app.models.user import User
from app.models.parent import Parent, CoOpChallenge
from app.models.learner import Learner
from app.models.bridge import BridgeZone, BridgeProgress, KSLCard

router = APIRouter()


def get_current_parent(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)) -> Parent:
    """Get current authenticated parent."""
    payload = decode_token(token)
    if not payload:
        raise HTTPException(status_code=401, detail="Invalid token")
    
    user_id = payload.get("user_id")
    user = db.query(User).filter(User.id == user_id).first()
    
    if not user or user.role != "parent":
        raise HTTPException(status_code=403, detail="Not authorized as parent")
    
    parent = db.query(Parent).filter(Parent.user_id == user_id).first()
    if not parent:
        raise HTTPException(status_code=404, detail="Parent profile not found")
    
    return parent


@router.get("/children")
async def get_children(
    parent: Parent = Depends(get_current_parent),
    db: Session = Depends(get_db)
):
    """Get parent's children."""
    children = []
    for child_id in parent.learner_ids:
        learner = db.query(Learner).filter(Learner.user_id == child_id).first()
        if learner:
            children.append({
                "id": str(learner.user_id),
                "full_name": learner.user.full_name,
                "grade_level": learner.grade_level,
                "current_streak": learner.current_streak,
                "total_xp": learner.total_xp,
                "slo_mastery_rate": learner.total_slos_mastered / max(learner.total_lessons_completed, 1) * 100,
            })
    
    return {"children": children}


@router.get("/child/{child_id}/progress")
async def get_child_progress(
    child_id: str,
    parent: Parent = Depends(get_current_parent),
    db: Session = Depends(get_db)
):
    """Get child's progress."""
    if child_id not in [str(c) for c in parent.learner_ids]:
        raise HTTPException(status_code=403, detail="Not authorized to view this child")
    
    learner = db.query(Learner).filter(Learner.user_id == child_id).first()
    if not learner:
        raise HTTPException(status_code=404, detail="Child not found")
    
    return {
        "profile": {
            "id": str(learner.user_id),
            "full_name": learner.user.full_name,
            "grade_level": learner.grade_level,
        },
        "weekly_summary": {
            "lessons_completed": 5,  # Would calculate
            "xp_earned": 150,
            "average_score": 85,
        },
        "slo_mastery": learner.total_slos_mastered,
        "recent_activity": [],
        "upcoming_lessons": [],
    }


@router.get("/bridge/zones")
async def get_bridge_zones(
    parent: Parent = Depends(get_current_parent),
    db: Session = Depends(get_db)
):
    """Get Bridge Programme zones for parent learning."""
    zones = db.query(BridgeZone).order_by(BridgeZone.order_number).all()
    
    result = []
    for zone in zones:
        progress = db.query(BridgeProgress).filter(
            BridgeProgress.learner_id == parent.user_id,
            BridgeProgress.bridge_zone_id == zone.id
        ).first()
        
        result.append({
            "zone_level": zone.zone_level,
            "title": zone.title,
            "description": zone.description,
            "vocabulary_count": zone.vocabulary_count,
            "xp_reward": zone.xp_reward,
            "status": progress.completion_status if progress else "locked",
            "score": progress.score if progress else None,
        })
    
    return {"zones": result}


@router.get("/bridge/ksl-card/{learner_id}")
async def get_ksl_card(
    learner_id: str,
    parent: Parent = Depends(get_current_parent),
    db: Session = Depends(get_db)
):
    """Generate KSL card for deaf child."""
    learner = db.query(Learner).filter(Learner.user_id == learner_id).first()
    if not learner:
        raise HTTPException(status_code=404, detail="Learner not found")
    
    return {
        "learner_name": learner.user.full_name,
        "mastered_signs_count": 50,  # Would count from sign_mastery
        "bridge_zones_completed": len(parent.bridge_zones_completed),
        "qr_code_url": "https://signasili.org/card/12345",
        "verification_status": "verified",
    }
