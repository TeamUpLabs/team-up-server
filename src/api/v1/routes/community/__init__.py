from .recommendation import router as recommendation_router
from .post import router as post_router
from .community import router as community_router

routers = [
  recommendation_router,
  post_router,
  community_router,
]