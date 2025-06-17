from pydantic import BaseModel
from typing import Optional, List
from schemas.member import Member
from schemas.task import Task
from schemas.milestone import MileStone
from schemas.schedule import Schedule
from schemas.channel import Channel

class ProjectBase(BaseModel):
    id: str
    title: str
    description: str
    status: str
    roles: Optional[List[str]] = []
    techStack: Optional[List[str]] = []
    startDate: str
    endDate: str
    teamSize: int
    location: str
    projectType: str
    createdAt: str
    github_repo_url: Optional[str] = None
    
    
class ProjectCreate(ProjectBase):
    leader_id: int
    manager_id: List[int] = []
  
    class Config:
      from_attributes = True
        
class Project(ProjectBase):
    members: Optional[List[Member]] = []
    tasks: Optional[List[Task]] = []
    milestones: Optional[List[MileStone]] = []
    leader: Optional[Member] = None
    manager: Optional[List[Member]] = []
    participationRequestMembers: Optional[List[Member]] = []
    schedules: Optional[List[Schedule]] = []
    channels: Optional[List[Channel]] = []
    class Config:
        from_attributes = True
        
class ProjectMemberAdd(BaseModel):
    member_id: int
    
    class Config:
        from_attributes = True
        
class ProjectMemberScout(BaseModel):
    sender_id: int
    receiver_id: int
    
    class Config:
        from_attributes = True
        
class ProjectInfoUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    status: Optional[str] = None
    roles: Optional[List[str]] = []
    techStack: Optional[List[str]] = []
    startDate: Optional[str] = None
    endDate: Optional[str] = None
    teamSize: Optional[int] = None
    location: Optional[str] = None
    projectType: Optional[str] = None
    status: Optional[str] = None
    github_repo_url: Optional[str] = None
    class Config:
        from_attributes = True
        
class ProjectMemberPermission(BaseModel):
    permission: str
    
    class Config:
        from_attributes = True
        
        