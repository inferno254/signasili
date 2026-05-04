"""
Community models - Circles and events for deaf community
"""
from datetime import datetime, date
from sqlalchemy import Column, Integer, String, DateTime, Date, Text, ForeignKey, Numeric
from sqlalchemy.dialects.postgresql import UUID, ARRAY
from sqlalchemy.orm import relationship
from app.core.database import Base


class CommunityCircle(Base):
    """Community circles for deaf learners (schools, churches, markets)."""
    __tablename__ = "community_circles"
    
    id = Column(Integer, primary_key=True)
    name = Column(String(255), nullable=False)
    type = Column(String(50))  # school, church, mosque, market, village, online
    location = Column(String(255))
    latitude = Column(Numeric(10, 8))
    longitude = Column(Numeric(11, 8))
    
    created_by = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    created_at = Column(DateTime, default=datetime.utcnow)
    member_count = Column(Integer, default=0)
    is_active = Column(Boolean, default=True)
    
    members = relationship("CommunityCircleMember", back_populates="circle", cascade="all, delete-orphan")
    events = relationship("CommunitySignDayEvent", back_populates="circle", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<CommunityCircle {self.name} ({self.type})>"


class CommunityCircleMember(Base):
    """Members of community circles."""
    __tablename__ = "community_circle_members"
    
    circle_id = Column(Integer, ForeignKey("community_circles.id", ondelete="CASCADE"), primary_key=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), primary_key=True)
    
    role = Column(String(50), default="member")  # member, moderator, admin
    joined_at = Column(DateTime, default=datetime.utcnow)
    
    circle = relationship("CommunityCircle", back_populates="members")
    
    def __repr__(self):
        return f"<CommunityCircleMember {self.circle_id}:{self.user_id}>"


class CommunitySignDayEvent(Base):
    """Community Sign Day events for practice and socialization."""
    __tablename__ = "community_sign_day_events"
    
    id = Column(Integer, primary_key=True)
    circle_id = Column(Integer, ForeignKey("community_circles.id"), index=True)
    scheduled_date = Column(Date, nullable=False)
    theme = Column(String(255))
    vocabulary_list = Column(ARRAY(Integer), default=[])  # Sign IDs to practice
    attendee_count = Column(Integer, default=0)
    
    created_by = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    created_at = Column(DateTime, default=datetime.utcnow)
    
    circle = relationship("CommunityCircle", back_populates="events")
    
    def __repr__(self):
        return f"<CommunitySignDayEvent {self.circle_id} on {self.scheduled_date}>"
