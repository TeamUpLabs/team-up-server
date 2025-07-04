from typing import Optional, List
from pydantic import BaseModel, Field
from datetime import datetime

# 기본 알림 스키마
class NotificationBase(BaseModel):
    title: str = Field(..., min_length=1, max_length=100)
    message: str = Field(..., min_length=1)
    type: str = Field(..., min_length=1, max_length=100)
    project_id: Optional[str] = None
    result: Optional[str] = None

# 알림 생성 스키마
class NotificationCreate(NotificationBase):
    receiver_id: int
    sender_id: Optional[int] = None

# 알림 업데이트 스키마
class NotificationUpdate(BaseModel):
    is_read: Optional[bool] = None
    title: Optional[str] = Field(None, min_length=1, max_length=100)
    message: Optional[str] = Field(None, min_length=1)

# 간략한 사용자 정보
class UserBrief(BaseModel):
    id: int
    name: str
    profile_image: Optional[str] = None
    
    class Config:
        from_attributes = True

# 간략한 프로젝트 정보
class ProjectBrief(BaseModel):
    id: str
    title: str
    
    class Config:
        from_attributes = True

# 알림 응답 스키마
class NotificationResponse(NotificationBase):
    id: int
    timestamp: datetime
    is_read: bool
    sender: Optional[UserBrief] = None
    receiver: UserBrief
    project: Optional[ProjectBrief] = None
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True

# 알림 목록 응답 스키마
class NotificationListResponse(BaseModel):
    notifications: List[NotificationResponse]
    total_count: int
    unread_count: int 