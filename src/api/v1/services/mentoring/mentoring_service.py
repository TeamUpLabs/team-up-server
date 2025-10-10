from sqlalchemy.orm import Session
from src.api.v1.repositories.mentoring.mentor_repository import MentorRepository
from src.api.v1.schemas.mentoring.mentor_schema import MentorCreate, MentorDetail, MentorUpdate
from src.api.v1.models.mentoring.mentor import Mentor
from typing import List

class MentoringService:
  def __init__(self, db: Session):
    self.repository = MentorRepository(db)
    
  def create(self, mentor_create: MentorCreate) -> Mentor:
    return self.repository.create(mentor_create)
    
  def get(self, user_id: int) -> MentorDetail:
    return self.repository.get(user_id)
    
  def get_all(self) -> List[MentorDetail]:
    return self.repository.get_all()
    
  def update(self, user_id: int, mentor_update: MentorUpdate) -> Mentor:
    return self.repository.update(user_id, mentor_update)
    
  def delete(self, user_id: int) -> bool:
    return self.repository.delete(user_id)
  