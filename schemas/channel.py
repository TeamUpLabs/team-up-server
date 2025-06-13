from pydantic import BaseModel
from typing import Optional, List
from schemas.member import Member

class ChannelBase(BaseModel):
  projectId: str
  channelId: str
  channelName: str
  channelDescription: Optional[str]
  isPublic: bool
    
class ChannelCreate(ChannelBase):
  member_id: List[int]
  created_at: str
  created_by: int
  
class Channel(ChannelBase):
  id: int
  member_id: List[int]
  members: List[Member]
  created_at: str
  created_by: int
  
class ChannelUpdate(BaseModel):
  channelName: Optional[str]
  channelDescription: Optional[str]
  isPublic: Optional[bool]
  member_id: Optional[List[int]]
  