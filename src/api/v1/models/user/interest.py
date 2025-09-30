from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy.orm import relationship
from core.database.database import Base
from api.v1.models.base import BaseModel

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