from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

DATABASE_URL = "postgresql://postgres@localhost:5432/teamup"

engine = create_engine(DATABASE_URL)
try:
  engine.connect()
  print("✅ Database connection successful!")
except Exception as e:
  print(f"❌ Database connection failed: {str(e)}")

SessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False)
Base = declarative_base()