from pydantic import BaseModel
from typing import Optional, List, Literal
from schemas.member import Member
from schemas.task import Task

class MileStoneBase(BaseModel):
  project_id: str
  title: str
  description: str
  startDate: str
  endDate: str
  assignee_id: List[int] = []
  status: Literal["not-started", "in-progress", "done"]
  priority: Literal["low", "medium", "high"]
  tags: Optional[List[str]] = []
  createdAt: str
  updatedAt: str
  createdBy: int
  updatedBy: int
class MileStoneCreate(MileStoneBase):
  pass
  class Config:
    from_attributes = True
    
class MileStone(MileStoneBase):
  id: int
  assignee: List[Member] = []
  subtasks: Optional[List[Task]] = []
  
  class Config:
    from_attributes = True
    
class MileStoneUpdate(BaseModel):
  title: Optional[str] = None
  description: Optional[str] = None
  startDate: Optional[str] = None
  endDate: Optional[str] = None
  assignee_id: Optional[List[int]] = None
  status: Optional[Literal["not-started", "in-progress", "done"]] = None
  priority: Optional[Literal["low", "medium", "high"]] = None
  tags: Optional[List[str]] = None
  updatedAt: Optional[str] = None
  updatedBy: Optional[int] = None
  class Config:
    from_attributes = True
