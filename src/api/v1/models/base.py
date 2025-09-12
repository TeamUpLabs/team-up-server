from sqlalchemy import Column, DateTime
from src.core.config import setting

class BaseModel(object):
    """모든 모델의 기본이 되는 베이스 모델 클래스"""
    created_at = Column(DateTime, nullable=False, server_default=setting.now())
    updated_at = Column(DateTime, nullable=False, server_default=setting.now(), onupdate=setting.now()) 