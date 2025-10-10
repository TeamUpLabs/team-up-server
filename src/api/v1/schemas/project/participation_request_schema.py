from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime
from src.api.v1.schemas.brief import UserBrief

class ParticipationRequestBase(BaseModel):
  project_id: str
  user_id: int
  message: Optional[str] = None
  
class ParticipationRequestCreate(ParticipationRequestBase):
  request_type: str = Field(..., description="Either 'invitation' or 'request'")
  
class ParticipationRequestUpdate(BaseModel):
  status: str = Field(..., description="Either 'accepted' or 'rejected'")
  
class ParticipationRequestDetail(ParticipationRequestBase):
  id: int
  request_type: str
  status: str
  created_at: datetime
  processed_at: Optional[datetime] = None
  user: UserBrief
  
  class Config:
    orm_mode = True
  
class ParticipationRequestList(BaseModel):
  items: List[ParticipationRequestDetail]
  total: int
