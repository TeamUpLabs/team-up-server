from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text, ForeignKey, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from database import Base
from new_models.base import BaseModel
from new_models.association_tables import (
    project_members, task_assignees, milestone_assignees,
    user_tech_stacks, user_collaboration_preferences,
    user_interests, user_social_links, channel_members
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
    
    created_comments = relationship(
        "Comment",
        back_populates="creator",
        foreign_keys="[Comment.created_by]"
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
    
    # 사용자-기술 스택 관계
    tech_stacks = relationship(
        "TechStack",
        secondary=user_tech_stacks,
        backref="users"
    )
    
    # 사용자-협업 선호도 관계 (일대다)
    collaboration_preferences = relationship(
        "CollaborationPreference",
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
    
    # 채널 관계
    joined_channels = relationship(
        "Channel",
        secondary="channel_members",
        back_populates="members"
    )
    
    def __repr__(self):
        return f"<User(id={self.id}, name='{self.name}', email='{self.email}')>" 

# 사용자 협업 선호도 모델
class CollaborationPreference(Base, BaseModel):
    """사용자 협업 선호도 모델"""
    __tablename__ = "collaboration_preferences"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    preference_type = Column(String(50), nullable=False)  # remote, in-person, hybrid, timezone
    preference_value = Column(String(100), nullable=False)
    
    # 관계 정의
    user = relationship("User", back_populates="collaboration_preferences")
    
    def __repr__(self):
        return f"<CollaborationPreference(id={self.id}, user_id={self.user_id}, type='{self.preference_type}')>"

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