from pydantic import BaseModel
from typing import List, Dict
from src.api.v1.schemas.community.post_schema import PostDetail

class CommunityInfo(BaseModel):
  hot_topic: List[Dict[str, int]]
  posts: List[PostDetail]
  
  class Config:
    from_attributes = True