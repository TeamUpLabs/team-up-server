from sqlalchemy import Column, Integer, String, Text, JSON
from sqlalchemy.dialects.postgresql import JSONB
from database import Base

class Member(Base):
    __tablename__ = "member"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    email = Column(String, unique=True, index=True, nullable=False)
    password = Column(String, nullable=False)
    role = Column(String, nullable=False)
    status = Column(String, nullable=False)
    lastLogin = Column(String)
    createdAt = Column(String)
    skills = Column(JSON)
    projects = Column(JSONB)
    profileImage = Column(String)
    contactNumber = Column(String, nullable=False)
    birthDate = Column(String)
    introduction = Column(Text)
    workingHours = Column(JSON, nullable=False)
    languages = Column(JSON)
    socialLinks = Column(JSON)
    participationRequest = Column(JSONB, nullable=True)
    notification = Column(JSON, nullable=True)


