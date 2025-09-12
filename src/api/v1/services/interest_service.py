from typing import List, Optional
from sqlalchemy.orm import Session
from fastapi import HTTPException, status
from api.v1.models.user import UserInterest as DBInterest
from api.v1.schemas.interest_schema import (
    InterestCreate,
    InterestUpdate,
    Interest
)

class InterestService:
    def __init__(self, db: Session):
        self.db = db

    def get_user_interests(self, user_id: int) -> List[Interest]:
        return self.db.query(DBInterest).filter(
            DBInterest.user_id == user_id
        ).all()

    def get_interest(self, interest_id: int, user_id: int) -> Interest:
        db_interest = self.db.query(DBInterest).filter(
            DBInterest.id == interest_id,
            DBInterest.user_id == user_id
        ).first()
        
        if not db_interest:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Interest with id {interest_id} not found for user {user_id}"
            )
        return db_interest

    def create_interest(
        self, user_id: int, interest: InterestCreate
    ) -> Interest:
        db_interest = DBInterest(
            user_id=user_id,
            **interest.dict()
        )
        self.db.add(db_interest)
        self.db.commit()
        self.db.refresh(db_interest)
        return db_interest

    def update_interest(
        self, interest_id: int, user_id: int, interest: InterestUpdate
    ) -> Interest:
        db_interest = self.get_interest(interest_id, user_id)
        
        update_data = interest.dict(exclude_unset=True)
        for field, value in update_data.items():
            setattr(db_interest, field, value)
            
        self.db.commit()
        self.db.refresh(db_interest)
        return db_interest

    def delete_interest(self, interest_id: int, user_id: int) -> dict:
        db_interest = self.get_interest(interest_id, user_id)
        self.db.delete(db_interest)
        self.db.commit()
        return {"message": "Interest deleted successfully"}
