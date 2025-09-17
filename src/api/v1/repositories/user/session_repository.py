from sqlalchemy.orm import Session
from api.v1.schemas.user.session_schema import SessionCreate, SessionUpdate
from api.v1.models.user import UserSession
import httpx
from datetime import datetime
from fastapi import HTTPException, status
from typing import List

async def get_geoip(ip: str):
  async with httpx.AsyncClient() as client:
    response = await client.get(f"http://ip-api.com/json/{ip}")
    return response.json()

class SessionRepository:
  def __init__(self, db: Session):
    self.db = db
    
  async def create(self, obj_in: SessionCreate) -> UserSession:
    try:
      existing_session = self.db.query(UserSession).filter(UserSession.session_id == obj_in.session_id).first()
      
      if existing_session:
        existing_session.last_active_at = datetime.now()
        existing_session.is_current = True
        existing_session.ip_address = obj_in.ip_address
        existing_session.user_agent = obj_in.user_agent
        
        self.db.commit()
        self.db.refresh(existing_session)
        return existing_session
      
      try:
        geoip = await get_geoip(obj_in.ip_address)
        geo_location = f"{geoip['country']}, {geoip['city']}" if geoip.get('country') and geoip.get('city') else None
      except Exception as e:
        self.db.rollback()
        geo_location = None
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))
      
      db_session = UserSession(
        session_id=obj_in.session_id,
        user_id=obj_in.user_id,
        user_agent=obj_in.user_agent,
        device_id=obj_in.device_id,
        ip_address=obj_in.ip_address,
        device=obj_in.device,
        device_type=obj_in.device_type,
        os=obj_in.os,
        browser=obj_in.browser,
        geo_location=geo_location,
        last_active_at=datetime.now(),
        is_current=True
      )
      
      self.db.add(db_session)
      self.db.commit()
      self.db.refresh(db_session)
      return db_session
    
    except Exception as e:
      self.db.rollback()
      raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))
        
  def end(self, db: Session, *, session_id: str, user_id: int) -> UserSession:
    """세션 종료"""
    db_obj = db.query(UserSession).filter(UserSession.session_id == session_id, UserSession.user_id == user_id).first()
    if not db_obj:
      raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="세션을 찾을 수 없습니다.")
    
    db_obj.is_current = False
    db_obj.last_active_at = datetime.now()
    
    db.commit()
    db.refresh(db_obj)
    return db_obj

  def get_current_session(self, db: Session, *, user_id: int, session_id: str) -> UserSession:
    """현재 세션 조회"""
    return db.query(UserSession).filter(UserSession.user_id == user_id, UserSession.session_id == session_id).first()
  
  def get_all_sessions(self, db: Session, *, user_id: int) -> List[UserSession]:
    """모든 세션 조회"""
    return db.query(UserSession).filter(UserSession.user_id == user_id).all()
    
  def get_session_by_id(self, db: Session, *, session_id: str) -> UserSession:
    """세션 ID로 세션 조회"""
    return db.query(UserSession).filter(UserSession.session_id == session_id).first()
    
  def get_all_sessions_by_user_id(self, db: Session, *, user_id: int) -> List[UserSession]:
    """사용자 ID로 모든 세션 조회"""
    return db.query(UserSession).filter(UserSession.user_id == user_id).all()
    
  def update(self, db: Session, *, db_obj: UserSession, obj_in: SessionUpdate) -> UserSession:
    """세션 정보 업데이트"""
    update_data = obj_in.model_dump(exclude_unset=True)
    
    for key, value in update_data.items():
      setattr(db_obj, key, value)
    
    db.commit()
    db.refresh(db_obj)
    return db_obj
    
  def remove(self, db: Session, *, id: int) -> UserSession:
    """세션 삭제"""
    db_obj = db.query(UserSession).filter(UserSession.id == id).first()
    if not db_obj:
      raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="세션을 찾을 수 없습니다.")
    
    db.delete(db_obj)
    db.commit()
    return db_obj
  
  def update_current_session(self, db: Session, *, user_id: int, session_id: str) -> UserSession:
    """현재 세션 업데이트"""
    db_obj = self.get_current_session(db, user_id=user_id, session_id=session_id)
    if not db_obj:
      raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="세션을 찾을 수 없습니다.")
    
    db_obj.is_current = True
    db_obj.last_active_at = datetime.now()
    db.commit()
    db.refresh(db_obj)
    return db_obj