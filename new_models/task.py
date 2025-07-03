from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, Float
from sqlalchemy.orm import relationship
from database import Base
from new_models.base import BaseModel
from new_models.association_tables import task_assignees

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
    parent_task_id = Column(Integer, ForeignKey("tasks.id", ondelete="SET NULL"), nullable=True)
    created_by = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    
    # 관계 정의
    project = relationship("Project", back_populates="tasks")
    milestone = relationship("Milestone", back_populates="tasks")
    
    # 하위 업무 관계
    parent_task = relationship(
        "Task",
        remote_side=[id],
        backref="subtasks"
    )
    
    # 담당자 관계 (many-to-many)
    assignees = relationship(
        "User",
        secondary=task_assignees,
        back_populates="assigned_tasks"
    )
    
    # 생성자 관계
    creator = relationship(
        "User",
        foreign_keys=[created_by],
        back_populates="created_tasks"
    )
    
    def __repr__(self):
        return f"<Task(id={self.id}, title='{self.title}')>" 