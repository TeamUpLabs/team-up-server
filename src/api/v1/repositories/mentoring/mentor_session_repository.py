from sqlalchemy.orm import Session
from api.v1.schemas.mentoring.mentor_session_schema import MentorSessionCreate, MentorSessionDetail, MentorSessionUpdate
from api.v1.models.mentoring.mentor_session import MentorSession
from fastapi import HTTPException
from typing import List

class MentorSessionRepository:
  def __init__(self, db: Session):
    self.db = db
    
  def create(self, mentor_session_create: MentorSessionCreate) -> MentorSession:
    try:
      mentor_session = MentorSession(**mentor_session_create.model_dump())
      self.db.add(mentor_session)
      self.db.commit()
      self.db.refresh(mentor_session)
      return mentor_session
    except Exception as e:
      raise HTTPException(status_code=500, detail=str(e))
  
  def get_by_id(self, session_id: int) -> MentorSessionDetail:
    try:
      mentor_session = self.db.query(MentorSession).filter(MentorSession.id == session_id).first()
      return MentorSessionDetail.model_validate(mentor_session, from_attributes=True)
    except Exception as e:
      raise HTTPException(status_code=500, detail=str(e))
  
  def get_by_mentor_id(self, mentor_id: int) -> List[MentorSessionDetail]:
    try:
      mentor_sessions = self.db.query(MentorSession).filter(MentorSession.mentor_id == mentor_id).all()
      return [MentorSessionDetail.model_validate(session, from_attributes=True) for session in mentor_sessions]
    except Exception as e:
      raise HTTPException(status_code=500, detail=str(e))
    
  def get_by_user_id(self, user_id: int) -> List[MentorSessionDetail]:
    try:
      mentor_sessions = self.db.query(MentorSession).filter(MentorSession.user_id == user_id).all()
      return [MentorSessionDetail.model_validate(session, from_attributes=True) for session in mentor_sessions]
    except Exception as e:
      raise HTTPException(status_code=500, detail=str(e))
    
  def update(self, session_id: int, mentor_session_update: MentorSessionUpdate) -> MentorSessionDetail:
    try:
      mentor_session = self.db.query(MentorSession).filter(MentorSession.id == session_id).first()
      if not mentor_session:
        raise HTTPException(status_code=404, detail="MentorSession not found")
      mentor_session.title = mentor_session_update.title
      mentor_session.description = mentor_session_update.description
      mentor_session.start_date = mentor_session_update.start_date
      mentor_session.end_date = mentor_session_update.end_date
      self.db.commit()
      self.db.refresh(mentor_session)
      return MentorSessionDetail.model_validate(mentor_session, from_attributes=True)
    except Exception as e:
      raise HTTPException(status_code=500, detail=str(e))
    
  def delete(self, session_id: int) -> None:
    try:
      mentor_session = self.db.query(MentorSession).filter(MentorSession.id == session_id).first()
      if not mentor_session:
        raise HTTPException(status_code=404, detail="MentorSession not found")
      self.db.delete(mentor_session)
      self.db.commit()
    except Exception as e:
      raise HTTPException(status_code=500, detail=str(e))