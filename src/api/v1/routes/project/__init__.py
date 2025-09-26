from .project import router as project_router
from .task import router as task_router
from .milestone import router as milestone_router
from .chat import router as chat_router
from .channel import router as channel_router
from .whiteboard import router as whiteboard_router
from .schedule import router as schedule_router
from .participation_request import router as participation_request_router
from .voice_call import router as voice_call_router

routers = [
    project_router,
    task_router,
    milestone_router,
    chat_router,
    channel_router,
    whiteboard_router,
    schedule_router,
    participation_request_router,
    voice_call_router,
]
