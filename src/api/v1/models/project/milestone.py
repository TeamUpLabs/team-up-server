from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, JSON
from sqlalchemy.orm import relationship
from src.core.database.database import Base
from src.api.v1.models.base import BaseModel
from src.api.v1.models.association_tables import milestone_assignees

class Milestone(Base, BaseModel):
  """마일스톤 모델"""
  __tablename__ = "milestones"
  
  id = Column(Integer, primary_key=True, index=True)
  title = Column(String(100), nullable=False)
  description = Column(Text, nullable=True)
  
  # 상태 및 우선순위
  status = Column(String(20), default="not_started")  # not_started, in_progress, completed, on_hold
  priority = Column(String(20), default="medium")  # low, medium, high, urgent
  
  # 진행도
  progress = Column(Integer, default=0)  # 0-100%
  
  # 날짜 정보
  start_date = Column(DateTime, nullable=True)
  due_date = Column(DateTime, nullable=True)
  completed_at = Column(DateTime, nullable=True)
  
  # 외래 키
  project_id = Column(String(6), ForeignKey("projects.id", ondelete="CASCADE"), nullable=False)
  created_by = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
  
  # 메타데이터
  tags = Column(JSON, nullable=True)
  
  # 관계 정의
  project = relationship("Project", back_populates="milestones")
  
  # 업무 관계
  tasks = relationship("Task", back_populates="milestone")
  
  # 담당자 관계 (many-to-many)
  assignees = relationship("User", secondary=milestone_assignees)
  
  # 생성자 관계
  creator = relationship("User", foreign_keys=[created_by])
  
  def __repr__(self):
    return f"<Milestone(id={self.id}, title='{self.title}')>" 