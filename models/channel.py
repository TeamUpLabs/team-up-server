from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, Boolean
from sqlalchemy.orm import relationship
from database import Base
from models.base import BaseModel
from models.association_tables import channel_members

class Channel(Base, BaseModel):
    __tablename__ = "channels"
    
    channel_id = Column(String(100), primary_key=True, index=True, nullable=False)
    project_id = Column(String(6), ForeignKey("projects.id", ondelete="CASCADE"), nullable=False)
    name = Column(String(100), nullable=False)
    description = Column(Text, nullable=True)
    is_public = Column(Boolean, nullable=False)
    
    created_at = Column(DateTime, nullable=False)
    updated_at = Column(DateTime, nullable=False)
    
    created_by = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    updated_by = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    
    project = relationship("Project", foreign_keys=[project_id])
    creator = relationship("User", foreign_keys=[created_by])
    updater = relationship("User", foreign_keys=[updated_by])
    
    members = relationship(
        "User",
        secondary=channel_members
    )
    
    chats = relationship("Chat", back_populates="channel", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<Channel(id={self.id}, name='{self.name}')>" 