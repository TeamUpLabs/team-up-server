from sqlalchemy import Column, Integer, String, Text, ForeignKey, JSON
from core.database.database import Base
from api.v1.models.base import BaseModel
from sqlalchemy.orm import relationship
from api.v1.models.association_tables import user_post_bookmarks

class Post(Base, BaseModel):
  """게시글 모델"""
  __tablename__ = "posts"

  id = Column(Integer, primary_key=True, index=True)
  content = Column(Text, nullable=False)
  code = Column(JSON, nullable=True)  # Format: {"language": string, "code": string}
  tags = Column(JSON, nullable=True)
  images = Column(JSON, nullable=True)
  videos = Column(JSON, nullable=True)
  
  reaction = relationship("PostReaction", back_populates="post")
  
  # 관계
  user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
  comments = relationship("PostComment", back_populates="post", cascade="all, delete-orphan")
      
  creator = relationship("User", foreign_keys=[user_id], back_populates="posts")
  bookmarked_users = relationship("User", secondary=user_post_bookmarks, back_populates="bookmarked_posts")

class PostReaction(Base, BaseModel):
  """리액션 모델"""
  __tablename__ = "post_reactions"
  
  id = Column(Integer, primary_key=True, index=True)
  reaction_type = Column(String(20), nullable=False)  # 'like', 'dislike', 'view', 'share'
  
  # Relationships
  user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
  post_id = Column(Integer, ForeignKey("posts.id", ondelete="SET NULL"), nullable=False)
  
  post = relationship("Post", back_populates="reaction")
  user = relationship("User", foreign_keys=[user_id])
    

class PostComment(Base, BaseModel):
  """댓글 모델"""
  __tablename__ = "post_comments"
  
  id = Column(Integer, primary_key=True, index=True)
  content = Column(Text, nullable=False)
  post_id = Column(Integer, ForeignKey("posts.id", ondelete="CASCADE"), nullable=False)
  user_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=False)

  post = relationship("Post", back_populates="comments")
  user = relationship("User", foreign_keys=[user_id])
    