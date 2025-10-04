from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from api.v1.services.mentoring.mentor_review_service import MentorReviewService
from api.v1.schemas.mentoring.mentor_review_schema import MentorReviewCreate, MentorReviewDetail, MentorReviewUpdate
from typing import List, Optional
from core.database.database import get_db
from core.security.auth import get_current_user

router = APIRouter(prefix="/api/v1/mentors/reviews", tags=["Mentor Review"])

@router.post("/", status_code=status.HTTP_201_CREATED)
def create_mentor_review(
  mentor_review_create: MentorReviewCreate,
  db: Session = Depends(get_db),
  current_user: dict = Depends(get_current_user)
) -> MentorReviewDetail:
  try:
    if not current_user:
      raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Unauthorized")
    mentoring_service = MentorReviewService(db)
    return mentoring_service.create(mentor_review_create)
  except HTTPException as e:
    raise e
  except Exception as e:
    raise HTTPException(status_code=400, detail=str(e))

@router.get("/")
def get_mentor_review(
  review_id: Optional[int] = None,
  mentor_id: Optional[int] = None,
  user_id: Optional[int] = None,
  db: Session = Depends(get_db),
  current_user: dict = Depends(get_current_user)
) -> List[MentorReviewDetail]:
  try:
    if not current_user:
      raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Unauthorized")
    mentoring_service = MentorReviewService(db)
    if mentor_id:
      return mentoring_service.get_by_mentor_id(mentor_id)
    elif user_id:
      return mentoring_service.get_by_user_id(user_id)
    else:
      return mentoring_service.get_by_id(review_id)
  except HTTPException as e:
    raise e

@router.put("/")
def update_mentor_review(
  review_id: int,
  mentor_review_update: MentorReviewUpdate,
  db: Session = Depends(get_db),
  current_user: dict = Depends(get_current_user)
) -> MentorReviewDetail:
  try:
    if not current_user:
      raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Unauthorized")
    mentoring_service = MentorReviewService(db)
    return mentoring_service.update(review_id, mentor_review_update)
  except HTTPException as e:
    raise e
  except Exception as e:
    raise HTTPException(status_code=400, detail=str(e))
  
@router.delete("/")
def delete_mentor_review(
  review_id: int,
  db: Session = Depends(get_db),
  current_user: dict = Depends(get_current_user)
) -> bool:
  try:
    if not current_user:
      raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Unauthorized")
    mentoring_service = MentorReviewService(db)
    return mentoring_service.delete(review_id)
  except HTTPException as e:
    raise e
  except Exception as e:
    raise HTTPException(status_code=400, detail=str(e))
