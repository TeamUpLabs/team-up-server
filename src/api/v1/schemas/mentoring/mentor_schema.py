from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from api.v1.schemas.brief import UserBrief

class MentorBase(BaseModel):
  location: List[str]
  experience: int
  topic: List[str]
  bio: str
  availablefor: List[str]
  
  class Config:
    from_attributes = True
  
class MentorCreate(MentorBase):
  user_id: int
  
  class Config:
    from_attributes = True

class MentorUpdate(MentorBase):
  id: int

class MentorDetail(MentorBase):
  id: int
  user: Optional[UserBrief] = None

  
  links: Dict[str, Any] = {}
  
  def model_post_init(self, __context):
    base_url = f"/api/v1/mentors"
    self.links = {
      "self": {
        "href": f"{base_url}/{self.id}",
        "method": "GET",
        "title": "멘토 정보 조회"
      },
      "reviews": {
        "href": f"{base_url}/reviews/?mentor_id={self.id}",
        "method": "GET",
        "title": "멘토 리뷰 조회"
      },
      "sessions": {
        "href": f"{base_url}/sessions/?mentor_id={self.id}",
        "method": "GET",
        "title": "멘토 세션 조회"
      }
    }