from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime
from .chat import ChatResponse

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
    name: Optional[str] = Field(None, min_length=1, max_length=100, description="채널 이름")
    description: Optional[str] = Field(None, max_length=1000, description="채널 설명")
    is_public: Optional[bool] = Field(None, description="공개 채널 여부")
    member_ids: Optional[List[int]] = Field(None, description="채널 멤버 ID 목록")

class ChannelMemberBase(BaseModel):
    """채널 멤버 기본 스키마"""
    id: int = Field(..., description="사용자 ID")
    role: str = Field("member", description="채널 내 역할")

class ChannelMemberCreate(ChannelMemberBase):
    """채널 멤버 추가 스키마"""
    pass

class ChannelMemberResponse(BaseModel):
    """채널 멤버 응답 스키마"""
    id: int
    name: str
    email: str
    profile_image: Optional[str]
    role: str
    joined_at: datetime

class ChannelResponse(ChannelBase):
    """채널 응답 스키마"""
    project_id: str
    channel_id: str
    created_at: datetime
    updated_at: datetime
    created_by: Optional[int]
    updated_by: Optional[int]
    member_count: Optional[int] = 0
    members: List[ChannelMemberResponse] = []
    chats: List[ChatResponse] = []
    chats_count: int = 0

    class Config:
        from_attributes = True

class ChannelListResponse(BaseModel):
    """채널 목록 응답 스키마"""
    channels: List[ChannelResponse]
    total_count: int
    page: int
    limit: int 