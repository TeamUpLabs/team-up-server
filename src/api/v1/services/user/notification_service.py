from typing import List, Optional
from fastapi import HTTPException, status
from sqlalchemy.orm import Session
from api.v1.schemas.user.notification_schema import (
    NotificationCreate,
    NotificationUpdate,
    NotificationInDB,
    NotificationType
)
from api.v1.repositories.user.notification_repository import NotificationRepository

class NotificationService:
  def __init__(self, db: Session):
    self.repository = NotificationRepository(db)

  def get_user_notifications(
    self, 
    user_id: int,
    is_read: Optional[bool] = None,
    notification_type: Optional[NotificationType] = None,
    limit: int = 100,
    offset: int = 0
  ) -> List[NotificationInDB]:
    """Get notifications for a user with optional filters"""
    return self.repository.get_user_notifications(
      user_id=user_id,
      is_read=is_read,
      notification_type=notification_type,
      limit=limit,
      offset=offset
    )

  def get_notification(self, notification_id: int, user_id: int) -> NotificationInDB:
    """Get a specific notification for a user"""
    notification = self.repository.get(notification_id)
    if notification.receiver_id != user_id:
      raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail="Not authorized to access this notification"
      )
    return notification

  def create_notification(
    self,
    notification_data: NotificationCreate,
    sender_id: Optional[int] = None
  ) -> NotificationInDB:
    """Create a new notification"""
    return self.repository.create(notification_data)

  def update_notification(
    self,
    notification_id: int,
    user_id: int,
    notification_data: NotificationUpdate
  ) -> NotificationInDB:
    """Update a notification"""
    notification = self.get_notification(notification_id, user_id)
    
    if notification is None:
      raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail="Notification not found"
      )
    
    return self.repository.update(notification_id, notification_data)

  def mark_as_read(self, notification_id: int, user_id: int) -> NotificationInDB:
    """Mark a notification as read"""
    notification = self.get_notification(notification_id, user_id)
    
    if notification is None:
      raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail="Notification not found"
      )
    
    return self.repository.mark_as_read(notification.id)

  def mark_all_as_read(self, user_id: int) -> int:
    """Mark all notifications as read for a user"""
    return self.repository.mark_all_as_read(user_id)

  def delete_notification(self, notification_id: int, user_id: int) -> None:
    """Delete a notification"""
    notification = self.get_notification(notification_id, user_id)
    
    if notification is None:
      raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail="Notification not found"
      )
    
    self.repository.delete(notification.id)

  def get_unread_count(self, user_id: int) -> int:
    """Get count of unread notifications for a user"""
    return self.repository.get_unread_count(user_id)
