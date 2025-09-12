from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from src.core.database.database import Base
from src.api.v1.models.base import BaseModel

class Chat(Base, BaseModel):
  __tablename__ = "chat"
  
  id = Column(Integer, primary_key=True, index=True)
  project_id = Column(String(6), ForeignKey("projects.id", ondelete="CASCADE"), nullable=False)
  channel_id = Column(String(100), ForeignKey("channels.channel_id", ondelete="CASCADE"), nullable=False)
  user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
  message = Column(Text, nullable=False)
  timestamp = Column(DateTime, nullable=False)
  
  project = relationship("Project", foreign_keys=[project_id])
  channel = relationship("Channel", foreign_keys=[channel_id], back_populates="chats")
  user = relationship("User", foreign_keys=[user_id])
  
  def __repr__(self):
    return f"<Chat(id={self.id}, message='{self.message}')>" 