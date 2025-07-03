from typing import List, Optional
from sqlalchemy.orm import Session
from fastapi import HTTPException, status
from new_models.tech_stack import TechStack
from new_schemas.tech_stack import TechStackCreate, TechStackUpdate
from new_crud.base import CRUDBase

class CRUDTechStack(CRUDBase[TechStack, TechStackCreate, TechStackUpdate]):
    """기술 스택 모델에 대한 CRUD 작업"""
    
    def get_by_name(self, db: Session, *, name: str) -> Optional[TechStack]:
        """이름으로 기술 스택 조회"""
        return db.query(TechStack).filter(TechStack.name == name).first()
    
    def create(self, db: Session, *, obj_in: TechStackCreate) -> TechStack:
        """새 기술 스택 생성 (중복 확인)"""
        existing = self.get_by_name(db, name=obj_in.name)
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"이름이 '{obj_in.name}'인 기술 스택이 이미 존재합니다."
            )
        
        return super().create(db, obj_in=obj_in)
    
    def get_by_category(self, db: Session, *, category: str, skip: int = 0, limit: int = 100) -> List[TechStack]:
        """카테고리별 기술 스택 목록 조회"""
        return db.query(TechStack).filter(TechStack.category == category).offset(skip).limit(limit).all()
    
    def get_multi_by_names(self, db: Session, *, names: List[str]) -> List[TechStack]:
        """이름 목록으로 여러 기술 스택 조회"""
        return db.query(TechStack).filter(TechStack.name.in_(names)).all()

# CRUDTechStack 클래스 인스턴스 생성
tech_stack = CRUDTechStack(TechStack) 