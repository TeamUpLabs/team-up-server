from typing import Optional, List, Dict
from pydantic import BaseModel, EmailStr, Field
from datetime import datetime
from api.v1.schemas.brief import UserBrief
from api.v1.schemas.user.notification_schema import NotificationCreate, NotificationUpdate
from api.v1.schemas.user.collaboration_preference_schema import CollaborationPreferenceCreate, CollaborationPreferenceUpdate
from api.v1.schemas.user.interest_schema import InterestCreate, InterestUpdate
from api.v1.schemas.user.tech_stack_schema import TechStackCreate, TechStackUpdate
from api.v1.schemas.user.social_link_schema import SocialLinkCreate, SocialLinkUpdate

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
  auth: Dict = {}
  notification_settings: Optional[Dict[str, int]] = None
    
  # Related resource URLs
  links: Dict = {}
  
  class Config:
    from_attributes = True
    
  def __init__(self, **data):
    super().__init__(**data)
    
    self.auth = {
      "provider": data.get("auth_provider"),
      "provider_id": data.get("auth_provider_id"),
      "provider_access_token": data.get("auth_provider_access_token")
    }
    
    # Generate related resource URLs
    base_url = f"/api/v1/users/{self.id}"
    self.links = {
      "self": {
        "href": f"{base_url}",
        "method": "GET",
        "title": "자신의 사용자 정보 조회"
      },
      "projects": {
        "my": {
          "href": f"/api/v1/projects?user_id={self.id}",
          "method": "GET",
          "title": "자신이 참여한 프로젝트 조회"
        },
        "exclude_me": {
          "href": f"/api/v1/projects/exclude?user_id={self.id}",
          "method": "GET",
          "title": "자신이 참여하지 않은 프로젝트 조회"
        }
      },
      "collaboration_preferences": {
        "href": f"{base_url}/collaboration-preferences",
        "method": "GET",
        "title": "자신의 협업 선호도 조회"
      },
      "tech_stacks": {
        "href": f"{base_url}/tech-stacks",
        "method": "GET",
        "title": "자신의 기술 스택 조회"
      },
      "interests": {
        "href": f"{base_url}/interests",
        "method": "GET",
        "title": "자신의 관심사 조회"
      },
      "social_links": {
        "href": f"{base_url}/social-links",
        "method": "GET",
        "title": "자신의 소셜 링크 조회"
      },
      "notifications": {
        "href": f"{base_url}/notifications",
        "method": "GET",
        "title": "자신의 알림 조회"
      },
      "sessions": {
        "href": f"{base_url}/sessions",
        "method": "GET",
        "title": "자신의 세션 조회"
      },
    }
    
class Token(BaseModel):
  access_token: str
  token_type: str = "bearer"
  user_info: UserBrief