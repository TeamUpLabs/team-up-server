from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
from api.v1.schemas.brief import UserBrief
from datetime import datetime

class PostBase(BaseModel):
  content: str = Field(..., min_length=1, max_length=1000)
  code: Optional[Dict[str, Any]] = None
  tags: Optional[List[str]] = None
  images: Optional[List[str]] = None
  videos: Optional[List[str]] = None
    

class PostCreate(PostBase):
  user_id: int
  
  pass
    
class PostUpdate(BaseModel):
  content: Optional[str] = None
  code: Optional[Dict[str, Any]] = None
  tags: Optional[List[str]] = None
  images: Optional[List[str]] = None
  videos: Optional[List[str]] = None
    
class PostBreif(PostBase):
  id: int
  created_at: datetime
  updated_at: datetime
  creator: Optional[UserBrief] = None
  
  class Config:
    from_attributes = True
        
class CommentCreate(BaseModel):
  content: str = Field(..., min_length=1, max_length=1000)
        
class PostComment(BaseModel):
  id: int
  content: str
  created_at: datetime
  updated_at: datetime
  user: Optional[UserBrief] = None
  
  class Config:
    from_attributes = True
        
class ReactionUsers(BaseModel):
  count: int
  users: List[UserBrief]
  
  class Config:
    from_attributes = True

class PostReactions(BaseModel):
  likes: ReactionUsers
  dislikes: ReactionUsers
  views: ReactionUsers
  shares: ReactionUsers
  comments: List[PostComment]
    
  class Config:
    from_attributes = True
    
class PostDetail(PostBase):
  id: int
  created_at: datetime
  updated_at: datetime
  creator: Optional[UserBrief] = None
  
  reaction: Optional[PostReactions] = None
  
  class Config:
    from_attributes = True
            