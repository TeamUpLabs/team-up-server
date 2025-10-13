from fastapi import FastAPI
import uvicorn
from fastapi.middleware.cors import CORSMiddleware
from src.core.database.database import engine, Base
from src.core.middleware.ErrorHandlingMiddleware import ErrorHandlingMiddleware
from src.core.middleware.LoggingMiddleware import LoggingMiddleware
from src.core.config import setting

try:
    Base.metadata.create_all(bind=engine)
    print("✅ Database tables created successfully")
except Exception as e:
    print(f"⚠️  Database connection issue: {str(e)}")
    print("🔧 Running in WebSocket-only mode")

# Import routers after models to avoid circular imports
from src.api.v1.routes.user import routers as user_routers
from src.api.v1.routes.project import routers as project_routers
from src.api.v1.routes.community import routers as community_routers
from src.api.v1.routes.mentoring import routers as mentoring_routers

app = FastAPI(
  title=setting.TITLE,
  description=setting.SUMMARY,
  version=setting.VERSION
)

app.add_middleware(
  CORSMiddleware,
  allow_origins=["localhost", "http://localhost:3000", "http://127.0.0.1:3000", "https://team-up.kro.kr"],  # 정확한 origin 명시
  allow_credentials=True,
  allow_methods=["*"],
  allow_headers=["*"],  # Authorization 포함됨
)

app.add_middleware(ErrorHandlingMiddleware)
app.add_middleware(LoggingMiddleware)
# app.add_middleware(AuthMiddleware)

# Include all user routers
for router in user_routers:
    app.include_router(router)

# Include all project routers
for router in project_routers:
    app.include_router(router)

# Include all community routers
for router in community_routers:
    app.include_router(router)

# Include all mentoring routers
for router in mentoring_routers:
    app.include_router(router)

@app.get("/")
async def root():
  """API 루트 엔드포인트"""
  return {
    "name": setting.TITLE,
    "version": setting.VERSION,
    "status": setting.STATUS
  }

@app.get("/health")
async def health_check():
  return {"status": "ok"}

if __name__ == "__main__":
  uvicorn.run(app, host="0.0.0.0")
  