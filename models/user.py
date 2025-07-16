from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text, ForeignKey, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from database import Base
from models.base import BaseModel
from models.association_tables import (
    project_members, user_interests, user_social_links
)

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
    languages = Column(JSON, nullable=True)
    phone = Column(String(20), nullable=True)
    birth_date = Column(String(20), nullable=True)
    last_login = Column(DateTime, nullable=True)

    
    # OAuth 관련 필드
    auth_provider = Column(String(20), default="local")  # local, github, google 등
    auth_provider_id = Column(String(100), nullable=True)
    auth_provider_access_token = Column(String(255), nullable=True)
    
    # 알림 설정 (JSON 형태)
    notification_settings = Column(JSON, default={
        "emailEnable": 1,
        "taskNotification": 1,
        "milestoneNotification": 1,
        "scheduleNotification": 1,
        "deadlineNotification": 1,
        "weeklyReport": 1,
        "pushNotification": 1,
        "securityNotification": 1
    })
    
    # 관계 정의    
    projects = relationship(
        "Project",
        secondary=project_members,
        back_populates="members"
    )
    
    # 참여 요청/초대 관계
    participation_requests = relationship(
        "ParticipationRequest",
        back_populates="user"
    )
    
    # 사용자-협업 선호도 관계 (일대일)
    collaboration_preference = relationship(
        "CollaborationPreference",
        back_populates="user",
        uselist=False,
        cascade="all, delete-orphan"
    )
    
    # 사용자-기술 스택 관계 (일대다)
    tech_stacks = relationship(
        "UserTechStack",
        back_populates="user",
        cascade="all, delete-orphan"
    )
    
    # 사용자-관심분야 관계 (일대다)
    interests = relationship(
        "UserInterest",
        back_populates="user",
        cascade="all, delete-orphan"
    )
    
    # 사용자-소셜링크 관계 (일대다)
    social_links = relationship(
        "UserSocialLink",
        back_populates="user",
        cascade="all, delete-orphan"
    )
    
    # 알림 관계
    received_notifications = relationship(
        "Notification",
        back_populates="receiver",
        foreign_keys="[Notification.receiver_id]"
    )
    
    sent_notifications = relationship(
        "Notification",
        back_populates="sender",
        foreign_keys="[Notification.sender_id]"
    )
    
    def __repr__(self):
        return f"<User(id={self.id}, name='{self.name}', email='{self.email}')>" 

# 사용자 협업 선호도 모델
class CollaborationPreference(Base, BaseModel):
    """사용자 협업 선호도 모델"""
    __tablename__ = "collaboration_preferences"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, unique=True)
    collaboration_style = Column(String(50), nullable=True)  # ex. 적극적, 소극적
    preferred_project_type = Column(String(100), nullable=True)  # 웹, 모바일, AI 등 프로젝트 유형
    preferred_role = Column(String(50), nullable=True)  # 프론트엔드, 백엔드, 데이터 분석가, 디자이너, 프로젝트 매니저 등
    available_time_zone = Column(String(50), nullable=True)  # Asia/Seoul, UTC, America/New_York, America/Los_Angeles
    work_hours_start = Column(Integer, nullable=True)  # 주간 가능 시간 (시간) 0~24
    work_hours_end = Column(Integer, nullable=True)  # 주간 가능 시간 (시간) 0~24
    preferred_project_length = Column(String(20), nullable=True)  # 짧음, 중간, 김 등
    
    # 관계 정의
    user = relationship("User", back_populates="collaboration_preference")
    
    def __repr__(self):
        return f"<CollaborationPreference(id={self.id}, user_id={self.user_id}, type='{self.collaboration_style}')>"

# 사용자 기술 스택 모델
class UserTechStack(Base, BaseModel):
    """사용자 기술 스택 모델"""
    __tablename__ = "user_tech_stacks"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    tech = Column(String(100), nullable=False)
    level = Column(Integer, nullable=True)  # 숙련도 (초급: 0, 중급: 1, 고급: 2)
    
    # 관계 정의
    user = relationship("User", back_populates="tech_stacks")
    
    def __repr__(self):
        return f"<UserTechStack(id={self.id}, user_id={self.user_id}, tech={self.tech})>"

# 사용자 관심분야 모델
class UserInterest(Base, BaseModel):
    """사용자 관심분야 모델"""
    __tablename__ = "user_interests_detail"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    interest_category = Column(String(50), nullable=False)
    interest_name = Column(String(100), nullable=False)
    
    # 관계 정의
    user = relationship("User", back_populates="interests")
    
    def __repr__(self):
        return f"<UserInterest(id={self.id}, user_id={self.user_id}, name='{self.interest_name}')>"

# 사용자 소셜링크 모델
class UserSocialLink(Base, BaseModel):
    """사용자 소셜링크 모델"""
    __tablename__ = "user_social_links_detail"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    platform = Column(String(50), nullable=False)  # github, linkedin, twitter 등
    url = Column(String(255), nullable=False)
    
    # 관계 정의
    user = relationship("User", back_populates="social_links")
    
    def __repr__(self):
        return f"<UserSocialLink(id={self.id}, user_id={self.user_id}, platform='{self.platform}')>" 