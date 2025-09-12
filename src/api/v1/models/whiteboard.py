# models/document.py
from sqlalchemy import Column, Integer, String, Text, ForeignKey, JSON, DateTime
from sqlalchemy.orm import relationship
from sqlalchemy.sql import text
from core.database.database import Base
from api.v1.models.base import BaseModel

# Association table for user likes
class UserWhiteBoardLike(Base):
  __tablename__ = "user_whiteboard_likes"
  
  user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), primary_key=True)
  whiteboard_id = Column(Integer, ForeignKey("whiteboards.id", ondelete="CASCADE"), primary_key=True)
  created_at = Column(DateTime, nullable=False, server_default=text("CURRENT_TIMESTAMP"))
  
  def __repr__(self):
    return f"UserWhiteBoardLike(user_id={self.user_id}, whiteboard_id={self.whiteboard_id})"


class WhiteBoard(Base, BaseModel):
  __tablename__ = "whiteboards"

  id = Column(Integer, primary_key=True, index=True)
  type = Column(String(50), nullable=False)  # document, canvas
  project_id = Column(String(6), ForeignKey("projects.id", ondelete="CASCADE"), nullable=False)
  title = Column(String(255), nullable=False)
  
  # # 반응
  likes = Column(Integer, default=0)
  views = Column(Integer, default=0)
  comments = relationship("WhiteBoardComment", back_populates="whiteboard", cascade="all, delete-orphan")
  
  # 생성자, 수정자
  created_by = Column(Integer, ForeignKey("users.id"))
  updated_by = Column(Integer, ForeignKey("users.id"))
  
  creator = relationship("User", foreign_keys=[created_by])
  updater = relationship("User", foreign_keys=[updated_by])

  project = relationship("Project", back_populates="whiteboards")
  
  documents = relationship("Document", back_populates="whiteboard", cascade="all, delete-orphan")
  
  # Users who liked this whiteboard
  liked_by_users = relationship("User", secondary="user_whiteboard_likes", back_populates="liked_whiteboards", lazy="dynamic")
  
  def __repr__(self):
    return f"WhiteBoard(id={self.id}, type={self.type}, project_id={self.project_id}, title={self.title})"
    

class Document(Base, BaseModel):
  __tablename__ = "documents"
  
  id = Column(Integer, primary_key=True, index=True)
  content = Column(Text, nullable=False)
  tags = Column(JSON, nullable=True)
  whiteboard_id = Column(Integer, ForeignKey("whiteboards.id", ondelete="CASCADE"), nullable=False)
  
  whiteboard = relationship("WhiteBoard", back_populates="documents")
  attachments = relationship("Attachment", back_populates="document", cascade="all, delete-orphan")
  
  def __repr__(self):
    return f"Document(id={self.id}, content={self.content}, whiteboard_id={self.whiteboard_id})"
      

class Attachment(Base, BaseModel):
  __tablename__ = "attachments"
  
  id = Column(Integer, primary_key=True, index=True)
  filename = Column(String, nullable=False)
  file_url = Column(String, nullable=False)
  file_type = Column(String, nullable=False)
  file_size = Column(Integer, nullable=False)
  
  document_id = Column(Integer, ForeignKey("documents.id", ondelete="CASCADE"), nullable=False)
  
  document = relationship("Document", back_populates="attachments")
  
  def __repr__(self):
    return f"Attachment(id={self.id}, filename={self.filename}, document_id={self.document_id})"
      
class WhiteBoardComment(Base, BaseModel):
  """댓글 모델"""
  __tablename__ = "whiteboard_comments"
  
  id = Column(Integer, primary_key=True, index=True)
  content = Column(Text, nullable=False)
  created_at = Column(DateTime, nullable=False)
  updated_at = Column(DateTime, nullable=False)
  
  # 외래 키
  whiteboard_id = Column(Integer, ForeignKey("whiteboards.id", ondelete="CASCADE"), nullable=False)
  created_by = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
  
  # 관계 정의
  whiteboard = relationship("WhiteBoard", back_populates="comments")
  creator = relationship("User", foreign_keys=[created_by])
  
  def __repr__(self):
    return f"WhiteBoardComment(id={self.id}, content='{self.content}')" 
    