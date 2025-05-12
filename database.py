from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
import os
from dotenv import load_dotenv
import socket

load_dotenv()

DATABASE_URL = os.getenv("POSTGRES_URL")
print(f"Attempting to connect to: {DATABASE_URL}")

# Check if hostname can be resolved
try:
  host = DATABASE_URL.split('@')[1].split(':')[0] if '@' in DATABASE_URL else DATABASE_URL.split('/')[2].split(':')[0]
  print(f"Trying to resolve hostname: {host}")
  ip = socket.gethostbyname(host)
  print(f"✅ Hostname resolved to IP: {ip}")
except Exception as e:
  print(f"❌ Hostname resolution failed: {str(e)}")

engine = create_engine(DATABASE_URL, pool_pre_ping=True)
try:
  engine.connect()
  print("✅ Database connection successful!")
except Exception as e:
  print(f"❌ Database connection failed: {str(e)}")

SessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False)
Base = declarative_base()