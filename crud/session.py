from crud.base import CRUDBase
from models.user import UserSession
from schemas.session import SessionCreate, SessionDetail, SessionUpdate
from sqlalchemy.orm import Session
from fastapi import HTTPException, status
from datetime import datetime
from typing import List
import httpx
import logging

async def get_geoip(ip: str):
    async with httpx.AsyncClient() as client:
        response = await client.get(f"http://ip-api.com/json/{ip}")
        return response.json()


class CRUDSession(CRUDBase[UserSession, SessionCreate, SessionDetail]):
    """세션 모델에 대한 CRUD 작업"""
    
    async def create(self, db: Session, *, obj_in: SessionCreate) -> UserSession:
        """새 세션 생성. 이미 존재하는 session_id인 경우 해당 세션을 업데이트합니다."""
        try:
            # Check if session with this ID already exists
            existing_session = db.query(UserSession).filter(
                UserSession.session_id == obj_in.session_id
            ).first()
            
            if existing_session:
                # Update existing session
                existing_session.last_active_at = datetime.now()
                existing_session.is_current = True
                existing_session.ip_address = obj_in.ip_address
                existing_session.user_agent = obj_in.user_agent
                db.commit()
                db.refresh(existing_session)
                return existing_session
                
            # Create new session if not exists
            try:
                geoip = await get_geoip(obj_in.ip_address)
                geo_location = f"{geoip['country']}, {geoip['city']}" if geoip.get('country') and geoip.get('city') else None
            except Exception as e:
                logging.warning(f"Could not get geoip info: {str(e)}")
                geo_location = None
            
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
            
            db.add(db_session)
            db.commit()
            db.refresh(db_session)
            return db_session
            
        except Exception as e:
            db.rollback()
            logging.error(f"Error in session creation: {str(e)}", exc_info=True)
            raise
    
    def end(self, db: Session, *, session_id: str) -> UserSession:
        """세션 종료"""
        db_obj = db.query(UserSession).filter(UserSession.session_id == session_id).first()
        if not db_obj:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="세션을 찾을 수 없습니다.")
        
        db_obj.is_current = False
        db_obj.last_active_at = datetime.now()
        db.commit()
        return db_obj
      
    def get_current_session(self, db: Session, *, user_id: int) -> UserSession:
        """현재 세션 조회"""
        return db.query(UserSession).filter(UserSession.user_id == user_id, UserSession.is_current == True).first()
      
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
        return super().update(db, db_obj=db_obj, obj_in=obj_in)
    
    def remove(self, db: Session, *, id: int) -> UserSession:
        """세션 삭제"""
        return super().remove(db, id=id)
      
    def update_current_session(self, db: Session, *, user_id: int) -> UserSession:
        """현재 세션 업데이트"""
        db_obj = self.get_current_session(db, user_id=user_id)
        if not db_obj:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="세션을 찾을 수 없습니다.")
        
        db_obj.last_active_at = datetime.now()
        db_obj.is_current = True
        db.commit()
        return db_obj
    
session = CRUDSession(UserSession)