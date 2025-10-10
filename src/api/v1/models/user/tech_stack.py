from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy.orm import relationship
from src.core.database.database import Base
from src.api.v1.models.base import BaseModel

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