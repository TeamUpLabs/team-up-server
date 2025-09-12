from typing import List, Optional
from sqlalchemy.orm import Session
from fastapi import HTTPException, status
from api.v1.repositories.session_repository import SessionRepository
from api.v1.schemas.session_schema import (
    Session as SessionSchema,
    SessionCreate,
    SessionUpdate,
    SessionInDB
)

class SessionService:
  def __init__(self, db: Session):
    self.repository = SessionRepository(db)

  def get_user_sessions(
    self, 
    user_id: int,
    is_current: Optional[bool] = None,
    limit: int = 100,
    offset: int = 0
  ) -> List[SessionInDB]:
    """
    Get all sessions for a user with optional filters
    """
    return self.repository.get_user_sessions(
      user_id=user_id,
      is_current=is_current,
      limit=limit,
      offset=offset
    )

  def get_session(self, session_id: str, user_id: int) -> SessionInDB:
    """
    Get a specific session by ID for a user
    """
    return self.repository.get_session(session_id, user_id)

  def create_session(
    self, 
    user_id: int, 
    session_data: SessionCreate
  ) -> SessionInDB:
    """
    Create a new session for a user
    """
    # Invalidate any existing sessions with the same device_id
    self.repository.invalidate_other_sessions(user_id, session_data.device_id)
      
    # Create new session
    return self.repository.create_session(session_data)

  def update_session(
    self, 
    session_id: str, 
    user_id: int, 
    session_data: SessionUpdate
  ) -> SessionInDB:
    """
    Update an existing session
    """
    return self.repository.update_session(session_id, user_id, session_data)

  def delete_session(self, session_id: str, user_id: int) -> None:
    """
    Delete a session
    """
    self.repository.delete_session(session_id, user_id)

  def update_last_active(self, session_id: str, user_id: int) -> SessionInDB:
    """
    Update the last active timestamp of a session
    """
    return self.repository.update_last_active(session_id, user_id)

  def invalidate_session(self, session_id: str, user_id: int) -> SessionInDB:
    """
    Mark a session as invalid/expired
    """
    return self.repository.invalidate_session(session_id, user_id)

  def invalidate_other_sessions(
    self, 
    user_id: int, 
    exclude_session_id: str
  ) -> int:
    """
    Invalidate all other sessions except the specified one
    """
    return self.repository.invalidate_other_sessions(user_id, exclude_session_id)

  def get_active_session(
    self, 
    user_id: int, 
    device_id: str
  ) -> Optional[SessionInDB]:
    """
    Get the active session for a user and device
    """
    sessions = self.repository.get_user_sessions(
      user_id=user_id,
      is_current=True,
      limit=1
    )
      
    for session in sessions:
      if session.device_id == device_id:
        return session
      return None

  def update_session_activity(
    self, session_id: str, user_id: int
  ) -> SessionSchema:
    db_session = self.get_session(session_id, user_id)
    db_session.last_active_at = datetime.now(timezone.utc)
    self.db.commit()
    self.db.refresh(db_session)
    return db_session

  def invalidate_session(self, session_id: str, user_id: int) -> dict:
    db_session = self.get_session(session_id, user_id)
    db_session.is_current = False
    self.db.commit()
    return {"message": "Session invalidated successfully"}

  def invalidate_all_sessions(self, user_id: int, exclude_current: bool = False) -> dict:
    query = self.db.query(DBSession).filter(
      DBSession.user_id == user_id,
      DBSession.is_current == True
    )
      
    if exclude_current:
      # This would typically be implemented by excluding the current session ID
      # from the query, which would be passed in from the request context
      pass
          
    query.update({"is_current": False})
    self.db.commit()
    return {"message": "All sessions invalidated successfully"}

  def get_active_sessions_count(self, user_id: int) -> int:
    return self.db.query(DBSession).filter(
      DBSession.user_id == user_id,
      DBSession.is_current == True
    ).count()
