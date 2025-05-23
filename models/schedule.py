from sqlalchemy import Column, Integer, String, Enum, Text
from sqlalchemy.dialects.postgresql import JSONB
from database import Base

class Schedule(Base):
    __tablename__ = "schedule"

    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(String, nullable=False)
    type = Column(Enum("meeting", "event", name="type"), nullable=False)
    title = Column(String, nullable=False)
    description = Column(Text, nullable=False)
    where = Column(String, nullable=False)
    link = Column(Text, nullable=True)
    assignee_id = Column(JSONB, nullable=False)
    start_time = Column(String, nullable=False)
    end_time = Column(String, nullable=False)
    status = Column(Enum("not-started", "in-progress", "done", name="status"), nullable=False)
    created_at = Column(String, nullable=False)
    updated_at = Column(String, nullable=False)
    created_by = Column(Integer, nullable=False)
    updated_by = Column(Integer, nullable=False)
    memo = Column(Text, nullable=True)
    
    