from pydantic import BaseModel
from typing import Optional, List
from schemas.member import Member

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
    members: Optional[List[Member]] = []  # List of member IDs associated with the project

    class Config:
        from_attributes = True