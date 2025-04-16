from pydantic import BaseModel, ConfigDict
from typing import Optional, List, Any

class LanguageInfo(BaseModel):
    name: str
    level: str

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
    role: str
    department: str
    status: str
    lastLogin: Optional[str] = None
    createdAt: Optional[str] = None
    skills: Optional[List[str]] = []
    projects: Optional[List[str]] = []
    profileImage: Optional[str] = None
    contactNumber: Optional[str] = None
    birthDate: Optional[str] = None
    introduction: Optional[str] = None
    workingHours: Optional[WorkingHoursInfo] = None
    languages: Optional[List[LanguageInfo]] = []
    socialLinks: Optional[List[SocialLinksInfo]] = []

# Schema for creating a new member
class MemberCreate(MemberBase):
    password: str  # Password only required when creating

    model_config = ConfigDict(from_attributes=True)

# Schema for returning member data
class Member(MemberBase):
    id: int  # ID included in response but not in create request
    currentTask: Optional[List[Any]] = []  # Using Any to avoid circular import

    model_config = ConfigDict(from_attributes=True)