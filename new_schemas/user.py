from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field, EmailStr, validator, AnyUrl
from datetime import datetime
from new_schemas.notification import NotificationResponse

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

# 사용자 생성 스키마
class UserCreate(UserBase):
    password: str = Field(..., min_length=8)
    
    @validator('password')
    def validate_password(cls, v):
        if len(v) < 8:
            raise ValueError('비밀번호는 8자 이상이어야 합니다.')
        return v
    # 추가: 생성 시 함께 받을 수 있는 필드들
    collaboration_preferences: Optional[List["CollaborationPreferenceCreate"]] = None
    interests: Optional[List["UserInterestCreate"]] = None
    notification_settings: Optional[Dict[str, int]] = None
    social_links: Optional[List["UserSocialLinkCreate"]] = None

# 사용자 업데이트 스키마
class UserUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=2, max_length=100)
    profile_image: Optional[str] = None
    bio: Optional[str] = None
    role: Optional[str] = None
    languages: Optional[List[str]] = None
    phone: Optional[str] = None
    birth_date: Optional[str] = None
    notification_settings: Optional[Dict[str, int]] = None

# 사용자 응답 스키마
class UserBrief(BaseModel):
    """간략한 사용자 정보"""
    id: int
    name: str
    profile_image: Optional[str] = None
    role: Optional[str] = None
    status: Optional[str] = None
    
    class Config:
        from_attributes = True
        
# 간략한 프로젝트 정보
class ProjectBrief(BaseModel):
    id: str
    title: str
    status: str
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

# 기술 스택 스키마
class TechStackBrief(BaseModel):
    id: int
    name: str
    category: Optional[str] = None
    icon_url: Optional[str] = None
    
    class Config:
        from_attributes = True

# 사용자 기술 스택 스키마
class UserTechStackCreate(BaseModel):
    tech_stack_id: int
    proficiency_level: Optional[int] = None
    years_experience: Optional[int] = None

class UserTechStackResponse(BaseModel):
    tech_stack: TechStackBrief
    proficiency_level: Optional[int] = None
    years_experience: Optional[int] = None
    
    class Config:
        from_attributes = True

# 협업 선호도 스키마
class CollaborationPreferenceCreate(BaseModel):
    preference_type: str
    preference_value: str

class CollaborationPreferenceResponse(BaseModel):
    id: int
    preference_type: str
    preference_value: str
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

# 상세 사용자 응답 스키마
class UserDetail(UserBase):
    id: int
    status: str
    created_at: datetime
    updated_at: datetime
    last_login: Optional[datetime] = None
    auth_provider: str
    auth_provider_id: Optional[str] = None
    
    owned_projects: Optional[List[ProjectBrief]] = None
    projects: Optional[List[ProjectBrief]] = None
    assigned_tasks: Optional[List[TaskBrief]] = None
    created_tasks: Optional[List[TaskBrief]] = None
    assigned_milestones: Optional[List[MilestoneBrief]] = None
    created_milestones: Optional[List[MilestoneBrief]] = None
    
    tech_stacks: Optional[List[TechStackBrief]] = None
    collaboration_preferences: Optional[List[CollaborationPreferenceResponse]] = None
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
    user: UserBrief 

UserCreate.update_forward_refs() 