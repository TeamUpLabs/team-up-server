from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, Boolean, func
from sqlalchemy.orm import relationship
from core.database.database import Base
from api.v1.models.base import BaseModel

class UserSession(Base, BaseModel):
  """사용자 세션 모델"""
  __tablename__ = "user_sessions"
  
  id = Column(Integer, primary_key=True, index=True)
  user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
  
  device_id = Column(String, nullable=False)
  session_id = Column(String, index=True)
  user_agent = Column(String)
  ip_address = Column(String)
  geo_location = Column(String, nullable=True)
  device = Column(String, nullable=True)
  device_type = Column(String, nullable=True)
  os = Column(String, nullable=True)
  browser = Column(String, nullable=True)
  last_active_at = Column(DateTime, nullable=False, server_default=func.now())
  is_current = Column(Boolean, default=True)
  
  # 관계 정의
  user = relationship("User", back_populates="sessions")
  
  def __repr__(self):
    return f"<UserSession(id={self.id}, user_id={self.user_id}, session_id='{self.session_id}')>"