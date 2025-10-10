from pydantic import BaseModel, Field
from typing import Optional

class InterestBase(BaseModel):
    interest_category: str = Field(..., max_length=50)
    interest_name: str = Field(..., max_length=100)

class InterestCreate(InterestBase):
    pass

class InterestUpdate(InterestBase):
    interest_category: Optional[str] = Field(None, max_length=50)
    interest_name: Optional[str] = Field(None, max_length=100)

class InterestInDB(InterestBase):
    id: int
    user_id: int

    class Config:
        from_attributes = True

class Interest(InterestInDB):
    pass
