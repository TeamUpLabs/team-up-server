from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime
from src.api.v1.schemas.brief import UserBrief, TaskBrief

class MilestoneBase(BaseModel):
  title: str = Field(..., min_length=2, max_length=100)
  description: Optional[str] = None
  status: str = "not_started"  # not_started, in_progress, completed, on_hold
  priority: str = "medium"  # low, medium, high, urgent
  
  start_date: Optional[datetime] = None
  due_date: Optional[datetime] = None
  
  project_id: str
  tags: Optional[List[str]] = None
  

class MilestoneCreate(MilestoneBase):
  assignee_ids: Optional[List[int]] = None
  created_by: Optional[int] = None

class MilestoneUpdate(BaseModel):
  title: Optional[str] = Field(None, min_length=2, max_length=100)
  description: Optional[str] = None
  status: Optional[str] = None
  priority: Optional[str] = None
  progress: Optional[int] = Field(None, ge=0, le=100)
  
  start_date: Optional[datetime] = None
  due_date: Optional[datetime] = None
  
  assignee_ids: Optional[List[int]] = None
  tags: Optional[List[str]] = None
  
class MilestoneDetail(MilestoneBase):
  id: int
  created_at: datetime
  updated_at: datetime
  completed_at: Optional[datetime] = None
  progress: int
  
  # 관계
  # project: ProjectBrief
  assignees: List[UserBrief] = []
  creator: Optional[UserBrief] = None
  tasks: List[TaskBrief] = []
  
  # 통계
  task_count: int = len(tasks)
  completed_task_count: int = len([task for task in tasks if task.status == "completed"])
  
  class Config:
    from_attributes = True