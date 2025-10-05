from pydantic import BaseModel
from typing import Optional

class TechStackBase(BaseModel):
    tech: str
    level: Optional[int]

class TechStackCreate(TechStackBase):
    pass

class TechStackUpdate(TechStackBase):
    tech: Optional[str]

class TechStackInDB(TechStackBase):
    id: int
    user_id: int

    class Config:
        orm_mode = True

class TechStack(TechStackInDB):
    pass
