from fastapi import APIRouter, Depends, HTTPException, status
from typing import List
from schemas.session import SessionCreate, SessionDetail
from database import get_db
from utils.auth import get_current_user
from crud.session import session
from sqlalchemy.orm import Session
from models.user import User
from models.user import UserSession

router = APIRouter(
    prefix="/api/sessions",
    tags=["sessions"]
)

@router.post("/", response_model=SessionDetail, status_code=status.HTTP_201_CREATED)
async def create_session(session_in: SessionCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """새 세션 생성"""
    if current_user.id != session_in.user_id:
      raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="세션 생성 권한이 없습니다.")
    
    db_session = session.create(db, obj_in=session_in)
    
    return SessionDetail.model_validate(db_session, from_attributes=True)
  
@router.post("/end", status_code=status.HTTP_200_OK)
async def end_session(session_id: str, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """세션 종료"""
    if current_user.id != session_id:
      raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="세션 종료 권한이 없습니다.")
    
    session.end(db, session_id=session_id)
    
    return {"status": "ended"}
  
@router.get("/current", response_model=SessionDetail)
async def get_current_session(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """현재 세션 조회"""
    db_session = session.get_current_session(db, user_id=current_user.id)
    if not db_session:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="현재 활성화된 세션이 없습니다.")
    return SessionDetail.model_validate(db_session, from_attributes=True)

@router.get("/all", response_model=List[SessionDetail])
async def get_all_sessions(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """모든 세션 조회"""
    db_sessions = session.get_all_sessions(db, user_id=current_user.id)
    return [SessionDetail.model_validate(session, from_attributes=True) for session in db_sessions]
  
@router.delete("/{session_id}", status_code=status.HTTP_200_OK)
async def delete_session(session_id: str, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """세션 삭제"""
    
    session.remove(db, id=session_id)
    
    return {"status": "deleted"}
