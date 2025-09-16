from .project import router as project_router
from .task import router as task_router

routers = [
    project_router,
    task_router,
]
