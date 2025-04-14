from pydantic import BaseModel
from typing import Optional, List
from schemas.member import Member
from schemas.task import Task

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
    
class ProjectCreate(ProjectBase):
    pass
  
    class Config:
      from_attributes = True
        
class Project(ProjectBase):
    members: Optional[List[Member]] = []
    tasks: Optional[List[Task]] = []

    class Config:
        from_attributes = True