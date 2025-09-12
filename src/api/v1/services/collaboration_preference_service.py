from typing import List, Optional
from sqlalchemy.orm import Session
from fastapi import HTTPException, status
from api.v1.models.user import CollaborationPreference as DBCollaborationPreference
from api.v1.schemas.collaboration_preference_schema import (
    CollaborationPreferenceCreate,
    CollaborationPreferenceUpdate,
    CollaborationPreference
)

class CollaborationPreferenceService:
    def __init__(self, db: Session):
        self.db = db

    def get_collaboration_preference(self, user_id: int) -> Optional[CollaborationPreference]:
        db_pref = self.db.query(DBCollaborationPreference).filter(
            DBCollaborationPreference.user_id == user_id
        ).first()
        if not db_pref:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Collaboration preference for user {user_id} not found"
            )
        return db_pref

    def create_collaboration_preference(
        self, user_id: int, preference: CollaborationPreferenceCreate
    ) -> CollaborationPreference:
        # Check if preference already exists
        existing_pref = self.db.query(DBCollaborationPreference).filter(
            DBCollaborationPreference.user_id == user_id
        ).first()
        
        if existing_pref:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Collaboration preference for user {user_id} already exists"
            )
            
        db_pref = DBCollaborationPreference(
            user_id=user_id,
            **preference.dict()
        )
        self.db.add(db_pref)
        self.db.commit()
        self.db.refresh(db_pref)
        return db_pref

    def update_collaboration_preference(
        self, user_id: int, preference: CollaborationPreferenceUpdate
    ) -> CollaborationPreference:
        db_pref = self.db.query(DBCollaborationPreference).filter(
            DBCollaborationPreference.user_id == user_id
        ).first()
        
        if not db_pref:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Collaboration preference for user {user_id} not found"
            )
            
        update_data = preference.dict(exclude_unset=True)
        for field, value in update_data.items():
            setattr(db_pref, field, value)
            
        self.db.commit()
        self.db.refresh(db_pref)
        return db_pref

    def delete_collaboration_preference(self, user_id: int) -> None:
        db_pref = self.db.query(DBCollaborationPreference).filter(
            DBCollaborationPreference.user_id == user_id
        ).first()
        
        if not db_pref:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Collaboration preference for user {user_id} not found"
            )
            
        self.db.delete(db_pref)
        self.db.commit()
        return {"message": "Collaboration preference deleted successfully"}
