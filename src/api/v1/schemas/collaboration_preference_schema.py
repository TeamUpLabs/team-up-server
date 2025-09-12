from pydantic import BaseModel, Field
from typing import Optional
from datetime import time

class CollaborationPreferenceBase(BaseModel):
    collaboration_style: Optional[str] = None
    preferred_project_type: Optional[str] = None
    preferred_role: Optional[str] = None
    available_time_zone: Optional[str] = None
    work_hours_start: Optional[int] = Field(None, ge=0, le=23)
    work_hours_end: Optional[int] = Field(None, ge=0, le=23)
    preferred_project_length: Optional[str] = None

class CollaborationPreferenceCreate(CollaborationPreferenceBase):
    pass

class CollaborationPreferenceUpdate(CollaborationPreferenceBase):
    pass

class CollaborationPreferenceInDB(CollaborationPreferenceBase):
    id: int
    user_id: int

    class Config:
        orm_mode = True

class CollaborationPreference(CollaborationPreferenceInDB):
    pass
