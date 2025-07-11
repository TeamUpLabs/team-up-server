from pydantic import BaseModel, ConfigDict
from typing import Optional, List, Any

class SubTask(BaseModel):
  id: Optional[int] = None
  title: str
  completed: bool
  
class Comment(BaseModel):
  id: int
  author_id: int
  content: str
  createdAt: str

class TaskBase(BaseModel):
  project_id: str
  milestone_id: Optional[int] = None
  title: str
  description: str
  status: str
  priority: str
  startDate: str
  endDate: str
  tags: Optional[List[str]] = []
  subtasks: Optional[List[SubTask]] = []
  comments: Optional[List[Comment]] = []
  createdAt: str
  updatedAt: str
  createdBy: int
  updatedBy: int
  
class TaskCreate(TaskBase):
  assignee_id: List[int] = []

  model_config = ConfigDict(from_attributes=True)
        
class Task(TaskBase):
  id: int
  assignee_id: List[int] = []
  assignee: List[Any] = []  # Using Any to avoid circular import
  comments: List[Comment] | None

  model_config = ConfigDict(from_attributes=True)
  
class TaskStatusUpdate(BaseModel):
  status: str
  
  model_config = ConfigDict(from_attributes=True)
  
class TaskUpdate(BaseModel):
  title: Optional[str] = None
  description: Optional[str] = None
  status: Optional[str] = None
  priority: Optional[str] = None
  startDate: Optional[str] = None
  endDate: Optional[str] = None
  assignee_id: Optional[List[int]] = None
  tags: Optional[List[str]] = None
  subtasks: Optional[List[SubTask]] = None
  comments: Optional[List[Comment]] = None
  updatedAt: Optional[str] = None
  updatedBy: Optional[int] = None
  
  model_config = ConfigDict(from_attributes=True)

class UpdateSubTaskState(BaseModel):
  completed: bool
  
  model_config = ConfigDict(from_attributes=True)
