from typing import List
from sqlalchemy.orm import Session
from src.api.v1.schemas.user.interest_schema import (
    InterestCreate,
    InterestUpdate,
    InterestInDB
)
from src.api.v1.repositories.user.interest_repository import InterestRepository

class InterestService:
  def __init__(self, db: Session):
    self.repository = InterestRepository(db)

  def get_user_interests(self, user_id: int) -> List[InterestInDB]:
    """Get all interests for a user"""
    return self.repository.get_user_interests(user_id)

  def get_interest(self, interest_id: int, user_id: int) -> InterestInDB:
    """Get a specific interest for a user"""
    return self.repository.get_interest(interest_id, user_id)
      
  def create_interest(
    self, 
    user_id: int, 
    interest: InterestCreate
  ) -> InterestInDB:
    """Create a new interest for a user"""
    return self.repository.create_interest(user_id, interest)
      
  def update_interest(
    self, 
    interest_id: int, 
    user_id: int, 
    interest: InterestUpdate
  ) -> InterestInDB:
    """Update an existing interest"""
    return self.repository.update_interest(interest_id, user_id, interest)
      
  def delete_interest(self, interest_id: int, user_id: int) -> dict:
    """Delete an interest"""
    self.repository.delete_interest(interest_id, user_id)
    return {"message": "Interest deleted successfully"}
