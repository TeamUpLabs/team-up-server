from typing import List
from fastapi import HTTPException
from sqlalchemy.orm import Session
from src.api.v1.schemas.user.tech_stack_schema import (
    TechStackCreate,
    TechStackUpdate,
    TechStackInDB
)
from src.api.v1.repositories.user.tech_stack_repository import TechStackRepository

class TechStackService:
  def __init__(self, db: Session):
    self.repository = TechStackRepository(db)

  def get_user_tech_stacks(self, user_id: int) -> List[TechStackInDB]:
    """Get all tech stacks for a user"""
    return self.repository.get_user_tech_stacks(user_id)

  def get_tech_stack(self, tech_stack_id: int, user_id: int) -> TechStackInDB:
    """Get a specific tech stack for a user"""
    try:
      return self.repository.get_tech_stack(tech_stack_id, user_id)
    except Exception as e:
      raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail=f"Tech stack with id {tech_stack_id} not found for user {user_id}"
      )
      
  def create_tech_stack(
    self, 
    user_id: int, 
    tech_stack: TechStackCreate
  ) -> TechStackInDB:
    """Create a new tech stack for a user"""
    return self.repository.create_tech_stack(user_id, tech_stack)
      
  def update_tech_stack(
    self, 
    tech_stack_id: int, 
    user_id: int, 
    tech_stack: TechStackUpdate
  ) -> TechStackInDB:
    """Update an existing tech stack"""
    return self.repository.update_tech_stack(tech_stack_id, user_id, tech_stack)
      
  def delete_tech_stack(self, tech_stack_id: int, user_id: int) -> dict:
    """Delete a tech stack"""
    self.repository.delete_tech_stack(tech_stack_id, user_id)
    return {"message": "Tech stack deleted successfully"}
