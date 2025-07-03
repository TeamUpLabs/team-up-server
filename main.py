from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import logging
from database import engine, Base
# Import routers
# from routers import (
#     member_routes, 
#     project_routes, 
#     task_routes, 
#     milestone_routes, 
#     auth_routes, 
#     chat_routes, 
#     video_call_routes,
#     voice_call_routes,
#     notification_routes,
#     schedule_routes,
#     channel_routes,
#     github_routes
# )
<<<<<<< HEAD
from new_routers import user_router, project_router, task_router, milestone_router, schedule_router, participation_request_router
=======
from router import user_router, project_router, task_router, milestone_router
>>>>>>> e34fcb6 (Refactor authentication and database interaction for user management)

Base.metadata.create_all(bind=engine)
app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*", "Authorization"],
)

app.include_router(user_router.router)
app.include_router(project_router.router)
app.include_router(task_router.router)
app.include_router(milestone_router.router)
<<<<<<< HEAD
app.include_router(participation_request_router.router)
app.include_router(schedule_router.router)
=======
>>>>>>> e34fcb6 (Refactor authentication and database interaction for user management)

@app.get("/")
async def root():
    return {"message": "TeamUp Server API"}

# # Include routers
# app.include_router(auth_routes.router)
# app.include_router(member_routes.router)
# app.include_router(project_routes.router)
# app.include_router(task_routes.router)
# app.include_router(milestone_routes.router)
# app.include_router(chat_routes.router)
# app.include_router(video_call_routes.router)
# app.include_router(voice_call_routes.router)
# app.include_router(notification_routes.router)
# app.include_router(schedule_routes.router)
# app.include_router(channel_routes.router)
# app.include_router(github_routes.router)