from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Optional

from core.database.database import get_db
from api.v1.schemas.user.session_schema import (
    SessionCreate,
    SessionDetail
)
from api.v1.services.user.session_service import SessionService
from core.security.auth import get_current_user

router = APIRouter(
    prefix="/api/v1/users/{user_id}/sessions",
    tags=["sessions"]
)

@router.post("/", response_model=SessionCreate, status_code=status.HTTP_201_CREATED)
def create_session(
  user_id: int,
  session: SessionCreate,
  db: Session = Depends(get_db),
  current_user: dict = Depends(get_current_user)
):
  """
  세션 생성
  """
  if current_user.id != user_id:
    raise HTTPException(
      status_code=status.HTTP_403_FORBIDDEN,
      detail="Not authorized to perform this action"
    )
        
  service = SessionService(db)
  return service.create_session(user_id, session)

@router.post("/end", status_code=status.HTTP_204_NO_CONTENT)
def end_session(
  user_id: int,
  session_id: int,
  db: Session = Depends(get_db),
  current_user: dict = Depends(get_current_user)
):
  """
  세션 종료
  """
  if current_user.id != user_id:
    raise HTTPException(
      status_code=status.HTTP_403_FORBIDDEN,
      detail="Not authorized to perform this action"
    )
        
  service = SessionService(db)
  return service.end(session_id, user_id)

@router.get("/current", response_model=SessionDetail)
def get_current_session(
  user_id: int,
  db: Session = Depends(get_db),
  current_user: dict = Depends(get_current_user)
):
  """
  현재 세션 조회
  """
  if current_user.id != user_id:
    raise HTTPException(
      status_code=status.HTTP_403_FORBIDDEN,
      detail="Not authorized to perform this action"
    )
        
  service = SessionService(db)
  return service.get_current_session(user_id)

@router.get("/all", response_model=List[SessionDetail])
def get_all_sessions(
  user_id: int,
  db: Session = Depends(get_db),
  current_user: dict = Depends(get_current_user)
):
  """
  세션 조회
  """
  if current_user.id != user_id:
    raise HTTPException(
      status_code=status.HTTP_403_FORBIDDEN,
      detail="Not authorized to perform this action"
    )
        
  service = SessionService(db)
  return service.get_all_sessions(user_id)

@router.delete("/{session_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_session(
  user_id: int,
  session_id: int,
  db: Session = Depends(get_db),
  current_user: dict = Depends(get_current_user)
):
  """
  세션 삭제
  """
  if current_user.id != user_id:
    raise HTTPException(
      status_code=status.HTTP_403_FORBIDDEN,
      detail="Not authorized to perform this action"
    )
        
  service = SessionService(db)
  service.remove(session_id)
  return None
