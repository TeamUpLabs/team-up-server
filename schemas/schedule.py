from pydantic import BaseModel, ConfigDict
from typing import Optional, List, Any

class ScheduleBase(BaseModel):
    project_id: str
    type: str
    title: str
    description: str
    where: str
    assignee_id: List[int]
    start_time: str
    end_time: str
    status: str
    created_at: str
    updated_at: str
    created_by: int
    updated_by: int

    model_config = ConfigDict(from_attributes=True)

class ScheduleCreate(ScheduleBase):
    pass

class Schedule(ScheduleBase):
    id: int
    assignee_id: List[int] = []
    assignee: List[Any] = []

    model_config = ConfigDict(from_attributes=True)
    
class ScheduleUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    where: Optional[str] = None
    assignee_id: Optional[List[int]] = None
    status: Optional[str] = None
    start_time: Optional[str] = None
    end_time: Optional[str] = None
    updated_at: Optional[str] = None
    updated_by: Optional[int] = None

    model_config = ConfigDict(from_attributes=True)
