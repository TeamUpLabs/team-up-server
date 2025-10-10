from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Optional

from src.core.database.database import get_db
from src.api.v1.schemas.user.notification_schema import (
    Notification,
    NotificationCreate,
    NotificationType
)
from src.api.v1.services.user.notification_service import NotificationService
from src.core.security.auth import get_current_user
from fastapi import Request
from fastapi.responses import StreamingResponse
import json
from src.core.utils.sse_manager import notification_sse_manager

router = APIRouter(
  prefix="/api/v1/users/{user_id}/notifications",
  tags=["notifications"]
)

@router.get("/sse")
async def notification_sse(
  user_id: int,
  request: Request,
  db: Session = Depends(get_db),
):
  queue = await notification_sse_manager.connect(user_id)
  
  async def event_generator():
    try:
      service = NotificationService(db)
      notifications = service.get_user_notifications(user_id=user_id)
      notifications_dict = notification_sse_manager.convert_to_dict(notifications)
      yield f"data: {json.dumps(notifications_dict)}\n\n"
    finally:
      db.close()
      
    async for event in notification_sse_manager.event_generator(user_id, queue):
      if await request.is_disconnected():
        await notification_sse_manager.disconnect(user_id, queue)
        break
      yield event

  return StreamingResponse(
    event_generator(),
    media_type="text/event-stream",
    headers={
      "Cache-Control": "no-cache",
      "Connection": "keep-alive",
      "X-Accel-Buffering": "no",
      "Access-Control-Allow-Origin": "*"  # Add CORS header
    }
  )

@router.get("/", response_model=List[Notification])
def list_notifications(
  user_id: int,
  is_read: Optional[bool] = None,
  notification_type: Optional[NotificationType] = None,
  limit: int = Query(100, ge=1, le=1000),
  offset: int = Query(0, ge=0),
  db: Session = Depends(get_db),
  current_user: dict = Depends(get_current_user)
):
  """
  Get all notifications for a user with optional filters
  """
  if current_user.id != user_id:
    raise HTTPException(
      status_code=status.HTTP_403_FORBIDDEN,
      detail="Not authorized to access this resource"
    )
      
  service = NotificationService(db)
  return service.get_user_notifications(
    user_id=user_id,
    is_read=is_read,
    notification_type=notification_type,
    limit=limit,
    offset=offset
  )

@router.get("/unread-count", response_model=dict)
def get_unread_count(
  user_id: int,
  db: Session = Depends(get_db),
  current_user: dict = Depends(get_current_user)
):
  """
  Get count of unread notifications for a user
  """
  if current_user.id != user_id:
    raise HTTPException(
      status_code=status.HTTP_403_FORBIDDEN,
      detail="Not authorized to access this resource"
    )
        
  service = NotificationService(db)
  return {"count": service.get_unread_count(user_id)}

@router.post("/", response_model=Notification, status_code=status.HTTP_201_CREATED)
def create_notification(
  user_id: int,
  notification: NotificationCreate,
  db: Session = Depends(get_db),
  current_user: dict = Depends(get_current_user)
):
  """
  Create a new notification for a user (typically used by the system)
  """
  # In a real application, you might want to restrict who can create notifications
  # For now, we'll allow any authenticated user to create notifications
    
  service = NotificationService(db)
  return service.create_notification(user_id, notification)

@router.get("/{notification_id}", response_model=Notification)
def get_notification(
  user_id: int,
  notification_id: int,
  db: Session = Depends(get_db),
  current_user: dict = Depends(get_current_user)
):
  """
  Get a specific notification by ID
  """
  if current_user.id != user_id:
    raise HTTPException(
      status_code=status.HTTP_403_FORBIDDEN,
      detail="Not authorized to access this resource"
    )
        
  service = NotificationService(db)
  return service.get_notification(notification_id, user_id)

@router.post("/{notification_id}/read", response_model=Notification)
def mark_as_read(
  user_id: int,
  notification_id: int,
  db: Session = Depends(get_db),
  current_user: dict = Depends(get_current_user)
):
  """
  Mark a notification as read
  """
  if current_user.id != user_id:
    raise HTTPException(
      status_code=status.HTTP_403_FORBIDDEN,
      detail="Not authorized to perform this action"
    )
        
  service = NotificationService(db)
  return service.mark_as_read(notification_id, user_id)

@router.post("/mark-all-read", response_model=dict)
def mark_all_as_read(
  user_id: int,
  db: Session = Depends(get_db),
  current_user: dict = Depends(get_current_user)
):
  """
  Mark all notifications as read for a user
  """
  if current_user.id != user_id:
    raise HTTPException(
      status_code=status.HTTP_403_FORBIDDEN,
      detail="Not authorized to perform this action"
    )
        
  service = NotificationService(db)
  return service.mark_all_as_read(user_id)

@router.delete("/{notification_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_notification(
  user_id: int,
  notification_id: int,
  db: Session = Depends(get_db),
  current_user: dict = Depends(get_current_user)
):
  """
  Delete a notification
  """
  if current_user.id != user_id:
    raise HTTPException(
      status_code=status.HTTP_403_FORBIDDEN,
      detail="Not authorized to perform this action"
    )
        
  service = NotificationService(db)
  service.delete_notification(notification_id, user_id)
  return None
