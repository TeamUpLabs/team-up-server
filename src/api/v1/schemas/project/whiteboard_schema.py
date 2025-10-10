from pydantic import BaseModel, Field
from typing import Optional, List, Union
from datetime import datetime
from src.api.v1.schemas.brief import UserBrief

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
  
class DocumentUpdate(DocumentBase):
  pass

class CommentBase(BaseModel):
  id: int
  content: str
  created_at: datetime
  updated_at: datetime
  creator: Optional[UserBrief] = None
  
class CommentCreate(BaseModel):
  content: str
  created_by: int

class CommentUpdate(BaseModel):
  content: Optional[str] = None

class Comment(CommentBase):
  class Config:
    from_attributes = True
    
class ReactionLikes(BaseModel):
  count: int = 0
  users: List[UserBrief] = []
    
class ReactionComments(BaseModel):
  count: int = 0
  comments: List[Comment] = []
  class Config:
    from_attributes = True

class ReactionBase(BaseModel):
  # Match ORM relationships so Pydantic can map directly
  likes: ReactionLikes = Field(default_factory=ReactionLikes)
  views: int = 0
  comments: ReactionComments = Field(default_factory=ReactionComments)

class ReactionCreate(ReactionBase):
  pass

class Reaction(ReactionBase):
  class Config:
    from_attributes = True

class WhiteBoardBase(BaseModel):
  type: str
  project_id: str
  title: str


class WhiteBoardCreate(WhiteBoardBase):
  content: str
  tags: Optional[Union[dict, List[str]]] = None
  created_by: int
  updated_by: int
  attachments: Optional[List[AttachmentCreate]] = []
  
class WhiteBoardUpdate(BaseModel):
  title: Optional[str] = None
  content: Optional[str] = None
  tags: Optional[List[str]] = None
  attachments: Optional[List[AttachmentCreate]] = []
  updated_by: int
  
class WhiteBoardDetail(WhiteBoardBase):
  id: int
  created_at: datetime
  updated_at: datetime
  creator: Optional[UserBrief] = None
  updater: Optional[UserBrief] = None
  documents: List[Document] = []
  reactions: Reaction = None
  
  class Config:
    from_attributes = True