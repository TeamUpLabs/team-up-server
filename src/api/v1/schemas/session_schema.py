from pydantic import BaseModel, Field, IPvAnyAddress
from datetime import datetime
from typing import Optional

class SessionBase(BaseModel):
    device_id: str
    user_agent: Optional[str] = None
    ip_address: Optional[str] = None
    geo_location: Optional[str] = None
    device: Optional[str] = None
    device_type: Optional[str] = None
    os: Optional[str] = None
    browser: Optional[str] = None
    is_current: bool = True

class SessionCreate(SessionBase):
    pass

class SessionUpdate(BaseModel):
    is_current: Optional[bool] = None
    last_active_at: Optional[datetime] = None

class SessionInDB(SessionBase):
    id: int
    user_id: int
    session_id: str
    last_active_at: datetime
    created_at: datetime

    class Config:
        orm_mode = True

class Session(SessionInDB):
    pass
