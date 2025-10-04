from core.database.database import Base
from api.v1.models.base import BaseModel
from sqlalchemy import Column, Integer, String, Text, ForeignKey, JSON, DateTime
from sqlalchemy.orm import relationship

class Mentor(Base, BaseModel):
  """멘토 모델"""
  __tablename__ = "mentors"
  
  id = Column(Integer, primary_key=True, index=True)
  user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
  
  location = Column(JSON, nullable=False)
  experience = Column(Integer, nullable=False)
  topic = Column(JSON, nullable=False)
  bio = Column(Text, nullable=False)
  availablefor = Column(JSON, nullable=False)
  
  # 관계 정의
  user = relationship("User", back_populates="mentor_profiles")
  reviews = relationship("MentorReview", back_populates="mentor", cascade="all, delete-orphan")
  sessions = relationship("MentorSession", back_populates="mentor", cascade="all, delete-orphan")
  
  def __repr__(self):
    return f"<Mentor(id={self.id}, user_id={self.user_id})>"