from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional
from enum import Enum

class NotificationType(str, Enum):
    TASK_ASSIGNED = "task_assigned"
    TASK_UPDATED = "task_updated"
    TASK_COMPLETED = "task_completed"
    PROJECT_INVITE = "project_invite"
    MENTION = "mention"
    SYSTEM = "system"

class NotificationBase(BaseModel):
    title: str = Field(..., max_length=255)
    message: str
    notification_type: NotificationType
    is_read: bool = False
    metadata: Optional[dict] = None

class NotificationCreate(NotificationBase):
    pass

class NotificationUpdate(BaseModel):
    is_read: Optional[bool] = None

class NotificationInDB(NotificationBase):
    id: int
    user_id: int
    created_at: datetime
    read_at: Optional[datetime] = None

    class Config:
        from_attributes = True

class Notification(NotificationInDB):
    pass
