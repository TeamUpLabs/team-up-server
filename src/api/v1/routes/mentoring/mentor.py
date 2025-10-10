from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from src.core.database.database import get_db
from src.core.security.auth import get_current_user
from src.api.v1.services.mentoring.mentoring_service import MentoringService
from src.api.v1.schemas.mentoring.mentor_schema import MentorCreate, MentorUpdate, MentorDetail
from typing import List

router = APIRouter(prefix="/api/v1/mentors", tags=["Mentor"])

@router.post("/", status_code=status.HTTP_201_CREATED)
def create_mentor(
  mentor_create: MentorCreate,
  db: Session = Depends(get_db),
  current_user: dict = Depends(get_current_user)
) -> MentorDetail:
  try:
    if not current_user:
      raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Unauthorized")
    mentoring_service = MentoringService(db)
    return mentoring_service.create(mentor_create)
  except HTTPException as e:
    raise e
  except Exception as e:
    raise HTTPException(status_code=400, detail=str(e))

@router.get("/all")
def get_all_mentor(
  db: Session = Depends(get_db),
  current_user: dict = Depends(get_current_user)
) -> List[MentorDetail]:
  try:
    if not current_user:
      raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Unauthorized")
    mentoring_service = MentoringService(db)
    return mentoring_service.get_all()
  except HTTPException as e:
    raise e
  except Exception as e:
    raise HTTPException(status_code=400, detail=str(e))
  
@router.get("/{user_id}")
def get_mentor(
  user_id: int,
  db: Session = Depends(get_db),
  current_user: dict = Depends(get_current_user)
) -> MentorDetail:
  try:
    if not current_user:
      raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Unauthorized")
    mentoring_service = MentoringService(db)
    return mentoring_service.get(user_id)
  except HTTPException as e:
    raise e
  except Exception as e:
    raise HTTPException(status_code=400, detail=str(e))
  
@router.put("/{user_id}")
def update_mentor(
  user_id: int,
  mentor_update: MentorUpdate,
  db: Session = Depends(get_db),
  current_user: dict = Depends(get_current_user)
) -> MentorDetail:
  try:
    if not current_user:
      raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Unauthorized")
    mentoring_service = MentoringService(db)
    return mentoring_service.update(user_id, mentor_update)
  except HTTPException as e:
    raise e
  except Exception as e:
    raise HTTPException(status_code=400, detail=str(e))
  
@router.delete("/{user_id}")
def delete_mentor(
  user_id: int,
  db: Session = Depends(get_db),
  current_user: dict = Depends(get_current_user)
) -> bool:
  try:
    if not current_user:
      raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Unauthorized")
    mentoring_service = MentoringService(db)
    return mentoring_service.delete(user_id)
  except HTTPException as e:
    raise e
  except Exception as e:
    raise HTTPException(status_code=400, detail=str(e))
