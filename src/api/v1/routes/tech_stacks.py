from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

from core.database.database import get_db
from api.v1.schemas.tech_stack_schema import (
    TechStack,
    TechStackCreate,
    TechStackUpdate
)
from api.v1.services.tech_stack_service import TechStackService
from core.security.auth import get_current_user

router = APIRouter(
  prefix="/api/v1/users/{user_id}/tech-stacks",
  tags=["tech-stacks"]
)

@router.get("/", response_model=List[TechStack])
def list_tech_stacks(
  user_id: int,
  db: Session = Depends(get_db),
  current_user: dict = Depends(get_current_user)
):
  """
  Get all tech stacks for a user
  """
  if current_user.id != user_id:
    raise HTTPException(
      status_code=status.HTTP_403_FORBIDDEN,
      detail="Not authorized to access this resource"
    )
      
  service = TechStackService(db)
  return service.get_user_tech_stacks(user_id)

@router.post("/", response_model=TechStack, status_code=status.HTTP_201_CREATED)
def create_tech_stack(
  user_id: int,
  tech_stack: TechStackCreate,
  db: Session = Depends(get_db),
  current_user: dict = Depends(get_current_user)
):
  """
  Add a new tech stack for a user
  """
  if current_user.id != user_id:
    raise HTTPException(
      status_code=status.HTTP_403_FORBIDDEN,
      detail="Not authorized to perform this action"
    )
        
  service = TechStackService(db)
  return service.create_tech_stack(user_id, tech_stack)

@router.get("/{tech_stack_id}", response_model=TechStack)
def get_tech_stack(
  user_id: int,
  tech_stack_id: int,
  db: Session = Depends(get_db),
  current_user: dict = Depends(get_current_user)
):
  """
    Get a specific tech stack by ID
    """
  if current_user.id != user_id:
    raise HTTPException(
      status_code=status.HTTP_403_FORBIDDEN,
      detail="Not authorized to access this resource"
    )
        
  service = TechStackService(db)
  return service.get_tech_stack(tech_stack_id, user_id)

@router.put("/{tech_stack_id}", response_model=TechStack)
def update_tech_stack(
  user_id: int,
  tech_stack_id: int,
  tech_stack: TechStackUpdate,
  db: Session = Depends(get_db),
  current_user: dict = Depends(get_current_user)
):
  """
  Update a tech stack
  """
  if current_user.id != user_id:
    raise HTTPException(
      status_code=status.HTTP_403_FORBIDDEN,
      detail="Not authorized to perform this action"
    )
      
  service = TechStackService(db)
  return service.update_tech_stack(tech_stack_id, user_id, tech_stack)

@router.delete("/{tech_stack_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_tech_stack(
  user_id: int,
  tech_stack_id: int,
  db: Session = Depends(get_db),
  current_user: dict = Depends(get_current_user)
):
  """
  Delete a tech stack
  """
  if current_user.id != user_id:
    raise HTTPException(
      status_code=status.HTTP_403_FORBIDDEN,
      detail="Not authorized to perform this action"
    )
        
  service = TechStackService(db)
  service.delete_tech_stack(tech_stack_id, user_id)
  return None
