from typing import List, Optional
from datetime import datetime
from sqlalchemy.orm import Session
from fastapi import HTTPException, status
from src.api.v1.models.user.notification import Notification as DBNotification
from src.api.v1.schemas.user.notification_schema import (
    NotificationCreate,
    NotificationUpdate,
    NotificationType
)

class NotificationRepository:
  def __init__(self, db: Session):
    self.db = db
      
  def get(self, notification_id: int) -> DBNotification:
    """Get a notification by ID"""
    db_notification = self.db.query(DBNotification).filter(
        DBNotification.id == notification_id
    ).first()
    
    if not db_notification:
      raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail="Notification not found"
      )
    return db_notification
      
  def get_user_notifications(
    self, 
    user_id: int,
    is_read: Optional[bool] = None,
    notification_type: Optional[NotificationType] = None,
    limit: int = 100,
    offset: int = 0
  ) -> List[DBNotification]:
    """Get notifications for a user with optional filters"""
    query = self.db.query(DBNotification).filter(
      DBNotification.receiver_id == user_id
    )
    
    if is_read is not None:
      query = query.filter(DBNotification.is_read == is_read)
      
    if notification_type is not None:
      query = query.filter(DBNotification.type == notification_type)
          
    return query.order_by(DBNotification.timestamp.desc()).offset(offset).limit(limit).all()
      
  def create(self, notification_data: NotificationCreate) -> DBNotification:
    """Create a new notification"""
    db_notification = DBNotification(
      title=notification_data.title,
      message=notification_data.message,
      type=notification_data.notification_type,
      is_read=notification_data.is_read,
      receiver_id=notification_data.receiver_id,
      sender_id=notification_data.sender_id,
      project_id=notification_data.project_id,
      timestamp=datetime.now(datetime.timezone.utc)
    )
      
    self.db.add(db_notification)
    self.db.commit()
    self.db.refresh(db_notification)
    return db_notification
      
  def update(
    self, 
    notification_id: int, 
    notification_data: NotificationUpdate
  ) -> DBNotification:
    """Update a notification"""
    db_notification = self.get(notification_id)
      
    update_data = notification_data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
      setattr(db_notification, field, value)
          
    self.db.add(db_notification)
    self.db.commit()
    self.db.refresh(db_notification)
    return db_notification
      
  def mark_as_read(self, notification_id: int) -> DBNotification:
    """Mark a notification as read"""
    return self.update(notification_id, NotificationUpdate(is_read=True))
      
  def mark_all_as_read(self, user_id: int) -> int:
    """Mark all notifications as read for a user"""
    result = self.db.query(DBNotification).filter(
      DBNotification.receiver_id == user_id,
      DBNotification.is_read == False
    ).update({"is_read": True})
      
    self.db.commit()
    return result
      
  def delete(self, notification_id: int) -> None:
    """Delete a notification"""
    db_notification = self.get(notification_id)
    self.db.delete(db_notification)
    self.db.commit()
      
  def get_unread_count(self, user_id: int) -> int:
    """Get count of unread notifications for a user"""
    return self.db.query(DBNotification).filter(
      DBNotification.receiver_id == user_id,
      DBNotification.is_read == False
    ).count()
