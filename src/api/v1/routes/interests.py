from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

from core.database.database import get_db
from api.v1.schemas.interest_schema import (
    Interest,
    InterestCreate,
    InterestUpdate
)
from api.v1.services.interest_service import InterestService
from core.security.auth import get_current_user

router = APIRouter(
  prefix="/api/v1/users/{user_id}/interests",
  tags=["interests"]
)

@router.get("/", response_model=List[Interest])
def list_interests(
  user_id: int,
  db: Session = Depends(get_db),
  current_user: dict = Depends(get_current_user)
):
  """
  Get all interests for a user
  """
  if current_user.id != user_id:
    raise HTTPException(
      status_code=status.HTTP_403_FORBIDDEN,
      detail="Not authorized to access this resource"
    )
      
  service = InterestService(db)
  return service.get_user_interests(user_id)

@router.post("/", response_model=Interest, status_code=status.HTTP_201_CREATED)
def create_interest(
  user_id: int,
  interest: InterestCreate,
  db: Session = Depends(get_db),
  current_user: dict = Depends(get_current_user)
):
  """
  Add a new interest for a user
  """
  if current_user.id != user_id:
    raise HTTPException(
      status_code=status.HTTP_403_FORBIDDEN,
      detail="Not authorized to perform this action"
    )
        
  service = InterestService(db)
  return service.create_interest(user_id, interest)

@router.get("/{interest_id}", response_model=Interest)
def get_interest(
  user_id: int,
  interest_id: int,
  db: Session = Depends(get_db),
  current_user: dict = Depends(get_current_user)
):
  """
  Get a specific interest by ID
  """
  if current_user.id != user_id:
    raise HTTPException(
      status_code=status.HTTP_403_FORBIDDEN,
      detail="Not authorized to access this resource"
    )
        
  service = InterestService(db)
  return service.get_interest(interest_id, user_id)

@router.put("/{interest_id}", response_model=Interest)
def update_interest(
  user_id: int,
  interest_id: int,
  interest: InterestUpdate,
  db: Session = Depends(get_db),
  current_user: dict = Depends(get_current_user)
):
  """
  Update an interest
  """
  if current_user.id != user_id:
    raise HTTPException(
      status_code=status.HTTP_403_FORBIDDEN,
      detail="Not authorized to perform this action"
    )
        
  service = InterestService(db)
  return service.update_interest(interest_id, user_id, interest)

@router.delete("/{interest_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_interest(
  user_id: int,
  interest_id: int,
  db: Session = Depends(get_db),
  current_user: dict = Depends(get_current_user)
):
  """
  Delete an interest
  """
  if current_user.id != user_id:
    raise HTTPException(
      status_code=status.HTTP_403_FORBIDDEN,
      detail="Not authorized to perform this action"
    )
        
  service = InterestService(db)
  service.delete_interest(interest_id, user_id)
  return None
