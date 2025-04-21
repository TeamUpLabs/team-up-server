from pydantic import BaseModel, ConfigDict
from typing import Optional, List, Any

class WorkingHoursInfo(BaseModel):
    start: str
    end: str
    timezone: str

class SocialLinksInfo(BaseModel):
    name: str
    url: str

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
    workingHours: WorkingHoursInfo
    languages: Optional[List[str]] = []
    socialLinks: Optional[List[SocialLinksInfo]] = []

# Schema for creating a new member
class MemberCreate(MemberBase):
    model_config = ConfigDict(from_attributes=True)

# Schema for returning member data
class Member(MemberBase):
    id: int  # ID included in response but not in create request
    currentTask: Optional[List[Any]] = []  # Using Any to avoid circular import
    projectDetails: Optional[List[Any]] = []
    
    model_config = ConfigDict(from_attributes=True)