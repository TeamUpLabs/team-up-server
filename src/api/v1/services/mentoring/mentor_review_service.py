from sqlalchemy.orm import Session
from src.api.v1.repositories.mentoring.mentor_review_repository import MentorReviewRepository
from src.api.v1.schemas.mentoring.mentor_review_schema import MentorReviewCreate, MentorReviewDetail, MentorReviewUpdate
from src.api.v1.models.mentoring.mentor_review import MentorReview
from typing import List

class MentorReviewService:
  def __init__(self, db: Session):
    self.repository = MentorReviewRepository(db)
    
  def create(self, mentor_review_create: MentorReviewCreate) -> MentorReview:
    return self.repository.create(mentor_review_create)
    
  def get_by_id(self, review_id: int) -> MentorReviewDetail:
    return self.repository.get_by_id(review_id)
    
  def get_by_mentor_id(self, mentor_id: int) -> List[MentorReviewDetail]:
    return self.repository.get_by_mentor_id(mentor_id)
    
  def get_by_user_id(self, user_id: int) -> List[MentorReviewDetail]:
    return self.repository.get_by_user_id(user_id)
    
  def update(self, review_id: int, mentor_review_update: MentorReviewUpdate) -> MentorReview:
    return self.repository.update(review_id, mentor_review_update)
    
  def delete(self, review_id: int) -> bool:
    return self.repository.delete(review_id)