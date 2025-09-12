from fastapi import HTTPException
from sqlalchemy.orm import Session
from api.v1.models.user.collaboration_preference import CollaborationPreference as DBCollaborationPreference
from api.v1.schemas.user.collaboration_preference_schema import CollaborationPreferenceCreate, CollaborationPreferenceUpdate, CollaborationPreference

class CollaborationPreferenceRepository:
  def __init__(self, db: Session):
    self.db = db
  
  def get_by_user_id(self, user_id: int) -> CollaborationPreference:
    db_obj = self.db.query(DBCollaborationPreference).filter(DBCollaborationPreference.user_id == user_id).first()
    if not db_obj:
      raise HTTPException(status_code=404, detail="Collaboration preference not found")
    return CollaborationPreference.model_validate(db_obj, from_attributes=True)
  
  def create(self, user_id: int, preference_data: CollaborationPreferenceCreate) -> DBCollaborationPreference:
    db_obj = DBCollaborationPreference(
      user_id=user_id,
      **preference_data.model_dump(exclude_unset=True)
    )
    self.db.add(db_obj)
    self.db.commit()
    self.db.refresh(db_obj)
    return db_obj
    
  def update(self, user_id: int, preference_data: CollaborationPreferenceUpdate) -> DBCollaborationPreference:
    db_obj = self.get_by_user_id(user_id)
    update_data = preference_data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
      setattr(db_obj, field, value)
    self.db.add(db_obj)
    self.db.commit()
    self.db.refresh(db_obj)
    return db_obj