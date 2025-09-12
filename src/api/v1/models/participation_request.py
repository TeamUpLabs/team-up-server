from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, Text, func
from sqlalchemy.orm import relationship
from core.database.database import Base
from api.v1.models.base import BaseModel


class ParticipationRequest(Base, BaseModel):
  """프로젝트 참여 요청/초대 모델"""
  __tablename__ = "participation_requests"

  id = Column(Integer, primary_key=True, autoincrement=True)
  project_id = Column(String(6), ForeignKey('projects.id', ondelete='CASCADE'), nullable=False)
  user_id = Column(Integer, ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
  request_type = Column(String(20), nullable=False)  # 'invitation': 프로젝트에서 사용자 초대, 'request': 사용자가 참여 요청
  status = Column(String(20), nullable=False, default='pending')  # 'pending', 'accepted', 'rejected'
  message = Column(Text, nullable=True)  # 요청 또는 초대 메시지
  # created_at = Column(DateTime, nullable=False, server_default=func.now())
  processed_at = Column(DateTime, nullable=True)  # 요청이 수락/거절된 시간

  # 관계 정의
  project = relationship("Project", back_populates="participation_requests")
  user = relationship("User", back_populates="participation_requests")
  
  def __repr__(self):
    return f"<ParticipationRequest(id={self.id}, project_id='{self.project_id}', user_id={self.user_id})>"