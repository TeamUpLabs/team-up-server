from starlette.middleware.base import BaseHTTPMiddleware
import time
import logging

logger = logging.getLogger("app.middleware")

class LoggingMiddleware(BaseHTTPMiddleware):
  async def dispatch(self, request, call_next):
    start_time = time.time()
    response = await call_next(request)
    duration = time.time() - start_time

    logger.info(
      f"{request.method} {request.url.path} "
      f"Status: {response.status_code} "
      f"Duration: {duration:.2f}s"
    )
    return response