from sqlalchemy import Column, Integer, String, Text, JSON, Enum
from sqlalchemy.dialects.postgresql import JSONB
from database import Base

class Milestone(Base):
  __tablename__ = "milestone"
  
  id = Column(Integer, primary_key=True, index=True)
  project_id = Column(String, nullable=False)
  title = Column(String, nullable=False)
  description = Column(Text, nullable=False)
  assignee_id = Column(JSONB, nullable=False)
  startDate = Column(String, nullable=False)
  endDate = Column(String, nullable=False)
  status = Column(Enum("not-started", "in-progress", "done", name="status"), nullable=False)
  priority = Column(Enum("low", "medium", "high", name="priority"), nullable=False)
  tags = Column(JSONB, nullable=False)
  subtasks = Column(JSON, nullable=True)