from typing import List, Optional
from pydantic import BaseModel, Field, EmailStr, validator
from datetime import datetime

# 기본 사용자 스키마
class UserBase(BaseModel):
    name: str = Field(..., min_length=2, max_length=100)
    email: EmailStr = Field(...)
    profile_image: Optional[str] = None
    bio: Optional[str] = None
    role: Optional[str] = None

# 사용자 생성 스키마
class UserCreate(UserBase):
    password: str = Field(..., min_length=8)
    
    @validator('password')
    def validate_password(cls, v):
        if len(v) < 8:
            raise ValueError('비밀번호는 8자 이상이어야 합니다.')
        return v

# 사용자 업데이트 스키마
class UserUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=2, max_length=100)
    profile_image: Optional[str] = None
    bio: Optional[str] = None
    role: Optional[str] = None

# 사용자 응답 스키마
class UserBrief(BaseModel):
    """간략한 사용자 정보"""
    id: int
    name: str
    profile_image: Optional[str] = None
    role: Optional[str] = None
    
    class Config:
        from_attributes = True
        
# 간략한 프로젝트 정보
class ProjectBrief(BaseModel):
    id: str
    title: str
    short_description: Optional[str] = None
    status: str
    cover_image: Optional[str] = None
    
    class Config:
        from_attributes = True
        
class TaskBrief(BaseModel):
    id: int
    title: str
    status: str
    priority: str
    due_date: Optional[datetime] = None
    
    class Config:
        from_attributes = True

class MilestoneBrief(BaseModel):
    id: int
    title: str
    status: str
    priority: str
    progress: int
    due_date: Optional[datetime] = None
    
    class Config:
        from_attributes = True

# 상세 사용자 응답 스키마
class UserDetail(UserBase):
    id: int
    status: str
    created_at: datetime
    updated_at: datetime
    last_login: Optional[datetime] = None
    
    owned_projects: Optional[List[ProjectBrief]] = None
    projects: Optional[List[ProjectBrief]] = None
    assigned_tasks: Optional[List[TaskBrief]] = None
    created_tasks: Optional[List[TaskBrief]] = None
    assigned_milestones: Optional[List[MilestoneBrief]] = None
    created_milestones: Optional[List[MilestoneBrief]] = None
    
    # 프로젝트 관계는 필요에 따라 추가
    
    class Config:
        from_attributes = True

# 인증 토큰 스키마
class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserBrief 