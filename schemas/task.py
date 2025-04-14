from pydantic import BaseModel
from typing import Optional, List
from schemas.member import Member

class SubTask(BaseModel):
  title: str
  completed: bool
  
class Comment(BaseModel):
  author_id: int
  content: str
  createdAt: str

class TaskBase(BaseModel):
  project_id: str
  title: str
  description: str
  status: str
  priority: str
  dueDate: str
  tags: Optional[List[str]] = []
  subtasks: Optional[List[SubTask]] = []
  comments: Optional[List[Comment]] = []
  createdAt: str
  updatedAt: str
  
class TaskCreate(TaskBase):
  assignee_id: List[int] = []

  class Config:
    from_attributes = True
        
class Task(TaskBase):
  id: int
  assignee: List[Member] = []
  
  class Config:
    from_attributes = True