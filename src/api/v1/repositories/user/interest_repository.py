from typing import List
from sqlalchemy.orm import Session
from fastapi import HTTPException, status
from src.api.v1.models.user.interest import UserInterest as DBInterest
from src.api.v1.schemas.user.interest_schema import (
    InterestCreate,
    InterestUpdate
)

class InterestRepository:
  def __init__(self, db: Session):
      self.db = db
  
  def get_user_interests(self, user_id: int) -> List[DBInterest]:
    """Get all interests for a user"""
    return self.db.query(DBInterest).filter(
      DBInterest.user_id == user_id
    ).all()
  
  def get_interest(self, interest_id: int, user_id: int) -> DBInterest:
    """Get a specific interest for a user"""
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
    self, 
    user_id: int, 
    interest_data: InterestCreate
  ) -> DBInterest:
    """Create a new interest for a user"""
    # Check if the same interest already exists for the user
    existing_interest = self.db.query(DBInterest).filter(
      DBInterest.user_id == user_id,
      DBInterest.interest_category == interest_data.interest_category,
      DBInterest.interest_name == interest_data.interest_name
    ).first()
      
    if existing_interest:
      raise HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST,
        detail="This interest already exists for the user"
      )
          
    db_interest = DBInterest(
      user_id=user_id,
      **interest_data.model_dump()
    )
      
    self.db.add(db_interest)
    self.db.commit()
    self.db.refresh(db_interest)
    return db_interest
  
  def update_interest(
    self, 
    interest_id: int, 
    user_id: int, 
    interest_data: InterestUpdate
  ) -> DBInterest:
    """Update an existing interest"""
    db_interest = self.get_interest(interest_id, user_id)
      
    # Check if the updated interest would conflict with an existing one
    if hasattr(interest_data, 'interest_category') and hasattr(interest_data, 'interest_name'):
      existing_interest = self.db.query(DBInterest).filter(
        DBInterest.id != interest_id,
        DBInterest.user_id == user_id,
        DBInterest.interest_category == interest_data.interest_category,
        DBInterest.interest_name == interest_data.interest_name
      ).first()
          
      if existing_interest:
        raise HTTPException(
          status_code=status.HTTP_400_BAD_REQUEST,
          detail="This interest already exists for the user"
        )
      
    update_data = interest_data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
      setattr(db_interest, field, value)
        
    self.db.add(db_interest)
    self.db.commit()
    self.db.refresh(db_interest)
    return db_interest
  
  def delete_interest(self, interest_id: int, user_id: int) -> None:
    """Delete an interest"""
    db_interest = self.get_interest(interest_id, user_id)
    self.db.delete(db_interest)
    self.db.commit()
    return None
