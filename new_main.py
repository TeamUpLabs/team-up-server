from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from database import engine, Base
from new_models.base import BaseModel
from new_routers import (
    auth_router,
    user_router,
    project_router,
    task_router,
    milestone_router,
    participation_request_router,
    schedule_router,
    notification_router,
    channel_router,
    chat_router
)

# 모든 모델이 정의된 후 테이블 생성
Base.metadata.create_all(bind=engine)

# FastAPI 애플리케이션 생성
app = FastAPI(
    title="TeamUp API",
    description="프로젝트 관리를 위한 RESTful API",
    version="1.0.0"
)

# CORS 미들웨어 설정
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],  # 정확한 origin 명시
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],  # Authorization 포함됨
)

# 라우터 등록
app.include_router(auth_router)
app.include_router(user_router)
app.include_router(project_router)
app.include_router(task_router)
app.include_router(milestone_router)
app.include_router(participation_request_router)
app.include_router(schedule_router)
app.include_router(notification_router)
app.include_router(channel_router)
app.include_router(chat_router)

@app.get("/")
async def root():
    """API 루트 엔드포인트"""
    return {
        "name": "TeamUp API",
        "version": "2.0.0",
        "status": "active"
    }

# 애플리케이션 실행
if __name__ == "__main__":
    import uvicorn
    uvicorn.run("new_main:app", host="0.0.0.0", port=8000, reload=True) 