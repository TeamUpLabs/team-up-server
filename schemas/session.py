from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime
from .user import UserBrief

# 세션 기본 스키마
class SessionBase(BaseModel):
    user_agent: Optional[str] = None
    ip_address: Optional[str] = None
    geo_location: Optional[str] = None
    last_active_at: Optional[datetime] = None
    is_current: Optional[bool] = False
    device_id: str
    session_id: str

class SessionCreate(SessionBase):
    user_id: int

class SessionUpdate(BaseModel):
    user_agent: Optional[str] = None
    ip_address: Optional[str] = None
    geo_location: Optional[str] = None
    last_active_at: Optional[datetime] = None
    is_current: Optional[bool] = False

class SessionDetail(SessionBase):
    session_id: str
    id: int
    created_at: datetime
    updated_at: datetime
    user: UserBrief
    
    class Config:
        from_attributes = True
