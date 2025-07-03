from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime


class ParticipationRequestBase(BaseModel):
    project_id: str
    user_id: int
    message: Optional[str] = None


class ParticipationRequestCreate(ParticipationRequestBase):
    request_type: str = Field(..., description="Either 'invitation' or 'request'")


class ParticipationRequestUpdate(BaseModel):
    status: str = Field(..., description="Either 'accepted' or 'rejected'")


class ParticipationRequestResponse(ParticipationRequestBase):
    id: int
    request_type: str
    status: str
    created_at: datetime
    processed_at: Optional[datetime] = None
    
    class Config:
        orm_mode = True


class ParticipationRequestList(BaseModel):
    items: List[ParticipationRequestResponse]
    total: int 