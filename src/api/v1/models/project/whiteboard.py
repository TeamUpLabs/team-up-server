from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, JSON, Boolean, UniqueConstraint
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from src.api.v1.models.base import BaseModel
from src.core.database.database import Base


class Attachment(Base, BaseModel):
  __tablename__ = "attachments"
  
  id = Column(Integer, primary_key=True, index=True)
  filename = Column(String(255), nullable=False)
  file_url = Column(String(500), nullable=False)
  file_type = Column(String(100), nullable=False)
  file_size = Column(Integer, nullable=False)
  document_id = Column(Integer, ForeignKey("documents.id"), nullable=False)
  
  # Relationships
  document = relationship("Document", back_populates="attachments")

class Document(Base, BaseModel):
  __tablename__ = "documents"
  
  id = Column(Integer, primary_key=True, index=True)
  content = Column(Text, nullable=False)
  tags = Column(JSON, nullable=True)
  whiteboard_id = Column(Integer, ForeignKey("whiteboards.id"), nullable=False)
  
  # Relationships
  whiteboard = relationship("WhiteBoard", back_populates="documents")
  attachments = relationship("Attachment", back_populates="document", cascade="all, delete-orphan")

class WhiteboardComment(Base, BaseModel):
  __tablename__ = "whiteboard_comments"
  
  id = Column(Integer, primary_key=True, index=True)
  content = Column(Text, nullable=False)
  created_by = Column(Integer, ForeignKey("users.id"), nullable=False)
  whiteboard_id = Column(Integer, ForeignKey("whiteboards.id"), nullable=False)
  reaction_id = Column(Integer, ForeignKey("whiteboard_reactions.id"), nullable=False)
  
  # Relationships
  creator = relationship("User")
  whiteboard = relationship("WhiteBoard")
  reaction = relationship("WhiteboardReaction", back_populates="comments")

class WhiteboardReaction(Base, BaseModel):
  __tablename__ = "whiteboard_reactions"
  
  id = Column(Integer, primary_key=True, index=True)
  whiteboard_id = Column(Integer, ForeignKey("whiteboards.id"), nullable=False)
  views = Column(Integer, default=0)
  
  # Relationships
  whiteboard = relationship("WhiteBoard", back_populates="reactions")
  comments = relationship("WhiteboardComment", back_populates="reaction", cascade="all, delete-orphan")
  likes = relationship("WhiteboardReactionLike", back_populates="reaction", cascade="all, delete-orphan")

class WhiteboardReactionLike(Base, BaseModel):
  __tablename__ = "whiteboard_reaction_likes"
  
  id = Column(Integer, primary_key=True, index=True)
  reaction_id = Column(Integer, ForeignKey("whiteboard_reactions.id"), nullable=False)
  user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
  
  # Relationships
  reaction = relationship("WhiteboardReaction", back_populates="likes")
  user = relationship("User")
  
  # Unique constraint to prevent duplicate likes
  __table_args__ = (
    UniqueConstraint("reaction_id", "user_id", name="uq_whiteboard_reaction_like_user"),
    {"extend_existing": True},
  )

class WhiteBoard(Base, BaseModel):
  __tablename__ = "whiteboards"
  
  id = Column(Integer, primary_key=True, index=True)
  type = Column(String(50), nullable=False)
  project_id = Column(String(6), ForeignKey("projects.id", ondelete="CASCADE"), nullable=False)
  title = Column(String(255), nullable=False)
  tags = Column(JSON, nullable=True)
  created_by = Column(Integer, ForeignKey("users.id"), nullable=False)
  updated_by = Column(Integer, ForeignKey("users.id"), nullable=False)
  
  # Relationships
  project = relationship("Project", back_populates="whiteboards")
  creator = relationship("User", foreign_keys=[created_by])
  updater = relationship("User", foreign_keys=[updated_by])
  documents = relationship("Document", back_populates="whiteboard", cascade="all, delete-orphan")
  reactions = relationship("WhiteboardReaction", back_populates="whiteboard", cascade="all, delete-orphan")
  
  # Users who liked this whiteboard (reciprocal to User.liked_whiteboards)
  liked_by_users = relationship(
      "User",
      secondary="user_whiteboard_likes",
      back_populates="liked_whiteboards"
  )
