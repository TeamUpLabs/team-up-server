from sqlalchemy.orm import Session
from api.v1.repositories.user.session_repository import SessionRepository
from api.v1.schemas.user.session_schema import SessionCreate, SessionUpdate
from api.v1.models.user import UserSession
from typing import List

class SessionService:
  def __init__(self, db: Session):
    self.repository = SessionRepository(db)
    
  def create(self, obj_in: SessionCreate) -> UserSession:
    return self.repository.create(obj_in)
    
  def end(self, session_id: str, user_id: int) -> UserSession:
    return self.repository.end(session_id, user_id)
    
  def get_current_session(self, user_id: int, session_id: str) -> UserSession:
    return self.repository.get_current_session(user_id, session_id)
    
  def get_all_sessions(self, user_id: int) -> List[UserSession]:
    return self.repository.get_all_sessions(user_id)
    
  def get_session_by_id(self, session_id: str) -> UserSession:
    return self.repository.get_session_by_id(session_id)
    
  def get_all_sessions_by_user_id(self, user_id: int) -> List[UserSession]:
    return self.repository.get_all_sessions_by_user_id(user_id)
    
  def update(self, db_obj: UserSession, obj_in: SessionUpdate) -> UserSession:
    return self.repository.update(db_obj, obj_in)
    
  def remove(self, id: int) -> UserSession:
    return self.repository.remove(id)
    
  def update_current_session(self, user_id: int, session_id: str) -> UserSession:
    return self.repository.update_current_session(user_id, session_id)