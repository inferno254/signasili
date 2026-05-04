"""
Teacher model - For SNE teachers managing deaf learners
"""
from datetime import date
from sqlalchemy import Column, Integer, String, Boolean, Date, Text, ForeignKey, ARRAY, JSON
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.core.database import Base


class Teacher(Base):
    """Teacher profile with class management capabilities."""
    __tablename__ = "teachers"
    
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), primary_key=True)
    school_id = Column(UUID(as_uuid=True), ForeignKey("schools.id"), nullable=False, index=True)
    
    # Qualifications
    qualification_level = Column(String(100))
    years_experience = Column(Integer, default=0)
    is_ksl_certified = Column(Boolean, default=False)
    certification_level = Column(String(50))
    certification_date = Column(Date)
    
    # Class management
    classes_taught = Column(JSON, default=[])  # [{grade: 1, stream: "A", subject: "KSL"}]
    max_class_size = Column(Integer, default=30)
    subjects = Column(ARRAY(String), default=[])
    
    # Notes
    notes = Column(Text)
    
    # Relationships
    user = relationship("User", back_populates="teacher_profile")
    school = relationship("School", back_populates="teachers")
    
    def __repr__(self):
        return f"<Teacher {self.user_id} (School: {self.school_id})>"
    
    def get_class_students(self, grade: int = None):
        """Get students in teacher's classes."""
        # Would query Learner model
        pass
    
    def can_manage_student(self, student_id: UUID) -> bool:
        """Check if teacher can manage specific student."""
        # Would check if student is in teacher's class
        pass


class Intervention(Base):
    """Teacher intervention records for struggling students."""
    __tablename__ = "interventions"
    
    id = Column(Integer, primary_key=True)
    teacher_id = Column(UUID(as_uuid=True), ForeignKey("teachers.user_id"), nullable=False, index=True)
    learner_id = Column(UUID(as_uuid=True), ForeignKey("learners.user_id"), nullable=False, index=True)
    
    intervention_type = Column(String(50))  # remedial_lesson, parent_meeting, extra_practice, peer_pairing
    notes = Column(Text)
    assigned_remedial_lesson_id = Column(Integer)
    follow_up_date = Column(Date)
    
    created_at = Column(Date, default=date.today)
    completed = Column(Boolean, default=False)
    completed_at = Column(Date)
    outcome = Column(Text)
    
    def __repr__(self):
        return f"<Intervention {self.teacher_id} -> {self.learner_id}>"
