from pydantic import BaseModel
from typing import Optional

class CollaborationPreferenceBase(BaseModel):
    collaboration_style: Optional[str] = None
    preferred_project_type: Optional[str] = None
    preferred_role: Optional[str] = None
    available_time_zone: Optional[str] = None
    work_hours_start: Optional[int] = None
    work_hours_end: Optional[int] = None
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
