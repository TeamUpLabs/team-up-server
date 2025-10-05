from pydantic import BaseModel
from api.v1.schemas.brief import UserBrief
from api.v1.schemas.mentoring.mentor_schema import MentorDetail
from datetime import datetime

class MentorReviewBase(BaseModel):
  rating: int
  comment: str
  
  class Config:
    from_attributes = True
  
class MentorReviewCreate(MentorReviewBase):
  mentor_id: int
  user_id: int
  
  class Config:
    from_attributes = True
  
class MentorReviewUpdate(MentorReviewBase):
  id: int
  
  class Config:
    from_attributes = True

class MentorReviewDetail(MentorReviewBase):
  id: int
  mentor: MentorDetail
  user: UserBrief
  
  created_at: datetime
  updated_at: datetime
  
  class Config:
    from_attributes = True