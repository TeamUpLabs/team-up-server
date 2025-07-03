from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from database import Base
from new_models.base import BaseModel
from new_models.association_tables import schedule_assignees

class Schedule(Base, BaseModel):
    __tablename__ = "schedules"
    
    id = Column(Integer, primary_key=True, index=True)
    type = Column(String, nullable=False) # meeting, event
    title = Column(String(100), nullable=False)
    description = Column(Text, nullable=True)
    where = Column(String, nullable=False)
    link = Column(Text, nullable=True)
    start_time = Column(String, nullable=False)
    end_time = Column(String, nullable=False)
    status = Column(String, nullable=False) # not-started, in-progress, done
    created_at = Column(DateTime, nullable=False)
    updated_at = Column(DateTime, nullable=False)
    memo = Column(Text, nullable=True)
    
    project_id = Column(String(6), ForeignKey("projects.id", ondelete="CASCADE"), nullable=False)
    created_by = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    updated_by = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    
    project = relationship("Project", back_populates="schedules")
    creator = relationship("User", back_populates="created_schedules", foreign_keys=[created_by])
    updater = relationship("User", foreign_keys=[updated_by])
    
    assignees = relationship(
        "User",
        secondary=schedule_assignees,
        back_populates="assigned_schedules"
    )
    