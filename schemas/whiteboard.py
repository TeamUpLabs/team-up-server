from pydantic import BaseModel
from typing import Optional, List
from schemas.user import UserBrief
from datetime import datetime

class AttachmentBase(BaseModel):
    filename: str
    file_url: str

class AttachmentCreate(AttachmentBase):
    pass

class Attachment(AttachmentBase):
    id: int
    document_id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class DocumentBase(BaseModel):
    content: str
    tags: Optional[dict] = None
    attachments: List[AttachmentCreate] = []

class DocumentCreate(DocumentBase):
    pass

class Document(DocumentBase):
    id: int
    whiteboard_id: int
    created_at: datetime
    updated_at: datetime
    attachments: List[Attachment] = []

    class Config:
        from_attributes = True

class WhiteBoardBase(BaseModel):
    type: str
    project_id: str
    title: str
    
class WhiteBoardCreate(WhiteBoardBase):
    created_by: int
    updated_by: int
    attachments: List[AttachmentCreate] = []
    
class WhiteBoardUpdate(BaseModel):
    id: int
    title: Optional[str] = None
    updated_by: int
    
class WhiteBoardDetail(WhiteBoardBase):
    id: int
    creator: Optional[UserBrief] = None
    updater: Optional[UserBrief] = None
    created_at: datetime
    updated_at: datetime
    documents: List[Document] = []
    
    class Config:
        from_attributes = True
        
class WhiteBoardBrief(BaseModel):
    id: int
    type: str
    project_id: str
    title: str
    created_at: datetime
    updated_at: datetime
    created_by: int
    updated_by: int
    
    class Config:
        from_attributes = True