from pydantic import BaseModel
from typing import Optional
from api.v1.schemas.brief import UserBrief
from datetime import datetime

class MentorSessionBase(BaseModel):
  title: str
  description: str
  start_date: datetime
  end_date: datetime
  
  class Config:
    from_attributes = True

class MentorSessionCreate(MentorSessionBase):
  mentor_id: int
  mentee_id: int
  
  class Config:
    from_attributes = True

class MentorSessionUpdate(MentorSessionBase):
  id: int
  
  class Config:
    from_attributes = True

class MentorSessionDetail(MentorSessionBase):
  id: int
  mentor: Optional[UserBrief] = None
  mentee: Optional[UserBrief] = None
  
  class Config:
    from_attributes = True