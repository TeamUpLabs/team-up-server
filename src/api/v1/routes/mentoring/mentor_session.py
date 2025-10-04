from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from api.v1.services.mentoring.mentor_session_service import MentorSessionService
from api.v1.schemas.mentoring.mentor_session_schema import MentorSessionCreate, MentorSessionDetail, MentorSessionUpdate
from typing import List, Optional
from core.database.database import get_db
from core.security.auth import get_current_user

router = APIRouter(prefix="/api/v1/mentors/sessions", tags=["Mentor Session"])

@router.post("/")
def create_mentor_session(
  mentor_session_create: MentorSessionCreate,
  db: Session = Depends(get_db),
  current_user: dict = Depends(get_current_user)
) -> MentorSessionDetail:
  try:
    if not current_user:
      raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Unauthorized")
    mentoring_service = MentorSessionService(db)
    return mentoring_service.create(mentor_session_create)
  except HTTPException as e:
    raise e
  except Exception as e:
    raise HTTPException(status_code=400, detail=str(e))
  
@router.get("/")
def get_mentor_session(
  session_id: Optional[int] = None,
  mentor_id: Optional[int] = None,
  user_id: Optional[int] = None,
  db: Session = Depends(get_db),
  current_user: dict = Depends(get_current_user)
) -> List[MentorSessionDetail]:
  try:
    if not current_user:
      raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Unauthorized")
    mentoring_service = MentorSessionService(db)
    
    if mentor_id:
      return mentoring_service.get_by_mentor_id(mentor_id)
    elif user_id:
      return mentoring_service.get_by_user_id(user_id)
    else:
      return mentoring_service.get_by_id(session_id)
  except HTTPException as e:
    raise e
  except Exception as e:
    raise HTTPException(status_code=400, detail=str(e))
    
@router.put("/")
def update_mentor_session(
  session_id: int,
  mentor_session_update: MentorSessionUpdate,
  db: Session = Depends(get_db),
  current_user: dict = Depends(get_current_user)
) -> MentorSessionDetail:
  try:
    if not current_user:
      raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Unauthorized")
    mentoring_service = MentorSessionService(db)
    return mentoring_service.update(session_id, mentor_session_update)
  except HTTPException as e:
    raise e
  except Exception as e:
    raise HTTPException(status_code=400, detail=str(e))
    
@router.delete("/")
def delete_mentor_session(
  session_id: int,
  db: Session = Depends(get_db),
  current_user: dict = Depends(get_current_user)
) -> bool:
  try:
    if not current_user:
      raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Unauthorized")
    mentoring_service = MentorSessionService(db)
    return mentoring_service.delete(session_id)
  except HTTPException as e:
    raise e
  except Exception as e:
    raise HTTPException(status_code=400, detail=str(e))

    