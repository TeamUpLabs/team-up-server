from starlette.middleware.base import BaseHTTPMiddleware
from fastapi import Request, HTTPException
from core.security.jwt import verify_token

class AuthMiddleware(BaseHTTPMiddleware):
  async def dispatch(self, request: Request, call_next):
    if request.url.path.startswith("/users/login") or request.url.path.startswith("/docs"):
      return await call_next(request)

    token = request.headers.get("Authorization")
    if not token or not token.startswith("Bearer "):
      raise HTTPException(status_code=401, detail="Not authenticated")

    jwt_token = token.split(" ")[1]
    try:
      payload = verify_token(jwt_token)
      request.state.user = payload  # request에 유저 정보 저장
    except Exception:
      raise HTTPException(status_code=401, detail="Invalid token")

    return await call_next(request)