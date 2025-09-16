from pydantic import BaseModel, Field, validator
from typing import Optional, List
from datetime import datetime
from api.v1.schemas.brief import UserBrief, MilestoneBrief

class CommentBase(BaseModel):
  content: str = Field(..., min_length=2, max_length=100)
  
class CommentCreate(CommentBase):
  pass

class CommentUpdate(CommentBase):
  content: Optional[str] = None
  
class CommentDetail(CommentBase):
  id: int
  created_at: datetime
  updated_at: datetime
  created_by: Optional[int] = None
  creator: Optional[UserBrief] = None
  
  class Config:
    from_attributes = True
  
class SubTaskBase(BaseModel):
  title: str = Field(..., min_length=2, max_length=100)
  is_completed: bool = False
  
class SubTaskCreate(SubTaskBase):
  pass

class SubTaskUpdate(SubTaskBase):
  title: Optional[str] = None
  is_completed: Optional[bool] = None

class SubTaskDetail(SubTaskBase):
  id: int
  created_at: datetime
  updated_at: datetime
  
  class Config:
    from_attributes = True

class TaskBase(BaseModel):
  title: str = Field(..., min_length=2, max_length=100)
  description: Optional[str] = None
  status: str = "not_started"  # not_started, in_progress, completed, on_hold
  priority: str = "medium"  # low, medium, high, urgent
  estimated_hours: Optional[float] = None
  
  start_date: Optional[datetime] = None
  due_date: Optional[datetime] = None
  
  project_id: str
  milestone_id: Optional[int] = None
  
class TaskCreate(TaskBase):
  @validator("milestone_id", pre=True)
  def empty_str_to_none(cls, v):
    if v == 0:
      return None
    return v
    
  assignee_ids: Optional[List[int]] = None
  created_by: Optional[int] = None
  subtasks: Optional[List[SubTaskCreate]] = None
    
class TaskUpdate(BaseModel):
  title: Optional[str] = Field(None, min_length=2, max_length=100)
  description: Optional[str] = None
  status: Optional[str] = None
  priority: Optional[str] = None
  estimated_hours: Optional[float] = None
  actual_hours: Optional[float] = None
  
  start_date: Optional[datetime] = None
  due_date: Optional[datetime] = None
  
  milestone_id: Optional[int] = None
  assignee_ids: Optional[List[int]] = None
  
class TaskDetail(TaskBase):
  id: int
  created_at: datetime
  updated_at: datetime
  completed_at: Optional[datetime] = None
  actual_hours: Optional[float] = None
  
  # 관계
  milestone: Optional[MilestoneBrief] = None
  assignees: List[UserBrief] = []
  creator: Optional[UserBrief] = None
  
  # 하위 업무
  subtasks: List[SubTaskDetail] = []
  
  # 댓글
  comments: List[CommentDetail] = []
  
  class Config:
    from_attributes = True