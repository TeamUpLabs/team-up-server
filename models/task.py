from sqlalchemy import Column, Integer, String, Text, Enum, JSON
from sqlalchemy.dialects.postgresql import JSONB
from database import Base

class Task(Base):
  __tablename__ = "task"
  
  id = Column(Integer, primary_key=True, index=True, nullable=False)
  title = Column(String, nullable=False)
  description = Column(Text, nullable=False)
  status = Column(Enum("todo", "in-progress", "done", name="status"), nullable=False)
  priority = priority = Column(Enum("low", "medium", "high", name="priority"), nullable=False)
  assignee_id = Column(JSONB, nullable=False)
  dueDate = Column(String, nullable=False)
  tags = Column(JSONB, nullable=False)
  subtasks = Column(JSON, nullable=True)
  comments = Column(JSON, nullable=True)
  createdAt = Column(String, nullable=False)
  updatedAt = Column(String, nullable=False)
  