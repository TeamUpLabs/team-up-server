from sqlalchemy.orm import Session
from src.api.v1.repositories.mentoring.mentor_session_repository import MentorSessionRepository
from src.api.v1.schemas.mentoring.mentor_session_schema import MentorSessionCreate, MentorSessionDetail, MentorSessionUpdate
from typing import List

class MentorSessionService:
  def __init__(self, db: Session):
    self.repository = MentorSessionRepository(db)
    
  def create(self, mentor_session_create: MentorSessionCreate) -> MentorSessionDetail:
    return self.repository.create(mentor_session_create)
    
  def get_by_id(self, session_id: int) -> MentorSessionDetail:
    return self.repository.get_by_id(session_id)
    
  def get_by_mentor_id(self, mentor_id: int) -> List[MentorSessionDetail]:
    return self.repository.get_by_mentor_id(mentor_id)
    
  def get_by_mentee_id(self, mentee_id: int) -> List[MentorSessionDetail]:
    return self.repository.get_by_mentee_id(mentee_id)
    
  def update(self, session_id: int, mentor_session_update: MentorSessionUpdate) -> MentorSessionDetail:
    return self.repository.update(session_id, mentor_session_update)
    
  def delete(self, session_id: int) -> bool:
    return self.repository.delete(session_id)