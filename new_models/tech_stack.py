from sqlalchemy import Column, Integer, String
from sqlalchemy.orm import relationship
from database import Base
from new_models.base import BaseModel
from new_models.association_tables import project_tech_stacks, user_tech_stacks

class TechStack(Base, BaseModel):
    """기술 스택 모델"""
    __tablename__ = "tech_stacks"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(50), nullable=False, unique=True)
    category = Column(String(30), nullable=True)  # frontend, backend, database, devops 등
    icon_url = Column(String(255), nullable=True)
    
    # 관계 정의
    projects = relationship(
        "Project",
        secondary=project_tech_stacks,
        back_populates="tech_stacks"
    )
    
    # 사용자 관계 (user.py에서 backref로 정의됨)
    # users = relationship("User", secondary=user_tech_stacks, back_populates="tech_stacks")
    
    def __repr__(self):
        return f"<TechStack(id={self.id}, name='{self.name}')>" 