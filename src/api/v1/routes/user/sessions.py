from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Optional

from core.database.database import get_db
from api.v1.schemas.user.session_schema import (
    Session as SessionSchema,
    SessionCreate
)
from api.v1.services.user.session_service import SessionService
from core.security.auth import get_current_user

router = APIRouter(
    prefix="/api/v1/users/{user_id}/sessions",
    tags=["sessions"]
)

@router.get("/", response_model=List[SessionSchema])
def list_sessions(
  user_id: int,
  is_current: Optional[bool] = None,
  limit: int = Query(100, ge=1, le=1000),
  offset: int = Query(0, ge=0),
  db: Session = Depends(get_db),
  current_user: dict = Depends(get_current_user)
):
  """
  Get all sessions for a user with optional filters
  """
  if current_user.id != user_id:
    raise HTTPException(
      status_code=status.HTTP_403_FORBIDDEN,
      detail="Not authorized to access this resource"
    )
      
  service = SessionService(db)
  return service.get_user_sessions(
    user_id=user_id,
    is_current=is_current,
    limit=limit,
    offset=offset
  )

@router.get("/active-count", response_model=dict)
def get_active_sessions_count(
  user_id: int,
  db: Session = Depends(get_db),
  current_user: dict = Depends(get_current_user)
):
  """
  Get count of active sessions for a user
  """
  if current_user.id != user_id:
    raise HTTPException(
      status_code=status.HTTP_403_FORBIDDEN,
      detail="Not authorized to access this resource"
    )
        
  service = SessionService(db)
  return {"count": service.get_active_sessions_count(user_id)}

@router.post("/", response_model=SessionSchema, status_code=status.HTTP_201_CREATED)
def create_session(
  user_id: int,
  session: SessionCreate,
  db: Session = Depends(get_db),
  current_user: dict = Depends(get_current_user)
):
  """
  Create a new session for a user (typically used during login)
  """
  if current_user.id != user_id:
    raise HTTPException(
      status_code=status.HTTP_403_FORBIDDEN,
      detail="Not authorized to perform this action"
    )
        
  service = SessionService(db)
  return service.create_session(user_id, session)

@router.get("/{session_id}", response_model=SessionSchema)
def get_session(
  user_id: int,
  session_id: str,
  db: Session = Depends(get_db),
  current_user: dict = Depends(get_current_user)
):
  """
  Get a specific session by ID
  """
  if current_user.id != user_id:
    raise HTTPException(
      status_code=status.HTTP_403_FORBIDDEN,
      detail="Not authorized to access this resource"
    )
        
  service = SessionService(db)
  return service.get_session(session_id, user_id)

@router.post("/{session_id}/refresh", response_model=SessionSchema)
def refresh_session(
  user_id: int,
  session_id: str,
  db: Session = Depends(get_db),
  current_user: dict = Depends(get_current_user)
):
  """
  Refresh a session's last active timestamp
  """
  if current_user.id != user_id:
    raise HTTPException(
      status_code=status.HTTP_403_FORBIDDEN,
      detail="Not authorized to perform this action"
    )
        
  service = SessionService(db)
  return service.update_session_activity(session_id, user_id)

@router.delete("/{session_id}", status_code=status.HTTP_204_NO_CONTENT)
def invalidate_session(
  user_id: int,
  session_id: str,
  db: Session = Depends(get_db),
  current_user: dict = Depends(get_current_user)
):
  """
  Invalidate a specific session (logout)
  """
  if current_user.id != user_id:
    raise HTTPException(
      status_code=status.HTTP_403_FORBIDDEN,
      detail="Not authorized to perform this action"
    )
        
  service = SessionService(db)
  service.invalidate_session(session_id, user_id)
  return None

@router.post("/invalidate-all", response_model=dict)
def invalidate_all_sessions(
  user_id: int,
  exclude_current: bool = False,
  db: Session = Depends(get_db),
  current_user: dict = Depends(get_current_user)
):
  """
  Invalidate all sessions for a user (logout from all devices)
  """
  if current_user.id != user_id:
    raise HTTPException(
      status_code=status.HTTP_403_FORBIDDEN,
      detail="Not authorized to perform this action"
    )
        
  service = SessionService(db)
  return service.invalidate_all_sessions(user_id, exclude_current=exclude_current)
