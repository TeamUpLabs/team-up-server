from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime
from api.v1.schemas.brief import UserBrief, TaskBrief, MilestoneBrief

class ProjectBase(BaseModel):
  title: str = Field(..., min_length=2, max_length=100)
  description: Optional[str] = None
  status: str = "planning"  # planning, in_progress, completed, on_hold
  visibility: str = "public"  # public, private
  team_size: int
  project_type: Optional[str] = None
  created_at: datetime
  updated_at: datetime
  start_date: Optional[datetime] = None
  end_date: Optional[datetime] = None
  tags: Optional[List[str]] = None
  location: Optional[str] = None
  github_url: Optional[str] = None
    
class ProjectCreate(ProjectBase):
  id: str = Field(..., min_length=6, max_length=6)
  owner_id: int
  member_ids: Optional[List[int]] = None
    
class ProjectUpdate(BaseModel):
  title: Optional[str] = Field(None, min_length=2, max_length=100)
  description: Optional[str] = None
  status: Optional[str] = None
  team_size: Optional[int] = None
  visibility: Optional[str] = None
  project_type: Optional[str] = None
  start_date: Optional[datetime] = None
  end_date: Optional[datetime] = None
  tags: Optional[List[str]] = None
  location: Optional[str] = None
  github_url: Optional[str] = None
  
class ProjectMember(BaseModel):
  user: UserBrief
  role: Optional[str] = None
  joined_at: datetime
  
  def __init__(self, **data):
    super().__init__(**data)
    self.role = "leader" if data.get("is_leader") else "manager" if data.get("is_manager") else "member"
  
  class Config:
      from_attributes = True
      
class ProjectStats(BaseModel):
  total_tasks: int = 0
  completed_tasks: int = 0
  total_milestones: int = 0
  completed_milestones: int = 0
  progress_percentage: float = 0.0
  days_remaining: Optional[int] = None
  
  class Config:
    from_attributes = True
      
class ProjectDetail(ProjectBase):
  id: str
  completed_at: Optional[datetime] = None
  
  owner: Optional[UserBrief] = None
  members: Optional[List[ProjectMember]] = []
  tasks: Optional[List[TaskBrief]] = []
  milestones: Optional[List[MilestoneBrief]] = []
  # participation_requests: Optional[List[ParticipationRequestResponse]] = []
  # schedules: Optional[List[ScheduleResponse]] = []
  # channels: Optional[List[ChannelResponse]] = []
  # whiteboards: Optional[List[WhiteBoardDetail]] = []
  
  stats: Optional[ProjectStats] = None
  
  class Config:
    from_attributes = True