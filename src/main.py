from fastapi import FastAPI
import uvicorn
from fastapi.middleware.cors import CORSMiddleware
from core.database.database import engine, Base
from core.middleware.ErrorHandlingMiddleware import ErrorHandlingMiddleware
from core.middleware.LoggingMiddleware import LoggingMiddleware
from core.middleware.AuthMiddleware import AuthMiddleware
from core.config import setting

try:
    Base.metadata.create_all(bind=engine)
    print("✅ Database tables created successfully")
except Exception as e:
    print(f"⚠️  Database connection issue: {str(e)}")
    print("🔧 Running in WebSocket-only mode")

# Import routers after models to avoid circular imports
from api.v1.routes.user import routers as user_routers
from api.v1.routes.project import routers as project_routers

app = FastAPI(
  title=setting.TITLE,
  description=setting.SUMMARY,
  version=setting.VERSION
)

app.add_middleware(
  CORSMiddleware,
  allow_origins=["*"],  # 정확한 origin 명시
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

@app.get("/")
async def root():
  """API 루트 엔드포인트"""
  return {
    "name": setting.TITLE,
    "version": setting.VERSION,
    "status": setting.STATUS
  }
  
if __name__ == "__main__":
  uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True) 