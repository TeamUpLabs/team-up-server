from pydantic import BaseModel
from typing import List
from api.v1.schemas.brief import UserBrief

class FollowBase(BaseModel):
  follower_id: int
  followed_id: int
  
class FollowCreate(FollowBase):
  pass
  
class FollowList(BaseModel):
  count: int
  users: List[UserBrief]
  
class FollowResponse(BaseModel):
  user: UserBrief