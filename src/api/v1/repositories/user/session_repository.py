from typing import List, Optional
from datetime import datetime, timezone
from sqlalchemy.orm import Session
from fastapi import HTTPException, status
from api.v1.models.user.session import UserSession as DBSession
from api.v1.schemas.user.session_schema import SessionCreate, SessionUpdate

class SessionRepository:
  def __init__(self, db: Session):
    self.db = db

  def get_user_sessions(
    self, 
    user_id: int,
    is_current: Optional[bool] = None,
    limit: int = 100,
    offset: int = 0
  ) -> List[DBSession]:
    """Get all sessions for a user with optional filters"""
    query = self.db.query(DBSession).filter(
      DBSession.user_id == user_id
    )
    
    if is_current is not None:
      query = query.filter(DBSession.is_current == is_current)
        
    return query.order_by(DBSession.last_active_at.desc()).offset(offset).limit(limit).all()

  def get_session(self, session_id: str, user_id: int) -> DBSession:
    """Get a specific session by ID for a user"""
    db_session = self.db.query(DBSession).filter(
      DBSession.id == session_id,
      DBSession.user_id == user_id
    ).first()
    
    if not db_session:
      raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail=f"Session {session_id} not found for user {user_id}"
      )
    return db_session

  def create_session(self, session_data: SessionCreate) -> DBSession:
    """Create a new session"""
    db_session = DBSession(**session_data.model_dump())
    self.db.add(db_session)
    self.db.commit()
    self.db.refresh(db_session)
    return db_session

  def update_session(
    self, 
    session_id: str, 
    user_id: int, 
    session_data: SessionUpdate
  ) -> DBSession:
    """Update an existing session"""
    db_session = self.get_session(session_id, user_id)
      
    update_data = session_data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
      setattr(db_session, field, value)
          
    self.db.add(db_session)
    self.db.commit()
    self.db.refresh(db_session)
    return db_session

  def delete_session(self, session_id: str, user_id: int) -> None:
    """Delete a session"""
    db_session = self.get_session(session_id, user_id)
    self.db.delete(db_session)
    self.db.commit()

  def update_last_active(self, session_id: str, user_id: int) -> DBSession:
    """Update the last active timestamp of a session"""
    db_session = self.get_session(session_id, user_id)
    db_session.last_active_at = datetime.now(timezone.utc)
    self.db.add(db_session)
    self.db.commit()
    self.db.refresh(db_session)
    return db_session

  def invalidate_session(self, session_id: str, user_id: int) -> DBSession:
    """Mark a session as invalid/expired"""
    db_session = self.get_session(session_id, user_id)
    db_session.is_current = False
    db_session.expires_at = datetime.now(timezone.utc)
    self.db.add(db_session)
    self.db.commit()
    self.db.refresh(db_session)
    return db_session

  def invalidate_other_sessions(self, user_id: int, exclude_session_id: str) -> int:
    """Invalidate all other sessions except the specified one"""
    result = self.db.query(DBSession).filter(
      DBSession.user_id == user_id,
      DBSession.id != exclude_session_id,
      DBSession.is_current == True
    ).update({
      'is_current': False,
      'expires_at': datetime.now(timezone.utc)
    })
      
    self.db.commit()
    return result
