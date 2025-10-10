from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy.orm import relationship
from src.core.database.database import Base
from src.api.v1.models.base import BaseModel

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