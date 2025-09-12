from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, JSON
from sqlalchemy.orm import relationship
from src.core.database.database import Base
from src.api.v1.models.base import BaseModel
from src.api.v1.models.association_tables import project_members

class Project(Base, BaseModel):
    """프로젝트 모델"""
    __tablename__ = "projects"
    
    id = Column(String(6), primary_key=True)
    title = Column(String(100), nullable=False)
    description = Column(Text, nullable=True)

    # 프로젝트 상태 및 설정
    status = Column(String(20), default="planning")  # planning, in_progress, completed, on_hold
    visibility = Column(String(20), default="public")  # public, private
    
    # 프로젝트 메타데이터
    team_size = Column(Integer, nullable=False)
    project_type = Column(String, nullable=True)
    start_date = Column(DateTime, nullable=True)
    end_date = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    owner_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    
    # 추가 메타데이터
    created_at = Column(DateTime, nullable=False)
    updated_at = Column(DateTime, nullable=False)
    tags = Column(JSON, nullable=True)
    location = Column(String(255), nullable=True)
    github_url = Column(String(255), nullable=True)
    
    # 관계 정의
    owner = relationship(
        "User", 
        foreign_keys=[owner_id]
    )
    
    members = relationship(
        "User",
        secondary=project_members,
        back_populates="projects"
    )
    
    tasks = relationship(
        "Task",
        back_populates="project",
        cascade="all, delete-orphan"
    )
    
    whiteboards = relationship(
        "WhiteBoard",
        back_populates="project",
        cascade="all, delete-orphan"
    )
    
    milestones = relationship(
        "Milestone",
        back_populates="project",
        cascade="all, delete-orphan"
    )
    
    schedules = relationship(
        "Schedule",
        back_populates="project",
        cascade="all, delete-orphan"
    )
    
    # 프로젝트 참여 요청 관계
    participation_requests = relationship(
        "ParticipationRequest",
        primaryjoin="Project.id == ParticipationRequest.project_id",
        back_populates="project",
        cascade="all, delete-orphan"
    )
    
    channels = relationship(
        "Channel",
        back_populates="project",
        cascade="all, delete-orphan"
    )
    
    def __repr__(self):
        return f"<Project(id='{self.id}', title='{self.title}')>" 