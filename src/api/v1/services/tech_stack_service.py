from typing import List, Optional
from sqlalchemy.orm import Session
from fastapi import HTTPException, status
from api.v1.models.user import UserTechStack as DBTechStack
from api.v1.schemas.tech_stack_schema import (
    TechStackCreate,
    TechStackUpdate,
    TechStack
)

class TechStackService:
    def __init__(self, db: Session):
        self.db = db

    def get_user_tech_stacks(self, user_id: int) -> List[TechStack]:
        return self.db.query(DBTechStack).filter(
            DBTechStack.user_id == user_id
        ).all()

    def get_tech_stack(self, tech_stack_id: int, user_id: int) -> TechStack:
        db_tech = self.db.query(DBTechStack).filter(
            DBTechStack.id == tech_stack_id,
            DBTechStack.user_id == user_id
        ).first()
        
        if not db_tech:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Tech stack with id {tech_stack_id} not found for user {user_id}"
            )
        return db_tech

    def create_tech_stack(
        self, user_id: int, tech_stack: TechStackCreate
    ) -> TechStack:
        db_tech = DBTechStack(
            user_id=user_id,
            **tech_stack.dict()
        )
        self.db.add(db_tech)
        self.db.commit()
        self.db.refresh(db_tech)
        return db_tech

    def update_tech_stack(
        self, tech_stack_id: int, user_id: int, tech_stack: TechStackUpdate
    ) -> TechStack:
        db_tech = self.get_tech_stack(tech_stack_id, user_id)
        
        update_data = tech_stack.dict(exclude_unset=True)
        for field, value in update_data.items():
            setattr(db_tech, field, value)
            
        self.db.commit()
        self.db.refresh(db_tech)
        return db_tech

    def delete_tech_stack(self, tech_stack_id: int, user_id: int) -> dict:
        db_tech = self.get_tech_stack(tech_stack_id, user_id)
        self.db.delete(db_tech)
        self.db.commit()
        return {"message": "Tech stack deleted successfully"}
