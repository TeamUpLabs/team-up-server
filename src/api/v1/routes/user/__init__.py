from .user import router as user_router
from .collaboration_preferences import router as collaboration_preferences_router
from .tech_stacks import router as tech_stacks_router
from .interests import router as interests_router
from .social_links import router as social_links_router
from .notifications import router as notifications_router
from .sessions import router as sessions_router
from .oauth import router as oauth_router
from .follow import router as follow_router

# Import all routers
routers = [
    user_router,
    collaboration_preferences_router,
    tech_stacks_router,
    interests_router,
    social_links_router,
    notifications_router,
    sessions_router,
    oauth_router,
    follow_router
]