from pydantic import BaseModel
from typing import Optional
from api.v1.schemas.brief import UserBrief

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
  mentor: Optional[UserBrief] = None
  user: Optional[UserBrief] = None
  
  class Config:
    from_attributes = True