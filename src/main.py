from fastapi import FastAPI
import uvicorn
from fastapi.middleware.cors import CORSMiddleware
from core.database.database import engine, Base
from core.middleware.ErrorHandlingMiddleware import ErrorHandlingMiddleware
from core.middleware.LoggingMiddleware import LoggingMiddleware
from core.middleware.AuthMiddleware import AuthMiddleware

# Import all models to ensure they are registered with SQLAlchemy
from api.v1.models import *

# Create database tables
Base.metadata.create_all(bind=engine)

# Import routers after models to avoid circular imports
from api.v1.routes.user import routers as user_routers
from api.v1.routes.project import routers as project_routers

app = FastAPI(
  title="TeamUp API",
  description="프로젝트 관리를 위한 RESTful API",
  version="1.0.0"
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
    "name": "TeamUp API",
    "version": "1.0.0",
    "status": "active"
  }
  
if __name__ == "__main__":
  uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True) 