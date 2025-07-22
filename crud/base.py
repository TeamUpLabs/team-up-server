from typing import Any, Dict, Generic, List, Optional, Type, TypeVar, Union
from fastapi import HTTPException, status
from pydantic import BaseModel
from sqlalchemy.orm import Session
from database import Base
from datetime import datetime

# 모델 타입 변수 정의 (SQLAlchemy 모델)
ModelType = TypeVar("ModelType", bound=Base)
# 생성 스키마 타입 변수 정의 (Pydantic 모델)
CreateSchemaType = TypeVar("CreateSchemaType", bound=BaseModel)
# 업데이트 스키마 타입 변수 정의 (Pydantic 모델)
UpdateSchemaType = TypeVar("UpdateSchemaType", bound=BaseModel)

class CRUDBase(Generic[ModelType, CreateSchemaType, UpdateSchemaType]):
    """
    CRUD 작업을 위한 기본 클래스
    
    이 클래스를 상속받아 각 모델에 대한 CRUD 클래스 구현
    """
    
    def __init__(self, model: Type[ModelType]):
        """
        CRUD 객체 초기화
        
        :param model: SQLAlchemy 모델 클래스
        """
        self.model = model
    
    def get(self, db: Session, id: Any) -> Optional[ModelType]:
        """
        ID로 항목 조회
        """
        return db.query(self.model).filter(self.model.id == id).first()
    
    def get_multi(
        self, db: Session, *, skip: int = 0, limit: int = 100
    ) -> List[ModelType]:
        """
        여러 항목 조회
        """
        return db.query(self.model).offset(skip).limit(limit).all()
    
    def create(self, db: Session, *, obj_in: CreateSchemaType) -> ModelType:
        """
        새 항목 생성
        """
        obj_in_data = obj_in.model_dump()
        db_obj = self.model(**obj_in_data)
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj
    
    def update(
        self, db: Session, *, db_obj: ModelType, obj_in: Union[UpdateSchemaType, Dict[str, Any]]
    ) -> ModelType:
        """
        항목 업데이트
        """
        obj_data = db_obj.__dict__
        if isinstance(obj_in, dict):
            update_data = obj_in
        else:
            update_data = obj_in.model_dump(exclude_unset=True)
            
        for field in obj_data:
            if field in update_data:
                setattr(db_obj, field, update_data[field])
                
        # Always update the updated_at field to current time
        if hasattr(db_obj, 'updated_at'):
            db_obj.updated_at = datetime.now()
            
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj
    
    def remove(self, db: Session, *, id: Any) -> ModelType:
        """
        항목 삭제
        """
        obj = db.query(self.model).get(id)
        if obj is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"{self.model.__name__} with ID {id} not found"
            )
        db.delete(obj)
        db.commit()
        return obj 