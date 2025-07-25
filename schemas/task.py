from typing import List, Optional
from pydantic import BaseModel, Field, validator
from datetime import datetime
from .user import UserBrief
# from .project import ProjectBrief

# 마일스톤 간략 정보 (순환 참조 방지)
class MilestoneBrief(BaseModel):
    id: int
    title: str
    status: str
    
    class Config:
        from_attributes = True

# 댓글 스키마
class CommentBase(BaseModel):
    content: str = Field(..., min_length=1, max_length=1000)

class CommentCreate(CommentBase):
    pass

class CommentUpdate(BaseModel):
    content: str = Field(..., min_length=1, max_length=1000)

class CommentDetail(CommentBase):
    id: int
    created_at: datetime
    updated_at: datetime
    created_by: Optional[int] = None
    creator: Optional[UserBrief] = None
    
    class Config:
        from_attributes = True

# 하위 업무 스키마
class SubTaskBase(BaseModel):
    title: str = Field(..., min_length=2, max_length=100)
    is_completed: bool = False

class SubTaskCreate(SubTaskBase):
    pass

class SubTaskUpdate(BaseModel):
    title: Optional[str] = Field(None, min_length=2, max_length=100)
    is_completed: Optional[bool] = None

class SubTaskDetail(SubTaskBase):
    id: int
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True

# 업무 기본 스키마
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

# 업무 생성 스키마
class TaskCreate(TaskBase):
    @validator("milestone_id", pre=True)
    def empty_str_to_none(cls, v):
        if v == 0:
            return None
        return v
    assignee_ids: Optional[List[int]] = None
    created_by: Optional[int] = None
    subtasks: Optional[List[SubTaskCreate]] = None

# 업무 업데이트 스키마
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

# 업무 간략 정보
class TaskBrief(BaseModel):
    id: int
    title: str
    status: str
    priority: str
    due_date: Optional[datetime] = None
    
    class Config:
        from_attributes = True

# 업무 상세 정보
class TaskDetail(TaskBase):
    id: int
    created_at: datetime
    updated_at: datetime
    completed_at: Optional[datetime] = None
    actual_hours: Optional[float] = None
    
    # 관계
    # project: ProjectBrief는 순환 참조 문제로 제외
    milestone: Optional[MilestoneBrief] = None
    assignees: List[UserBrief] = []
    creator: Optional[UserBrief] = None
    
    # 하위 업무
    subtasks: List[SubTaskDetail] = []
    
    # 댓글
    comments: List[CommentDetail] = []
    
    class Config:
        from_attributes = True 