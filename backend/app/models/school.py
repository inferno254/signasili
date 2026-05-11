"""
School model - SNE schools and units across Kenya
"""
import uuid
from datetime import datetime
from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text, ForeignKey, ARRAY
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.core.database import Base


class School(Base):
    """School/SNE Unit information for Kenya."""
    __tablename__ = "schools"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(255), nullable=False)
    type = Column(String(50))  # special_needs_unit, deaf_school, mainstream, vocational
    registration_number = Column(String(100), unique=True)
    
    # Location (Kenyan administrative structure)
    county = Column(String(50), index=True)
    constituency = Column(String(50))
    ward = Column(String(50))
    address = Column(Text)
    
    # Contact
    phone = Column(String(20))
    email = Column(String(255))
    principal_name = Column(String(255))
    
    # Stats
    total_deaf_students = Column(Integer, default=0)
    total_teachers = Column(Integer, default=0)
    has_ksl_teachers = Column(Boolean, default=False)
    has_earc_support = Column(Boolean, default=False)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    teachers = relationship("Teacher", back_populates="school")
    
    def __repr__(self):
        return f"<School {self.name} ({self.county})>"


class EARCOfficer(Base):
    """Educational Assessment and Resource Centre officer."""
    __tablename__ = "earc_officers"
    
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), primary_key=True)
    region = Column(String(100))
    assigned_schools = Column(ARRAY(UUID(as_uuid=True)), default=[])
    assigned_learners = Column(ARRAY(UUID(as_uuid=True)), default=[])
    visit_frequency_days = Column(Integer, default=90)
    last_sync = Column(DateTime)
    
    def __repr__(self):
        return f"<EARCOfficer {self.user_id} ({self.region})>"


import uuid
