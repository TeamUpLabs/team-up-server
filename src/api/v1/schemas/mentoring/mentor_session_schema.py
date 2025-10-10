from pydantic import BaseModel
from src.api.v1.schemas.brief import UserBrief
from datetime import datetime
from src.api.v1.schemas.mentoring.mentor_schema import MentorDetail

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
  mentor: MentorDetail
  mentee: UserBrief
  
  created_at: datetime
  updated_at: datetime
  
  class Config:
    from_attributes = True