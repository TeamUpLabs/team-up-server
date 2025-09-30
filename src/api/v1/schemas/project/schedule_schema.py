from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime
from api.v1.schemas.brief import UserBrief

class ScheduleBase(BaseModel):
  type: str  # meeting, event
  title: str
  description: Optional[str] = None
  where: str
  link: Optional[str] = None
  start_time: str
  end_time: str
  status: str  # not-started, in-progress, done
  memo: Optional[str] = None
  
class ScheduleCreate(ScheduleBase):
  project_id: str
  assignee_ids: Optional[List[int]] = None
  created_at: Optional[datetime] = None
  updated_at: Optional[datetime] = None
  created_by: Optional[int] = None
  updated_by: Optional[int] = None
  
class ScheduleUpdate(BaseModel):
  type: Optional[str] = None
  title: Optional[str] = None
  description: Optional[str] = None
  where: Optional[str] = None
  link: Optional[str] = None
  start_time: Optional[str] = None
  end_time: Optional[str] = None
  status: Optional[str] = None
  memo: Optional[str] = None
  assignee_ids: Optional[List[int]] = None
  
class ScheduleDetail(ScheduleBase):
  id: int
  project_id: str
  created_at: datetime
  updated_at: datetime
  assignees: Optional[List[UserBrief]] = None
  creator: Optional[UserBrief] = None
  updater: Optional[UserBrief] = None
  
  class Config:
    from_attributes = True