from typing import List, Optional
from datetime import datetime, timezone
from sqlalchemy.orm import Session
from fastapi import HTTPException, status
from api.v1.models.user import UserSession as DBSession
from api.v1.schemas.session_schema import (
    Session as SessionSchema,
    SessionCreate,
    SessionUpdate
)

class SessionService:
    def __init__(self, db: Session):
        self.db = db

    def get_user_sessions(
        self, 
        user_id: int,
        is_current: Optional[bool] = None,
        limit: int = 100,
        offset: int = 0
    ) -> List[SessionSchema]:
        query = self.db.query(DBSession).filter(
            DBSession.user_id == user_id
        )
        
        if is_current is not None:
            query = query.filter(DBSession.is_current == is_current)
            
        return query.order_by(DBSession.last_active_at.desc()).offset(offset).limit(limit).all()

    def get_session(self, session_id: str, user_id: int) -> SessionSchema:
        db_session = self.db.query(DBSession).filter(
            DBSession.id == session_id,
            DBSession.user_id == user_id
        ).first()
        
        if not db_session:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Session with id {session_id} not found for user {user_id}"
            )
        return db_session

    def create_session(
        self, user_id: int, session: SessionCreate
    ) -> SessionSchema:
        # Invalidate any existing sessions with the same device_id
        self.db.query(DBSession).filter(
            DBSession.user_id == user_id,
            DBSession.device_id == session.device_id
        ).update({"is_current": False})
        
        db_session = DBSession(
            user_id=user_id,
            **session.dict(),
            is_current=True
        )
        self.db.add(db_session)
        self.db.commit()
        self.db.refresh(db_session)
        return db_session

    def update_session_activity(
        self, session_id: str, user_id: int
    ) -> SessionSchema:
        db_session = self.get_session(session_id, user_id)
        db_session.last_active_at = datetime.now(timezone.utc)
        self.db.commit()
        self.db.refresh(db_session)
        return db_session

    def invalidate_session(self, session_id: str, user_id: int) -> dict:
        db_session = self.get_session(session_id, user_id)
        db_session.is_current = False
        self.db.commit()
        return {"message": "Session invalidated successfully"}

    def invalidate_all_sessions(self, user_id: int, exclude_current: bool = False) -> dict:
        query = self.db.query(DBSession).filter(
            DBSession.user_id == user_id,
            DBSession.is_current == True
        )
        
        if exclude_current:
            # This would typically be implemented by excluding the current session ID
            # from the query, which would be passed in from the request context
            pass
            
        query.update({"is_current": False})
        self.db.commit()
        return {"message": "All sessions invalidated successfully"}

    def get_active_sessions_count(self, user_id: int) -> int:
        return self.db.query(DBSession).filter(
            DBSession.user_id == user_id,
            DBSession.is_current == True
        ).count()
