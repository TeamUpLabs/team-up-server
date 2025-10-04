from sqlalchemy.orm import Session
from api.v1.schemas.mentoring.mentor_schema import MentorCreate, MentorUpdate, MentorDetail
from api.v1.models.mentoring.mentor import Mentor
from fastapi import HTTPException
from typing import List

class MentorRepository:
  def __init__(self, db: Session):
    self.db = db
    
  def create(self, mentor_create: MentorCreate) -> Mentor:
    try:
      mentor = Mentor(**mentor_create.model_dump())
      self.db.add(mentor)
      self.db.commit()
      self.db.refresh(mentor)
      return mentor
    except Exception as e:
      raise HTTPException(status_code=500, detail=str(e))
  
  def get(self, user_id: int) -> MentorDetail:
    try:
      mentor = self.db.query(Mentor).filter(Mentor.user_id == user_id).first()
      if not mentor:
        raise HTTPException(status_code=404, detail="Mentor not found")
      return MentorDetail.model_validate(mentor, from_attributes=True)
    except Exception as e:
      raise HTTPException(status_code=500, detail=str(e))
    
  def get_all(self) -> List[MentorDetail]:
    try:
      mentors = self.db.query(Mentor).all()
      return [MentorDetail.model_validate(mentor, from_attributes=True) for mentor in mentors]
    except Exception as e:
      raise HTTPException(status_code=500, detail=str(e))
  
  def update(self, user_id: int, mentor_update: MentorUpdate) -> Mentor:
    try:
      mentor = self.get(user_id)
      if not mentor:
        raise HTTPException(status_code=404, detail="Mentor not found")
      for key, value in mentor_update.model_dump(exclude_unset=True).items():
        setattr(mentor, key, value)
      self.db.add(mentor)
      self.db.commit()
      self.db.refresh(mentor)
      return mentor
    except Exception as e:
      raise HTTPException(status_code=500, detail=str(e))
    
  def delete(self, user_id: int) -> bool:
    try:
      mentor = self.db.query(Mentor).filter(Mentor.user_id == user_id).first()
      if not mentor:
        raise HTTPException(status_code=404, detail="Mentor not found")
      self.db.delete(mentor)
      self.db.commit()
      return True
    except Exception as e:
      raise HTTPException(status_code=500, detail=str(e))