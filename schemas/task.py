from pydantic import BaseModel, ConfigDict
from typing import Optional, List, Any

class SubTask(BaseModel):
  title: str
  completed: bool
  
class Comment(BaseModel):
  author_id: int
  content: str
  createdAt: str

class TaskBase(BaseModel):
  project_id: str
  milestone_id: int
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

  model_config = ConfigDict(from_attributes=True)
        
class Task(TaskBase):
  id: int
  assignee_id: List[int] = []
  assignee: List[Any] = []  # Using Any to avoid circular import

  model_config = ConfigDict(from_attributes=True)
  
class TaskStatusUpdate(BaseModel):
  status: str
  
  model_config = ConfigDict(from_attributes=True)