from typing import List, Optional
from datetime import datetime
from sqlalchemy.orm import Session
from fastapi import HTTPException, status
from api.v1.models.notification import Notification as DBNotification
from api.v1.schemas.notification_schema import (
    NotificationCreate,
    NotificationUpdate,
    Notification,
    NotificationType
)

class NotificationService:
    def __init__(self, db: Session):
        self.db = db

    def get_user_notifications(
        self, 
        user_id: int,
        is_read: Optional[bool] = None,
        notification_type: Optional[NotificationType] = None,
        limit: int = 100,
        offset: int = 0
    ) -> List[Notification]:
        query = self.db.query(DBNotification).filter(
            DBNotification.receiver_id == user_id
        )
        
        if is_read is not None:
            query = query.filter(DBNotification.is_read == is_read)
            
        if notification_type is not None:
            query = query.filter(DBNotification.notification_type == notification_type)
            
        return query.order_by(DBNotification.created_at.desc()).offset(offset).limit(limit).all()

    def get_notification(self, notification_id: int, user_id: int) -> Notification:
        db_notification = self.db.query(DBNotification).filter(
            DBNotification.id == notification_id,
            DBNotification.receiver_id == user_id
        ).first()
        
        if not db_notification:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Notification with id {notification_id} not found for user {user_id}"
            )
        return db_notification

    def create_notification(
        self, user_id: int, notification: NotificationCreate
    ) -> Notification:
        db_notification = DBNotification(
            receiver_id=user_id,
            **notification.dict()
        )
        self.db.add(db_notification)
        self.db.commit()
        self.db.refresh(db_notification)
        return db_notification

    def mark_as_read(self, notification_id: int, user_id: int) -> Notification:
        db_notification = self.get_notification(notification_id, user_id)
        
        if not db_notification.is_read:
            db_notification.is_read = True
            db_notification.read_at = datetime.utcnow()
            self.db.commit()
            self.db.refresh(db_notification)
            
        return db_notification

    def mark_all_as_read(self, user_id: int) -> dict:
        self.db.query(DBNotification).filter(
            DBNotification.receiver_id == user_id,
            DBNotification.is_read == False
        ).update({
            DBNotification.is_read: True,
            DBNotification.read_at: datetime.now()
        })
        self.db.commit()
        return {"message": "All notifications marked as read"}

    def delete_notification(self, notification_id: int, user_id: int) -> dict:
        db_notification = self.get_notification(notification_id, user_id)
        self.db.delete(db_notification)
        self.db.commit()
        return {"message": "Notification deleted successfully"}
        
    def get_unread_count(self, user_id: int) -> int:
        return self.db.query(DBNotification).filter(
            DBNotification.receiver_id == user_id,
            DBNotification.is_read == False
        ).count()
