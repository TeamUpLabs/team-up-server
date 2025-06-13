from sqlalchemy import Column, Integer, String, Boolean, Text, JSON
from sqlalchemy.dialects.postgresql import JSONB
from database import Base

class Channel(Base):
  __tablename__ = "channel"

  id = Column(Integer, primary_key=True, index=True)
  projectId = Column(String, index=True)
  channelId = Column(String, index=True)
  channelName = Column(String)
  channelDescription = Column(Text)
  isPublic = Column(Boolean)
  member_id = Column(JSONB)
  created_at = Column(String)
  created_by = Column(Integer)
    