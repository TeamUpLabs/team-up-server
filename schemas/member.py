from pydantic import BaseModel, ConfigDict
from typing import Optional, List, Any, Literal
from datetime import datetime

class WorkingHoursInfo(BaseModel):
    start: str
    end: str
    timezone: str

class SocialLinksInfo(BaseModel):
    name: str
    url: str
    
class NotificationInfo(BaseModel):
    id: int
    title: str
    message: str
    timestamp: str
    isRead: bool
    type: Literal["info", "message", "task", "milestone", "chat", "scout", "project", "schedule"]
    sender_id: int
    receiver_id: int
    project_id: Optional[str] = None
    result: Optional[Literal["accept", "reject"]] = None

# Base class for shared attributes
class MemberBase(BaseModel):
    name: str
    email: str
    password: Optional[str] = None
    role: str
    status: str
    lastLogin: Optional[str] = None
    createdAt: Optional[str] = None
    skills: Optional[List[str]] = []
    projects: Optional[List[str]] = []
    profileImage: Optional[str] = None
    contactNumber: str
    birthDate: Optional[str] = None
    introduction: Optional[str] = None
    workingHours: Optional[WorkingHoursInfo] = None
    languages: Optional[List[str]] = []
    socialLinks: Optional[List[SocialLinksInfo]] = []
    isGithub: Optional[bool] = False
    github_id: Optional[str] = None
    github_access_token: Optional[str] = None
    isGoogle: Optional[bool] = False
    google_id: Optional[str] = None
    google_access_token: Optional[str] = None
    isApple: Optional[bool] = False
    apple_id: Optional[str] = None
    apple_access_token: Optional[str] = None
    signupMethod: Optional[str] = None
# Schema for creating a new member
class MemberCreate(BaseModel):
    name: str
    email: str
    password: str
    role: str
    status: str
    contactNumber: str
    birthDate: str
    introduction: str
    workingHours: WorkingHoursInfo
    languages: List[str]
    skills: List[str]
    lastLogin: str
    createdAt: str
    profileImage: Optional[str] = None
    signupMethod: Optional[str] = None
    
    model_config = ConfigDict(from_attributes=True)

# Schema for returning member data
class Member(MemberBase):
    id: int  # ID included in response but not in create request
    currentTask: Optional[List[Any]] = []  # Using Any to avoid circular import
    projectDetails: Optional[List[Any]] = []
    notification: Optional[List[NotificationInfo]] = []
    
    model_config = ConfigDict(from_attributes=True)
    
class MemberCheck(BaseModel):
    email: str
    
    class Config:
        from_attributes = True

class MemberUpdate(BaseModel):
    name: Optional[str] = None
    email: Optional[str] = None
    status: Optional[str] = None
    role: Optional[str] = None
    contactNumber: Optional[str] = None
    birthDate: Optional[str] = None
    introduction: Optional[str] = None
    skills: Optional[List[str]] = []
    languages: Optional[List[Any]] = []
    workingHours: Optional[WorkingHoursInfo] = None
    socialLinks: Optional[List[SocialLinksInfo]] = []
    notification: Optional[List[NotificationInfo]] = []
    lastLogin: Optional[str] = None
    
    class Config:
        from_attributes = True
        
class NotificationUpdate(BaseModel):
    title: Optional[str] = None
    message: Optional[str] = None
    timestamp: Optional[str] = None
    isRead: Optional[bool] = None
    type: Optional[Literal["info", "message", "task", "milestone", "chat", "scout", "project"]] = None
    result: Optional[Literal["accept", "reject"]] = None
    
    class Config:
        from_attributes = True