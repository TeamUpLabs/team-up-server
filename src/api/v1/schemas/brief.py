from typing import Optional, List
from datetime import datetime
from pydantic import BaseModel

class UserBrief(BaseModel):
  """간략한 사용자 정보"""
  id: int
  name: str
  email: str
  profile_image: Optional[str] = None
  role: Optional[str] = None
  status: Optional[str] = None
  created_at: datetime
  updated_at: datetime
  
  class Config:
    from_attributes = True

class ProjectBrief(BaseModel):
  """간략한 프로젝트 정보"""
  id: str
  title: str
  description: Optional[str] = None
  status: str
  team_size: int
  tags: Optional[List[str]] = None
  members: Optional[List[UserBrief]] = None
  project_type: Optional[str] = None
  
  class Config:
    from_attributes = True
    
class TaskBrief(BaseModel):
  """간략한 업무 정보"""
  id: int
  title: str
  status: str
  priority: str
  due_date: Optional[datetime] = None
  
  class Config:
    from_attributes = True
  
class MilestoneBrief(BaseModel):
  """간략한 마일스톤 정보"""
  id: int
  title: str
  status: str
  due_date: Optional[datetime] = None
  
  class Config:
    from_attributes = True