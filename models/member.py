from sqlalchemy import Column, Integer, String, Text, JSON, Boolean, Enum
from sqlalchemy.dialects.postgresql import JSONB
from database import Base

class Member(Base):
    __tablename__ = "member"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    email = Column(String, unique=True, index=True, nullable=False)
    password = Column(Text)
    role = Column(String, nullable=False)
    status = Column(String, nullable=False)
    lastLogin = Column(String)
    createdAt = Column(String)
    skills = Column(JSON)
    projects = Column(JSONB)
    profileImage = Column(String)
    contactNumber = Column(String)
    birthDate = Column(String)
    introduction = Column(Text)
    workingHours = Column(JSON)
    languages = Column(JSON)
    socialLinks = Column(JSON)
    participationRequest = Column(JSONB, nullable=True)
    notification = Column(JSON, nullable=True)
    isGithub = Column(Boolean)
    github_id = Column(String)
    github_access_token = Column(Text)
    isGoogle = Column(Boolean)
    google_id = Column(String)
    google_access_token = Column(Text)
    isApple = Column(Boolean)
    apple_id = Column(String)
    apple_access_token = Column(Text)
    signupMethod = Column(Enum("local", "github", "google", "apple", name="signupMethod"), nullable=False)