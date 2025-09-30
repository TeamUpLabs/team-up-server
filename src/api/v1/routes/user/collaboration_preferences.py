from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from core.database.database import get_db
from core.security.auth import get_current_user
from api.v1.schemas.user.collaboration_preference_schema import (
    CollaborationPreferenceCreate,
    CollaborationPreferenceUpdate,
    CollaborationPreference
)
from api.v1.services.user.collaboration_preference_service import CollaborationPreferenceService

router = APIRouter(
  prefix="/api/v1/users/{user_id}/collaboration-preferences",
  tags=["collaboration-preferences"]
)

@router.get("/", response_model=CollaborationPreference)
def get_user_collaboration_preference(
  user_id: int,
  db: Session = Depends(get_db),
  current_user: dict = Depends(get_current_user)
):
  """
  Get a user's collaboration preferences
  """
  if current_user.id != user_id:
    raise HTTPException(
      status_code=status.HTTP_403_FORBIDDEN,
      detail="Not authorized to access this resource"
    )
      
  service = CollaborationPreferenceService(db)
  return service.get(user_id)

@router.post("/", response_model=CollaborationPreference, status_code=status.HTTP_201_CREATED)
def create_collaboration_preference(
  user_id: int,
  preference: CollaborationPreferenceCreate,
  db: Session = Depends(get_db),
  current_user: dict = Depends(get_current_user)
):
  """
  Create collaboration preferences for a user
  """
  if current_user.id != user_id:
    raise HTTPException(
      status_code=status.HTTP_403_FORBIDDEN,
      detail="Not authorized to perform this action"
    )
    
  service = CollaborationPreferenceService(db)
  return service.create(user_id, preference)

@router.put("/", response_model=CollaborationPreference)
def update_collaboration_preference(
  user_id: int,
  preference: CollaborationPreferenceUpdate,
  db: Session = Depends(get_db),
  current_user: dict = Depends(get_current_user)
):
  """
  Update a user's collaboration preferences
  """
  if current_user.id != user_id:
    raise HTTPException(
      status_code=status.HTTP_403_FORBIDDEN,
      detail="Not authorized to perform this action"
    )
        
  service = CollaborationPreferenceService(db)
  return service.update(user_id, preference)
