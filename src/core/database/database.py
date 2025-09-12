from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from sqlalchemy.pool import StaticPool
from dotenv import load_dotenv
import os

load_dotenv()

# 데이터베이스 URL
DATABASE_URL = os.getenv("POSTGRES_URL")

# SQLAlchemy 엔진 생성
engine = create_engine(
  DATABASE_URL,
  poolclass=StaticPool,
  pool_pre_ping=True,
  echo=False  # SQL 쿼리 로깅을 원하면 True로 변경
)

try:
  engine.connect()
  print("✅ Database connection successful!")
except Exception as e:
  print(f"❌ Database connection failed: {str(e)}")

# 세션 팩토리 생성
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# 베이스 클래스 생성
Base = declarative_base()

# 데이터베이스 세션 의존성
def get_db():
  """
  데이터베이스 세션을 생성하고 관리하는 의존성 함수
  FastAPI의 Depends와 함께 사용
  """
  db = SessionLocal()
  try:
    yield db
  finally:
    db.close()
