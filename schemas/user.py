from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field, EmailStr, validator, AnyUrl
from datetime import datetime
from schemas.notification import NotificationResponse

# 사용자 응답 스키마
class UserBrief(BaseModel):
    """간략한 사용자 정보"""
    id: int
    name: str
    email: str
    profile_image: Optional[str] = None
    role: Optional[str] = None
    status: Optional[str] = None
    
    class Config:
        from_attributes = True


# 간략한 프로젝트 정보
class ProjectBrief(BaseModel):
    id: str
    title: str
    description: Optional[str] = None
    status: str
    team_size: int
    tags: Optional[List[str]] = None
    members: Optional[List[UserBrief]] = None
    project_type: Optional[str] = None
    
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

# 협업 선호도 스키마
class CollaborationPreferenceCreate(BaseModel):
    collaboration_style: Optional[str] = None
    preferred_project_type: Optional[str] = None
    preferred_role: Optional[str] = None
    available_time_zone: Optional[str] = None
    work_hours_start: Optional[int] = None
    work_hours_end: Optional[int] = None
    preferred_project_length: Optional[str] = None
    
class CollaborationPreferenceUpdate(BaseModel):
    collaboration_style: Optional[str] = None
    preferred_project_type: Optional[str] = None
    preferred_role: Optional[str] = None
    available_time_zone: Optional[str] = None
    work_hours_start: Optional[int] = None
    work_hours_end: Optional[int] = None
    preferred_project_length: Optional[str] = None

class CollaborationPreferenceResponse(BaseModel):
    id: int
    collaboration_style: Optional[str] = None
    preferred_project_type: Optional[str] = None
    preferred_role: Optional[str] = None
    available_time_zone: Optional[str] = None
    work_hours_start: Optional[int] = None
    work_hours_end: Optional[int] = None
    preferred_project_length: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True

# 사용자 프로젝트 스키마
class UserProjectCreate(BaseModel):
    project_id: str
    role_description: Optional[str] = None
    contribution: Optional[str] = None

class UserProjectResponse(BaseModel):
    id: int
    project: ProjectBrief
    role_description: Optional[str] = None
    contribution: Optional[str] = None
    joined_at: datetime
    left_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True

# 사용자 기술 스택 스키마
class UserTechStackCreate(BaseModel):
    user_id: int
    tech: str
    level: int

class UserTechStackCreateForUser(BaseModel):
    tech: str
    level: int
    
class UserTechStackResponse(BaseModel):
    id: int
    user_id: int
    tech: str
    level: int
    created_at: datetime

# 사용자 관심분야 스키마
class UserInterestCreate(BaseModel):
    interest_category: str
    interest_name: str

class UserInterestResponse(BaseModel):
    id: int
    interest_category: str
    interest_name: str
    created_at: datetime
    
    class Config:
        from_attributes = True

# 알림 설정 스키마 (JSON 형태)
class NotificationSettingsUpdate(BaseModel):
    emailEnable: Optional[int] = 1
    taskNotification: Optional[int] = 1
    milestoneNotification: Optional[int] = 1
    scheduleNotification: Optional[int] = 1
    deadlineNotification: Optional[int] = 1
    weeklyReport: Optional[int] = 1
    pushNotification: Optional[int] = 1
    securityNotification: Optional[int] = 1

# 소셜 링크 스키마
class UserSocialLinkCreate(BaseModel):
    platform: str
    url: str

class UserSocialLinkResponse(BaseModel):
    id: int
    platform: str
    url: str
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True

# 기본 사용자 스키마
class UserBase(BaseModel):
    name: str = Field(..., min_length=2, max_length=100)
    email: EmailStr = Field(...)
    profile_image: Optional[str] = None
    bio: Optional[str] = None
    role: Optional[str] = None
    languages: Optional[List[str]] = None
    phone: Optional[str] = None
    birth_date: Optional[str] = None
    status: Optional[str] = "inactive"

# 사용자 생성 스키마
class UserCreate(UserBase):
    password: Optional[str] = Field(None, min_length=8)  # OAuth의 경우 비밀번호가 없을 수 있음
    
    @validator('password')
    def validate_password(cls, v):
        if v is not None and len(v) < 8:
            raise ValueError('비밀번호는 8자 이상이어야 합니다.')
        return v
    
    # OAuth 관련 필드
    auth_provider: Optional[str] = "local"  # local, github, google 등
    auth_provider_id: Optional[str] = None
    auth_provider_access_token: Optional[str] = None
    
    # 추가: 생성 시 함께 받을 수 있는 필드들
    collaboration_preference: Optional["CollaborationPreferenceCreate"] = None
    interests: Optional[List["UserInterestCreate"]] = None
    notification_settings: Optional[Dict[str, int]] = None
    social_links: Optional[List["UserSocialLinkCreate"]] = None
    tech_stacks: Optional[List["UserTechStackCreateForUser"]] = None

# 사용자 업데이트 스키마
class UserUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=2, max_length=100)
    profile_image: Optional[str] = None
    bio: Optional[str] = None
    role: Optional[str] = None
    status: Optional[str] = None
    languages: Optional[List[str]] = None
    phone: Optional[str] = None
    birth_date: Optional[str] = None
    notification_settings: Optional[Dict[str, int]] = None
    collaboration_preference: Optional[CollaborationPreferenceUpdate] = None
    auth_provider_access_token: Optional[str] = None
    last_login: Optional[datetime] = None


# 상세 사용자 응답 스키마
class UserDetail(UserBase):
    id: int
    created_at: datetime
    updated_at: datetime
    last_login: Optional[datetime] = None
    auth_provider: str
    auth_provider_id: Optional[str] = None
    
    projects: Optional[List[ProjectBrief]] = None
    
    collaboration_preference: Optional[CollaborationPreferenceResponse] = None
    tech_stacks: Optional[List[UserTechStackResponse]] = None
    interests: Optional[List[UserInterestResponse]] = None
    notification_settings: Optional[Dict[str, int]] = None
    social_links: Optional[List[UserSocialLinkResponse]] = None
    received_notifications: Optional[List[NotificationResponse]] = None
    
    class Config:
        from_attributes = True

# 인증 토큰 스키마
class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user_info: UserBrief

class OAuthLoginRequest(BaseModel):
    """OAuth 로그인 요청 스키마"""
    email: str
    name: str
    auth_provider: str = "github"
    auth_provider_id: str
    auth_provider_access_token: Optional[str] = None
    profile_image: Optional[str] = None
    bio: Optional[str] = None
    role: Optional[str] = None
    status: Optional[str] = "active"
    languages: Optional[List[str]] = None
    phone: Optional[str] = None
    birth_date: Optional[str] = None
    collaboration_preference: Optional[CollaborationPreferenceCreate] = None
    interests: Optional[List[UserInterestCreate]] = None
    notification_settings: Optional[Dict[str, int]] = None
    social_links: Optional[List[UserSocialLinkCreate]] = None
    tech_stacks: Optional[List[UserTechStackCreateForUser]] = None 

UserCreate.update_forward_refs()
OAuthLoginRequest.update_forward_refs() 