from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy.orm import relationship
from src.core.database.database import Base
from src.api.v1.models.base import BaseModel

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
  
  # 관계 정의 (using string reference to avoid circular imports)
  user = relationship("User", back_populates="collaboration_preference")
  
  def __repr__(self):
    return f"<CollaborationPreference(id={self.id}, user_id={self.user_id}, type='{self.collaboration_style}')>"