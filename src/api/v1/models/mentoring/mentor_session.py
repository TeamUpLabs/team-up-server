from sqlalchemy import Column, Integer, String, Text, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from core.database.database import Base
from api.v1.models.base import BaseModel

class MentorSession(Base, BaseModel):
  """멘토 세션 모델"""
  __tablename__ = "mentor_sessions"
  
  id = Column(Integer, primary_key=True, index=True)
  mentor_id = Column(Integer, ForeignKey("mentors.id", ondelete="CASCADE"), nullable=False)
  user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
  
  title = Column(String(100), nullable=False)
  description = Column(Text, nullable=False)
  
  start_date = Column(DateTime, nullable=False)
  end_date = Column(DateTime, nullable=False)
  
  # 관계 정의
  mentor = relationship("Mentor", back_populates="sessions")
  user = relationship("User", back_populates="mentor_sessions")
  
  def __repr__(self):
    return f"<MentorSession(id={self.id}, mentor_id={self.mentor_id}, user_id={self.user_id})>"