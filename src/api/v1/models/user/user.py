from sqlalchemy import Column, Integer, String, DateTime, Text, JSON, func
from sqlalchemy.orm import relationship
from core.database.database import Base
from api.v1.models.base import BaseModel
from api.v1.models.association_tables import project_members

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
  
  # Whiteboards the user has liked
  liked_whiteboards = relationship(
    "WhiteBoard",
    secondary="user_whiteboard_likes",
    back_populates="liked_by_users"
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
  
  # 사용자-세션 관계 (일대다)
  sessions = relationship(
    "UserSession",
    back_populates="user",
    cascade="all, delete-orphan"
  )
  
  def __repr__(self):
    return f"<User(id={self.id}, name='{self.name}', email='{self.email}')>" 