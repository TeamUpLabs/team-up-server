from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text
from sqlalchemy.orm import relationship
from database import Base
from new_models.base import BaseModel
from new_models.association_tables import project_members, task_assignees, milestone_assignees

class User(Base, BaseModel):
    """사용자 모델"""
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    email = Column(String(100), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=True)
    profile_image = Column(String(255), nullable=True)
    bio = Column(Text, nullable=True)
    role = Column(String(50), nullable=True)  # developer, designer, PM 등
    status = Column(String(20), default="active")  # active, inactive
    last_login = Column(DateTime, nullable=True)
    
    # OAuth 관련 필드
    auth_provider = Column(String(20), default="local")  # local, github, google 등
    auth_provider_id = Column(String(100), nullable=True)
    
    # 관계 정의
    owned_projects = relationship(
        "Project", 
        back_populates="owner", 
        foreign_keys="[Project.owner_id]"
    )
    
    projects = relationship(
        "Project",
        secondary=project_members,
        back_populates="members"
    )
    
    assigned_tasks = relationship(
        "Task",
        secondary=task_assignees,
        back_populates="assignees"
    )
    
    created_tasks = relationship(
        "Task",
        back_populates="creator",
        foreign_keys="[Task.created_by]"
    )
    
    assigned_milestones = relationship(
        "Milestone",
        secondary=milestone_assignees,
        back_populates="assignees"
    )
    
    created_milestones = relationship(
        "Milestone",
        back_populates="creator",
        foreign_keys="[Milestone.created_by]"
    )
    
    # 참여 요청/초대 관계
    participation_requests = relationship(
        "ParticipationRequest",
        back_populates="user"
    )
    
    # 스케줄 관계
    created_schedules = relationship(
        "Schedule",
        back_populates="creator",
        foreign_keys="[Schedule.created_by]"
    )
    
    assigned_schedules = relationship(
        "Schedule",
        secondary="schedule_assignees",
        back_populates="assignees"
    )
    
    def __repr__(self):
        return f"<User(id={self.id}, name='{self.name}', email='{self.email}')>" 