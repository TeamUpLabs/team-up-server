from .project import router as project_router
from .task import router as task_router
from .milestone import router as milestone_router
from .chat import router as chat_router
from .channel import router as channel_router

routers = [
    project_router,
    task_router,
    milestone_router,
    chat_router,
    channel_router
]
