from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, JSON, Boolean
from sqlalchemy.orm import relationship
from database import Base
from models.base import BaseModel

class Notification(Base, BaseModel):
    __tablename__ = "notifications"
    
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(100), nullable=False)
    message = Column(Text, nullable=False)
    timestamp = Column(DateTime, nullable=False)
    is_read = Column(Boolean, nullable=False)
    type = Column(String(100), nullable=False)  # info, message, task, milestone, schedule, chat, scout, project
    sender_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    receiver_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    project_id = Column(String(6), ForeignKey("projects.id", ondelete="SET NULL"), nullable=True)
    result = Column(String(100), nullable=True)
    
    sender = relationship("User", foreign_keys=[sender_id], back_populates="sent_notifications")
    receiver = relationship("User", foreign_keys=[receiver_id], back_populates="received_notifications")
    project = relationship("Project", foreign_keys=[project_id])
    
    def __repr__(self):
        return f"<Notification(id={self.id}, title='{self.title}')>" 