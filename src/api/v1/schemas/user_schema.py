from typing import Optional, List, Dict
from pydantic import BaseModel, EmailStr, Field
from datetime import datetime
from api.v1.schemas.brief import UserBrief

class CollaborationPreference(BaseModel):
  collaboration_style: Optional[str] = None
  preferred_project_type: Optional[str] = None
  preferred_role: Optional[str] = None
  available_time_zone: Optional[str] = None
  work_hours_start: Optional[int] = None
  work_hours_end: Optional[int] = None
  preferred_project_length: Optional[str] = None
    
class CollaborationPreferenceResponse(CollaborationPreference):
  id: int
  created_at: datetime
  updated_at: datetime
  
  class Config:
    from_attributes = True
    
class UserProject(BaseModel):
  project_id: str
  role_description: Optional[str] = None
  contribution: Optional[str] = None
  
class UserProjectResponse(UserProject):
  id: int
  joined_at: datetime
  left_at: Optional[datetime] = None
  
  class Config:
    from_attributes = True
    
class UserTechStack(BaseModel):
  tech: str
  level: int

class UserTechStackResponse(UserTechStack):
  id: int
  created_at: datetime
  updated_at: datetime
  
  class Config:
    from_attributes = True
    
class UserInterest(BaseModel):
  interest_category: str
  interest_name: str

class UserInterestResponse(UserInterest):
  id: int
  created_at: datetime
  updated_at: datetime
  
  class Config:
    from_attributes = True
    
class NotificationSettings(BaseModel):
  emailEnable: Optional[int] = 1
  taskNotification: Optional[int] = 1
  milestoneNotification: Optional[int] = 1
  scheduleNotification: Optional[int] = 1
  deadlineNotification: Optional[int] = 1
  weeklyReport: Optional[int] = 1
  pushNotification: Optional[int] = 1
  securityNotification: Optional[int] = 1

class UserSocialLink(BaseModel):
  platform: str
  url: str

class UserSocialLinkResponse(UserSocialLink):
  id: int
  created_at: datetime
  updated_at: datetime
  
  class Config:
    from_attributes = True
    
class UserSessionResponse(BaseModel):
  id: int
  session_id: str
  user_id: int
  device_id: Optional[str] = None
  user_agent: Optional[str] = None
  geo_location: Optional[str] = None
  ip_address: Optional[str] = None
  device: Optional[str] = None
  device_type: Optional[str] = None
  os: Optional[str] = None
  browser: Optional[str] = None
  last_active_at: datetime
  is_current: bool
  created_at: datetime
  updated_at: datetime
  
  class Config:
    from_attributes = True

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
  
  
class UserCreate(UserBase):
  password: Optional[str] = Field(None, min_length=8)  # OAuth의 경우 비밀번호가 없을 수 있음
  
  auth_provider: Optional[str] = "local"  # local, github, google
  auth_provider_id: Optional[str] = None
  auth_provider_access_token: Optional[str] = None
  
  collaboration_preference: Optional[CollaborationPreference] = None
  interests: Optional[List[UserInterest]] = None
  notification_settings: Optional[NotificationSettings] = None
  social_links: Optional[List[UserSocialLink]] = None
  tech_stacks: Optional[List[UserTechStack]] = None
  
class UserUpdate(BaseModel):
  name: Optional[str] = Field(None, min_length=2, max_length=100)
  email: Optional[EmailStr] = Field(None)
  profile_image: Optional[str] = None
  bio: Optional[str] = None
  role: Optional[str] = None
  languages: Optional[List[str]] = None
  phone: Optional[str] = None
  birth_date: Optional[str] = None
  status: Optional[str] = None
  notification_settings: Optional[NotificationSettings] = None
  social_links: Optional[List[UserSocialLink]] = None
  tech_stacks: Optional[List[UserTechStack]] = None
  collaboration_preference: Optional[CollaborationPreference] = None
  interests: Optional[List[UserInterest]] = None
  auth_provider_access_token: Optional[str] = None
  last_login: Optional[datetime] = None
  
class UserDetail(UserBase):
  id: int
  created_at: datetime
  updated_at: datetime
  last_login: Optional[datetime] = None
  auth_provider: str
  auth_provider_id: Optional[str] = None
  auth_provider_access_token: Optional[str] = None
  projects: Optional[str] = None
  notification_settings: Optional[Dict[str, int]] = None
    
  # Related resource URLs
  urls: dict = {}
  
  class Config:
    from_attributes = True
    
  def __init__(self, **data):
    super().__init__(**data)
    # Generate related resource URLs
    base_url = f"/api/v1/users/{self.id}"
    self.urls = {
      "self": f"{base_url}",
      "collaboration_preferences": f"{base_url}/collaboration-preferences",
      "tech_stacks": f"{base_url}/tech-stacks",
      "interests": f"{base_url}/interests",
      "social_links": f"{base_url}/social-links",
      "notifications": f"{base_url}/notifications",
      "sessions": f"{base_url}/sessions"
    }
    
class Token(BaseModel):
  access_token: str
  token_type: str = "bearer"
  user_info: UserBrief