from sqlalchemy import Column, DateTime
from sqlalchemy.sql import func
from database import Base

class BaseModel(object):
    """모든 모델의 기본이 되는 베이스 모델 클래스"""
    
    created_at = Column(DateTime, nullable=False, server_default=func.now())
    updated_at = Column(DateTime, nullable=False, server_default=func.now(), onupdate=func.now()) 