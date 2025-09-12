from pydantic import BaseModel, Field
from typing import Optional

class TechStackBase(BaseModel):
    tech: str = Field(..., max_length=100)
    level: Optional[int] = Field(None, ge=1, le=5)

class TechStackCreate(TechStackBase):
    pass

class TechStackUpdate(TechStackBase):
    tech: Optional[str] = Field(None, max_length=100)

class TechStackInDB(TechStackBase):
    id: int
    user_id: int

    class Config:
        orm_mode = True

class TechStack(TechStackInDB):
    pass
