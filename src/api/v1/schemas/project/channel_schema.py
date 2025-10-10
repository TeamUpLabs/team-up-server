from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime
from src.api.v1.schemas.brief import UserBrief

class ChannelBase(BaseModel):
  """채널 기본 스키마"""
  name: str = Field(..., min_length=1, max_length=100, description="채널 이름")
  description: Optional[str] = Field(None, max_length=1000, description="채널 설명")
  is_public: bool = Field(True, description="공개 채널 여부")
    
class ChannelCreate(ChannelBase):
  """채널 생성 스키마"""
  project_id: str = Field(..., min_length=6, max_length=6, description="프로젝트 ID")
  channel_id: str = Field(..., min_length=1, max_length=100, description="채널 고유 ID")
  member_ids: List[int] = Field(..., description="채널 멤버 ID 목록")
  created_by: int
  updated_by: int
    
class ChannelUpdate(BaseModel):
  """채널 업데이트 스키마"""
  name: Optional[str] = None
  description: Optional[str] = None
  is_public: Optional[bool] = None
  member_ids: Optional[List[int]] = None
  updated_by: int
  
class ChannelMemberBase(BaseModel):
  """채널 멤버 기본 스키마"""
  id: int = Field(..., description="사용자 ID")
  role: str = Field("member", description="채널 내 역할")
  
class ChannelMemberCreate(ChannelMemberBase):
  """채널 멤버 추가 스키마"""
  pass

class ChannelMemberResponse(BaseModel):
  """채널 멤버 응답 스키마"""
  user: UserBrief
  role: str
  joined_at: datetime
  
class ChannelDetail(ChannelBase):
  """채널 응답 스키마"""
  project_id: str
  channel_id: str
  created_at: datetime
  updated_at: datetime
  created_by: Optional[int]
  updated_by: Optional[int]
  member_count: int = 0
  members: List[ChannelMemberResponse] = Field(default_factory=list)
  chats: Dict[str, Any] = Field(default_factory=dict)
  chats_count: int = 0
  
  def model_post_init(self, __context):
    self.chats = {
      "self": {
        "href": f"/api/v1/projects/{self.project_id}/chats?channel_id={self.channel_id}",
        "method": "GET",
        "title": "채널별 채팅 조회"
      }
    }
  
  class Config:
    from_attributes = True
    
class ChannelListResponse(BaseModel):
  """채널 목록 응답 스키마"""
  channels: List[ChannelDetail]
  total_count: int
  page: int
  limit: int