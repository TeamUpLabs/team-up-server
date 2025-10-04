from .mentor import router as mentor_router
from .mentor_review import router as mentor_review_router
from .mentor_session import router as mentor_session_router

routers = [
  mentor_router,
  mentor_review_router,
  mentor_session_router
]
  