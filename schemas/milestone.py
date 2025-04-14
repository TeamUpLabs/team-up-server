from pydantic import BaseModel
from typing import Optional, List
from schemas.member import Member
from schemas.task import Task

class MileStoneBase(BaseModel):
  project_id: str
  title: str
  description: str
  startDate: str
  endDate: str
  status: str
  priority: str
  tags: Optional[List[str]] = []
  
class MileStoneCreate(MileStoneBase):
  assignee_id: List[int] = []
  
  class Config:
    from_attributes = True
    
class MileStone(MileStoneBase):
  id: int
  assignee: List[Member] = []
  subtasks: Optional[List[Task]] = []
  
  class Config:
    from_attributes = True
