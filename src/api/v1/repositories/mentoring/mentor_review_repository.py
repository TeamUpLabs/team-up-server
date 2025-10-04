from sqlalchemy.orm import Session
from api.v1.schemas.mentoring.mentor_review_schema import MentorReviewCreate, MentorReviewUpdate, MentorReviewDetail
from api.v1.models.mentoring.mentor_review import MentorReview
from fastapi import HTTPException
from typing import List

class MentorReviewRepository:
  def __init__(self, db: Session):
    self.db = db
    
  def create(self, mentor_review_create: MentorReviewCreate) -> MentorReview:
    try:
      mentor_review = MentorReview(**mentor_review_create.model_dump())
      self.db.add(mentor_review)
      self.db.commit()
      self.db.refresh(mentor_review)
      return mentor_review
    except Exception as e:
      raise HTTPException(status_code=500, detail=str(e))
    
  def get_by_id(self, review_id: int) -> MentorReviewDetail:
    try:
      mentor_review = self.db.query(MentorReview).filter(MentorReview.id == review_id).first()
      return MentorReviewDetail.model_validate(mentor_review, from_attributes=True)
    except Exception as e:
      raise HTTPException(status_code=500, detail=str(e))
    
  def get_by_mentor_id(self, mentor_id: int) -> List[MentorReviewDetail]:
    try:
      mentor_reviews = self.db.query(MentorReview).filter(MentorReview.mentor_id == mentor_id).all()
      return [MentorReviewDetail.model_validate(review, from_attributes=True) for review in mentor_reviews]
    except Exception as e:
      raise HTTPException(status_code=500, detail=str(e))
    
  def get_by_user_id(self, user_id: int) -> List[MentorReviewDetail]:
    try:
      mentor_reviews = self.db.query(MentorReview).filter(MentorReview.user_id == user_id).all()
      return [MentorReviewDetail.model_validate(review, from_attributes=True) for review in mentor_reviews]
    except Exception as e:
      raise HTTPException(status_code=500, detail=str(e))
    
  def update(self, mentor_review_update: MentorReviewUpdate) -> MentorReview:
    try:
      mentor_review = self.db.query(MentorReview).filter(MentorReview.id == mentor_review_update.id).first()
      if not mentor_review:
        raise HTTPException(status_code=404, detail="Mentor review not found")
      mentor_review.rating = mentor_review_update.rating
      mentor_review.comment = mentor_review_update.comment
      self.db.commit()
      self.db.refresh(mentor_review)
      return mentor_review
    except Exception as e:
      raise HTTPException(status_code=500, detail=str(e))
    
  def delete(self, review_id: int) -> bool:
    try:
      mentor_review = self.db.query(MentorReview).filter(MentorReview.id == review_id).first()
      if not mentor_review:
        raise HTTPException(status_code=404, detail="Mentor review not found")
      self.db.delete(mentor_review)
      self.db.commit()
      return True
    except Exception as e:
      raise HTTPException(status_code=500, detail=str(e))