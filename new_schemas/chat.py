from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime

class ChatBase(BaseModel):
    """채팅 기본 스키마"""
    message: str = Field(..., min_length=1, max_length=2000, description="채팅 메시지")

class ChatCreate(ChatBase):
    """채팅 생성 스키마"""
    project_id: str = Field(..., min_length=6, max_length=6, description="프로젝트 ID")
    channel_id: str = Field(..., description="채널 ID")

class ChatUpdate(BaseModel):
    """채팅 수정 스키마"""
    message: str = Field(..., min_length=1, max_length=2000, description="채팅 메시지")

class UserInfo(BaseModel):
    """사용자 정보 스키마"""
    id: int
    name: str
    email: str
    profile_image: Optional[str] = None
    role: Optional[str] = None
    status: Optional[str] = None
    
    class Config:
        from_attributes = True

class ChatResponse(ChatBase):
    """채팅 응답 스키마"""
    id: int
    project_id: str
    channel_id: str
    user_id: int
    timestamp: datetime
    user: UserInfo

    class Config:
        from_attributes = True

class ChatListResponse(BaseModel):
    """채팅 목록 응답 스키마"""
    chats: List[ChatResponse]
    total_count: int
    page: int
    limit: int

class ChatSearchRequest(BaseModel):
    """채팅 검색 요청 스키마"""
    search_term: str = Field(..., min_length=1, description="검색어")
    limit: Optional[int] = Field(50, ge=1, le=100, description="검색 결과 수 제한")

class ChatDateRangeRequest(BaseModel):
    """채팅 날짜 범위 요청 스키마"""
    start_date: datetime = Field(..., description="시작 날짜")
    end_date: datetime = Field(..., description="종료 날짜")
    limit: Optional[int] = Field(100, ge=1, le=200, description="검색 결과 수 제한") 