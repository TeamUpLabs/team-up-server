from sqlalchemy import Column, Integer, String, Text, ForeignKey
from sqlalchemy.orm import relationship
from src.core.database.database import Base
from src.api.v1.models.base import BaseModel
from src.api.v1.models.association_tables import schedule_assignees

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
  memo = Column(Text, nullable=True)
  
  project_id = Column(String(6), ForeignKey("projects.id", ondelete="CASCADE"), nullable=False)
  created_by = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
  updated_by = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
  
  project = relationship("Project", back_populates="schedules")
  creator = relationship("User", foreign_keys=[created_by])
  updater = relationship("User", foreign_keys=[updated_by])
  
  assignees = relationship("User", secondary=schedule_assignees)
  
  def __repr__(self):
    return f"<Schedule(id={self.id}, title='{self.title}')>"
    