from pydantic import BaseModel
from typing import Optional, List, Union
from schemas.user import UserBrief
from datetime import datetime

class AttachmentBase(BaseModel):
    filename: str
    file_url: str
    file_type: str
    file_size: int

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
    tags: Optional[Union[dict, List[str]]] = None

class DocumentCreate(DocumentBase):
    attachments: List[AttachmentCreate] = []

class Document(DocumentBase):
    id: int
    whiteboard_id: int
    created_at: datetime
    updated_at: datetime
    attachments: List[Attachment] = []

    class Config:
        from_attributes = True
        
class Comment(BaseModel):
    id: int
    content: str
    created_at: datetime
    updated_at: datetime
    creator: Optional[UserBrief] = None
    
    class Config:
        from_attributes = True

class CommentCreate(BaseModel):
    content: str
    creator: UserBrief

class CommentUpdate(BaseModel):
    content: str

class WhiteBoardBase(BaseModel):
    type: str
    project_id: str
    title: str
    
class WhiteBoardCreate(WhiteBoardBase):
    content: str
    tags: List[str]
    created_by: int
    updated_by: int
    attachments: List[AttachmentCreate] = []
    
class WhiteBoardUpdate(BaseModel):
    id: int
    title: Optional[str] = None
    content: Optional[str] = None
    tags: List[str]
    updated_by: int
    
class WhiteBoardDetail(WhiteBoardBase):
    id: int
    creator: Optional[UserBrief] = None
    updater: Optional[UserBrief] = None
    created_at: datetime
    updated_at: datetime
    documents: List[Document] = []
    comments: List[Comment] = []
    likes: int = 0
    views: int = 0
    
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