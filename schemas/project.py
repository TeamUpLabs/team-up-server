from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
from datetime import datetime
from .user import UserBrief
from .task import TaskDetail
from .milestone import MilestoneDetail
from .participation_request import ParticipationRequestResponse
from .schedule import ScheduleResponse
from .channel import ChannelResponse
from .user import UserDetail

# 프로젝트 기본 스키마
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

# 프로젝트 생성 스키마
class ProjectCreate(ProjectBase):
    id: str = Field(..., min_length=6, max_length=6)
    owner_id: int
    member_ids: Optional[List[int]] = None

# 프로젝트 업데이트 스키마
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
    updated_at: datetime

# 프로젝트 멤버 스키마
class ProjectMember(BaseModel):
    user: UserDetail
    role: Optional[str] = None
    is_leader: bool
    is_manager: bool
    joined_at: datetime
    
    class Config:
        from_attributes = True

# 간략한 프로젝트 정보
class ProjectBrief(BaseModel):
    id: str
    title: str
    status: str
    team_size: int
    
    class Config:
        from_attributes = True

# 상세 프로젝트 정보
class ProjectDetail(ProjectBase):
    id: str
    completed_at: Optional[datetime] = None
    
    # 관계
    owner: Optional[UserBrief] = None
    members: Optional[List[ProjectMember]] = []
    tasks: List[TaskDetail] = []
    milestones: List[MilestoneDetail] = []
    participation_requests: List[ParticipationRequestResponse] = []
    schedules: List[ScheduleResponse] = []
    channels: List[ChannelResponse] = []
    
    # 통계
    task_count: Optional[int] = len(tasks)
    completed_task_count: Optional[int] = len([task for task in tasks if task.status == "completed"])
    milestone_count: Optional[int] = len(milestones)
    completed_milestone_count: Optional[int] = len([milestone for milestone in milestones if milestone.status == "completed"])
    participation_request_total_count: Optional[int] = len(participation_requests)
    participation_request_accepted_count: Optional[int] = len([request for request in participation_requests if request.status == "accepted"])
    participation_request_rejected_count: Optional[int] = len([request for request in participation_requests if request.status == "rejected"])
    participation_request_pending_count: Optional[int] = len([request for request in participation_requests if request.status == "pending"])
    schedule_count: Optional[int] = len(schedules)
    channel_count: Optional[int] = len(channels)
    chat_count: Optional[int] = len([chat for channel in channels for chat in channel.chats])
    class Config:
        from_attributes = True

# 프로젝트 통계 스키마
class ProjectStats(BaseModel):
    total_tasks: int = 0
    completed_tasks: int = 0
    total_milestones: int = 0
    completed_milestones: int = 0
    progress_percentage: float = 0.0
    days_remaining: Optional[int] = None
    
    class Config:
        from_attributes = True 