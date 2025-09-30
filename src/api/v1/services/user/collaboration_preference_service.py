from fastapi import HTTPException, status
from sqlalchemy.orm import Session
from api.v1.repositories.user.collaboration_preference_repository import CollaborationPreferenceRepository
from api.v1.schemas.user.collaboration_preference_schema import CollaborationPreferenceCreate, CollaborationPreferenceUpdate, CollaborationPreference

class CollaborationPreferenceService:
  def __init__(self, db: Session):
    self.repository = CollaborationPreferenceRepository(db)
    
  def get(self, user_id: int) -> CollaborationPreference:
    try:
      return self.repository.get_by_user_id(user_id)
    except HTTPException as e:
      if e.status_code == 404:
        raise HTTPException(
          status_code=status.HTTP_404_NOT_FOUND,
          detail=f"Collaboration preference for user {user_id} not found"
        )
      raise
    
  def create(self, user_id: int, preference_data: CollaborationPreferenceCreate) -> CollaborationPreference:
    try:
      return self.repository.create(user_id, preference_data)
    except HTTPException as e:
      if e.status_code == 404:
        raise HTTPException(
          status_code=status.HTTP_404_NOT_FOUND,
          detail=f"Collaboration preference for user {user_id} not found"
        )
      raise
    
  def update(self, user_id: int, preference_data: CollaborationPreferenceUpdate) -> CollaborationPreference:
    try:
      return self.repository.update(user_id, preference_data)
    except HTTPException as e:
      if e.status_code == 404:
        raise HTTPException(
          status_code=status.HTTP_404_NOT_FOUND,
          detail=f"Collaboration preference for user {user_id} not found"
        )
      raise