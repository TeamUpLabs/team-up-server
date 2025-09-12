from typing import Optional, List, Dict
from pydantic import BaseModel, EmailStr, Field
from datetime import datetime
from api.v1.schemas.brief import UserBrief
from api.v1.schemas.notification_schema import NotificationCreate, NotificationUpdate
from api.v1.schemas.collaboration_preference_schema import CollaborationPreferenceCreate, CollaborationPreferenceUpdate
from api.v1.schemas.interest_schema import InterestCreate, InterestUpdate
from api.v1.schemas.tech_stack_schema import TechStackCreate, TechStackUpdate
from api.v1.schemas.social_link_schema import SocialLinkCreate, SocialLinkUpdate

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
  
  collaboration_preference: Optional[CollaborationPreferenceCreate] = None
  interests: Optional[List[InterestCreate]] = None
  notification_settings: Optional[NotificationCreate] = None
  social_links: Optional[List[SocialLinkCreate]] = None
  tech_stacks: Optional[List[TechStackCreate]] = None
  
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
  notification_settings: Optional[NotificationUpdate] = None
  social_links: Optional[List[SocialLinkUpdate]] = None
  tech_stacks: Optional[List[TechStackUpdate]] = None
  collaboration_preference: Optional[CollaborationPreferenceUpdate] = None
  interests: Optional[List[InterestUpdate]] = None
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
      "projects": f"{base_url}/projects",
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