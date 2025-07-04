from typing import Optional, List, Dict
from sqlalchemy.orm import Session
from sqlalchemy import and_, desc
from fastapi import HTTPException, status
from datetime import datetime

from new_models.notification import Notification
from new_schemas.notification import NotificationCreate, NotificationUpdate
from new_crud.base import CRUDBase

class CRUDNotification(CRUDBase[Notification, NotificationCreate, NotificationUpdate]):
    """알림 모델에 대한 CRUD 작업"""
    
    def create_notification(self, db: Session, *, obj_in: NotificationCreate) -> Notification:
        """새 알림 생성"""
        db_obj = Notification(
            title=obj_in.title,
            message=obj_in.message,
            type=obj_in.type,
            timestamp=datetime.utcnow(),
            is_read=False,
            sender_id=obj_in.sender_id,
            receiver_id=obj_in.receiver_id,
            project_id=obj_in.project_id,
            result=obj_in.result
        )
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj
    
    def get_user_notifications(
        self, 
        db: Session, 
        *, 
        user_id: int, 
        skip: int = 0, 
        limit: int = 50,
        is_read: Optional[bool] = None
    ) -> List[Notification]:
        """사용자의 알림 목록 조회"""
        query = db.query(Notification).filter(Notification.receiver_id == user_id)
        
        if is_read is not None:
            query = query.filter(Notification.is_read == is_read)
        
        return query.order_by(desc(Notification.timestamp)).offset(skip).limit(limit).all()
    
    def get_unread_count(self, db: Session, *, user_id: int) -> int:
        """사용자의 읽지 않은 알림 개수 조회"""
        return db.query(Notification).filter(
            and_(
                Notification.receiver_id == user_id,
                Notification.is_read == False
            )
        ).count()
    
    def mark_as_read(self, db: Session, *, notification_id: int, user_id: int) -> Notification:
        """알림을 읽음으로 표시"""
        notification = db.query(Notification).filter(
            and_(
                Notification.id == notification_id,
                Notification.receiver_id == user_id
            )
        ).first()
        
        if not notification:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="알림을 찾을 수 없습니다."
            )
        
        notification.is_read = True
        db.commit()
        db.refresh(notification)
        return notification
    
    def mark_all_as_read(self, db: Session, *, user_id: int) -> Dict:
        """사용자의 모든 알림을 읽음으로 표시"""
        result = db.query(Notification).filter(
            and_(
                Notification.receiver_id == user_id,
                Notification.is_read == False
            )
        ).update({"is_read": True})
        
        db.commit()
        
        return {
            "status": "success",
            "message": f"{result}개의 알림이 읽음으로 표시되었습니다.",
            "updated_count": result
        }
    
    def delete_notification(self, db: Session, *, notification_id: int, user_id: int) -> Dict:
        """알림 삭제"""
        notification = db.query(Notification).filter(
            and_(
                Notification.id == notification_id,
                Notification.receiver_id == user_id
            )
        ).first()
        
        if not notification:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="알림을 찾을 수 없습니다."
            )
        
        db.delete(notification)
        db.commit()
        
        return {"status": "success", "message": "알림이 삭제되었습니다."}
    
    def create_system_notification(
        self, 
        db: Session, 
        *, 
        user_id: int, 
        title: str, 
        message: str, 
        notification_type: str,
        project_id: Optional[str] = None,
        result: Optional[str] = None
    ) -> Notification:
        """시스템 알림 생성 (sender_id가 없는 경우)"""
        db_obj = Notification(
            title=title,
            message=message,
            type=notification_type,
            timestamp=datetime.utcnow(),
            is_read=False,
            sender_id=None,  # 시스템 알림
            receiver_id=user_id,
            project_id=project_id,
            result=result
        )
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj

# CRUDNotification 클래스 인스턴스 생성
notification = CRUDNotification(Notification) 