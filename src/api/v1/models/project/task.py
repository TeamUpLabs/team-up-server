from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, Float, Boolean
from sqlalchemy.orm import relationship
from src.core.database.database import Base
from src.api.v1.models.base import BaseModel
from src.api.v1.models.association_tables import task_assignees

class Task(Base, BaseModel):
  """업무 모델"""
  __tablename__ = "tasks"
  
  id = Column(Integer, primary_key=True, index=True)
  title = Column(String(100), nullable=False)
  description = Column(Text, nullable=True)
  
  # 업무 상태 및 우선순위
  status = Column(String(20), default="not_started")  # not_started, in_progress, completed, on_hold
  priority = Column(String(20), default="medium")  # low, medium, high, urgent
  
  # 시간 추적
  estimated_hours = Column(Float, nullable=True)
  actual_hours = Column(Float, default=0.0)
  
  # 날짜 정보
  start_date = Column(DateTime, nullable=True)
  due_date = Column(DateTime, nullable=True)
  completed_at = Column(DateTime, nullable=True)
  
  # 외래 키
  project_id = Column(String(6), ForeignKey("projects.id", ondelete="CASCADE"), nullable=False)
  milestone_id = Column(Integer, ForeignKey("milestones.id", ondelete="SET NULL"), nullable=True)
  created_by = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
  
  # 관계 정의
  project = relationship("Project", back_populates="tasks")
  milestone = relationship("Milestone", back_populates="tasks")
  subtasks = relationship("SubTask", back_populates="task", cascade="all, delete-orphan")
  comments = relationship("Comment", back_populates="task", cascade="all, delete-orphan")
  
  # 담당자 관계 (many-to-many)
  assignees = relationship("User", secondary=task_assignees)
  
  # 생성자 관계
  creator = relationship("User", foreign_keys=[created_by])
  
  def __repr__(self):
    return f"<Task(id={self.id}, title='{self.title}')>" 
    
class SubTask(Base, BaseModel):
  """하위 업무 모델"""
  __tablename__ = "sub_tasks"
  
  id = Column(Integer, primary_key=True, index=True)
  title = Column(String(100), nullable=False)
  is_completed = Column(Boolean, default=False, nullable=False)
  created_at = Column(DateTime, nullable=False)
  updated_at = Column(DateTime, nullable=False)
  
  task_id = Column(Integer, ForeignKey("tasks.id", ondelete="CASCADE"), nullable=False)
  
  task = relationship("Task", back_populates="subtasks")
  
  def __repr__(self):
    return f"<SubTask(id={self.id}, title='{self.title}')>" 
    
class Comment(Base, BaseModel):
  """댓글 모델"""
  __tablename__ = "comments"
    
  id = Column(Integer, primary_key=True, index=True)
  content = Column(Text, nullable=False)
  created_at = Column(DateTime, nullable=False)
  updated_at = Column(DateTime, nullable=False)
    
  # 외래 키
  task_id = Column(Integer, ForeignKey("tasks.id", ondelete="CASCADE"), nullable=False)
  created_by = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    
  # 관계 정의
  task = relationship("Task", back_populates="comments")
  creator = relationship("User", foreign_keys=[created_by])
    
  def __repr__(self):
    return f"<Comment(id={self.id}, content='{self.content}')>" 