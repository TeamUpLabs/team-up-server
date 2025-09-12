from typing import List
from sqlalchemy.orm import Session
from fastapi import HTTPException, status
from api.v1.models.user import UserTechStack as DBTechStack
from api.v1.schemas.tech_stack_schema import (
    TechStackCreate,
    TechStackUpdate
)

class TechStackRepository:
  def __init__(self, db: Session):
    self.db = db
  
  def get_user_tech_stacks(self, user_id: int) -> List[DBTechStack]:
    """Get all tech stacks for a user"""
    return self.db.query(DBTechStack).filter(
      DBTechStack.user_id == user_id
    ).all()
  
  def get_tech_stack(self, tech_stack_id: int, user_id: int) -> DBTechStack:
    """Get a specific tech stack for a user"""
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
    self, 
    user_id: int, 
    tech_stack_data: TechStackCreate
  ) -> DBTechStack:
    """Create a new tech stack for a user"""
    # Check if the same tech already exists for the user
    existing_tech = self.db.query(DBTechStack).filter(
      DBTechStack.user_id == user_id,
      DBTechStack.tech == tech_stack_data.tech
    ).first()
      
    if existing_tech:
      raise HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST,
        detail=f"Tech stack '{tech_stack_data.tech}' already exists for this user"
      )
          
    db_tech = DBTechStack(
      user_id=user_id,
      **tech_stack_data.model_dump()
    )
      
    self.db.add(db_tech)
    self.db.commit()
    self.db.refresh(db_tech)
    return db_tech
  
  def update_tech_stack(
    self, 
    tech_stack_id: int, 
    user_id: int, 
    tech_stack_data: TechStackUpdate
  ) -> DBTechStack:
    """Update an existing tech stack"""
    db_tech = self.get_tech_stack(tech_stack_id, user_id)
    
    # If tech name is being updated, check for conflicts
    if hasattr(tech_stack_data, 'tech') and tech_stack_data.tech != db_tech.tech:
      existing_tech = self.db.query(DBTechStack).filter(
        DBTechStack.id != tech_stack_id,
        DBTechStack.user_id == user_id,
        DBTechStack.tech == tech_stack_data.tech
      ).first()
          
      if existing_tech:
        raise HTTPException(
          status_code=status.HTTP_400_BAD_REQUEST,
          detail=f"Tech stack '{tech_stack_data.tech}' already exists for this user"
        )
      
    update_data = tech_stack_data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
      setattr(db_tech, field, value)
        
    self.db.add(db_tech)
    self.db.commit()
    self.db.refresh(db_tech)
    return db_tech
  
  def delete_tech_stack(self, tech_stack_id: int, user_id: int) -> None:
    """Delete a tech stack"""
    db_tech = self.get_tech_stack(tech_stack_id, user_id)
    self.db.delete(db_tech)
    self.db.commit()
    return None
