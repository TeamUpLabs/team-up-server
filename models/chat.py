from sqlalchemy import Column, Integer, String, Text
from database import Base

class ChatMessage(Base):
    __tablename__ = "chat"

    id = Column(Integer, primary_key=True, index=True)
    channelId = Column(String, index=True)
    userId = Column(Integer)
    user = Column(String)
    message = Column(Text)
    timestamp = Column(String)