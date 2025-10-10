from sqlalchemy import Column, Integer, Text, ForeignKey
from sqlalchemy.orm import relationship
from src.core.database.database import Base
from src.api.v1.models.base import BaseModel

class MentorReview(Base, BaseModel):
  """멘토 리뷰 모델"""
  __tablename__ = "mentor_reviews"
  
  id = Column(Integer, primary_key=True, index=True)
  mentor_id = Column(Integer, ForeignKey("mentors.id", ondelete="CASCADE"), nullable=False)
  user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
  
  rating = Column(Integer, nullable=False)
  comment = Column(Text, nullable=False)
  
  # 관계 정의
  mentor = relationship("Mentor", back_populates="reviews")
  user = relationship("User", back_populates="mentor_reviews")
  
  def __repr__(self):
    return f"<MentorReview(id={self.id}, mentor_id={self.mentor_id}, user_id={self.user_id})>"