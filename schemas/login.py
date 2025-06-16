from pydantic import BaseModel
from typing import List, Optional
from schemas.member import WorkingHoursInfo, SocialLinksInfo

class LoginForm(BaseModel):
    userEmail: str
    password: str

class Token(BaseModel):
    access_token: str
    token_type: str
    user_id: int
    user_name: str
    user_email: str
    
    
class SocialNewMember(BaseModel):
    name: str
    email: str
    password: Optional[str] = None
    role: str
    status: str
    contactNumber: str
    birthDate: str
    introduction: str
    workingHours: WorkingHoursInfo
    socialLinks: Optional[List[SocialLinksInfo]] = []
    languages: List[str]
    skills: List[str]
    lastLogin: str
    createdAt: str
    profileImage: Optional[str] = None
    github_id: Optional[str] = None
    isGithub: Optional[bool] = True
    github_access_token: Optional[str] = None
    google_id: Optional[str] = None
    isGoogle: Optional[bool] = False
    google_access_token: Optional[str] = None
    apple_id: Optional[str] = None
    isApple: Optional[bool] = False
    apple_access_token: Optional[str] = None
    signupMethod: Optional[str] = None