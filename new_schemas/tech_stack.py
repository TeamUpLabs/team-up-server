from typing import List, Optional
from pydantic import BaseModel, Field
from datetime import datetime

# 기술 스택 기본 스키마
class TechStackBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=50)
    category: Optional[str] = None
    icon_url: Optional[str] = None

# 기술 스택 생성 스키마
class TechStackCreate(TechStackBase):
    pass

# 기술 스택 업데이트 스키마
class TechStackUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=50)
    category: Optional[str] = None
    icon_url: Optional[str] = None

# 기술 스택 응답 스키마
class TechStackDetail(TechStackBase):
    id: int
    created_at: datetime
    updated_at: datetime
    
    class Config:
        orm_mode = True 