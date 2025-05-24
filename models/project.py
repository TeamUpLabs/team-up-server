from sqlalchemy import Column, Integer, String, Text, JSON
from sqlalchemy.dialects.postgresql import JSONB
from database import Base

class Project(Base):
    __tablename__ = "project"

    id = Column(String, primary_key=True)
    title = Column(String, nullable=False)
    status = Column(String, nullable=False)
    description = Column(Text, nullable=False)
    leader_id = Column(Integer, nullable=False)
    manager_id = Column(JSONB, nullable=True)
    roles = Column(JSON)
    techStack = Column(JSON)
    startDate = Column(String, nullable=False)
    endDate = Column(String, nullable=False)
    teamSize = Column(Integer, nullable=False)
    location = Column(String, nullable=False)
    projectType = Column(String, nullable=False)
    participationRequest = Column(JSONB, nullable=True)
    createdAt = Column(String, nullable=False)
    