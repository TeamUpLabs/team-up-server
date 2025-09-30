from pydantic import BaseModel
from typing import Optional
from datetime import datetime
from api.v1.schemas.brief import UserBrief

class SessionBase(BaseModel):
  user_agent: Optional[str] = None
  ip_address: Optional[str] = None
  geo_location: Optional[str] = None
  device: Optional[str] = None
  device_type: Optional[str] = None
  os: Optional[str] = None
  browser: Optional[str] = None
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
  device: Optional[str] = None
  device_type: Optional[str] = None
  os: Optional[str] = None
  browser: Optional[str] = None
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