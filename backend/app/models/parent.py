"""
Parent model - For hearing parents of deaf children
"""
from sqlalchemy import Column, Integer, String, ForeignKey, ARRAY, JSON
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.core.database import Base


class Parent(Base):
    """Parent profile with bridge programme progress."""
    __tablename__ = "parents"
    
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), primary_key=True)
    
    # Children's IDs (can have multiple deaf children)
    learner_ids = Column(ARRAY(UUID(as_uuid=True)), default=[])
    
    # Bridge programme progress
    bridge_zones_completed = Column(ARRAY(String), default=[])  # B1, B2, etc.
    bridge_xp = Column(Integer, default=0)
    co_op_challenges_completed = Column(Integer, default=0)
    
    # Preferences
    notification_preferences = Column(JSON, default={
        "email": True,
        "sms": True,
        "push": True,
        "weekly_summary": True,
        "child_milestone": True,
    })
    
    # Relationships
    user = relationship("User", back_populates="parent_profile")
    
    def __repr__(self):
        return f"<Parent {self.user_id}>"
    
    def get_children(self):
        """Get all children (learners) for this parent."""
        # Would query Learner model
        pass
    
    def is_bridge_eligible(self) -> bool:
        """Check if parent has eligible children for bridge programme."""
        return len(self.learner_ids) > 0


class CoOpChallenge(Base):
    """Cooperative challenges between parent and child."""
    __tablename__ = "co_op_challenges"
    
    id = Column(Integer, primary_key=True)
    parent_id = Column(UUID(as_uuid=True), ForeignKey("parents.user_id"), nullable=False)
    learner_id = Column(UUID(as_uuid=True), ForeignKey("learners.user_id"), nullable=False)
    
    signs = Column(ARRAY(Integer), default=[])  # Sign IDs to practice
    due_date = Column(String(10))  # YYYY-MM-DD
    
    # Completion status
    parent_completed = Column(Boolean, default=False)
    learner_completed = Column(Boolean, default=False)
    both_completed = Column(Boolean, default=False)
    
    reward = Column(String(100))
    
    def __repr__(self):
        return f"<CoOpChallenge Parent:{self.parent_id} Child:{self.learner_id}>"
    
    def check_completion(self):
        """Check if both parent and child completed."""
        if self.parent_completed and self.learner_completed:
            self.both_completed = True
        return self.both_completed
