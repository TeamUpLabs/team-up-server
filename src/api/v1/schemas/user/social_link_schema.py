from pydantic import BaseModel, Field
from typing import Optional

class SocialLinkBase(BaseModel):
    platform: str = Field(..., max_length=50)
    url: str = Field(..., max_length=255)

class SocialLinkCreate(SocialLinkBase):
    pass

class SocialLinkUpdate(SocialLinkBase):
    platform: Optional[str] = Field(None, max_length=50)
    url: Optional[str] = Field(None, max_length=255)

class SocialLinkInDB(SocialLinkBase):
    id: int
    user_id: int

    class Config:
        orm_mode = True

class SocialLink(SocialLinkInDB):
    pass
