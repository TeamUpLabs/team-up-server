from fastapi import APIRouter, Request
from api.v1.services.user.oauth_service import OauthService
from api.v1.schemas.user.oauth_schema import OauthRequest
from core.database.database import get_db
from sqlalchemy.orm import Session
from fastapi import Depends, HTTPException

router = APIRouter(
    prefix="/api/v1/user/oauth",
    tags=["user/oauth"]
)

@router.get("/login")
async def oauth_login(
  provider: str,
  db: Session = Depends(get_db)
):
  """
  OAuth 로그인 URL 생성
  """
  try:
    service = OauthService(db)
    return await service.oauth_login(provider)
  except Exception as e:
    raise HTTPException(status_code=500, detail=str(e))

@router.post("/callback")
async def oauth_callback(
  form_data: OauthRequest,
  request: Request,
  db: Session = Depends(get_db)
):
  """
  OAuth 콜백 처리
  """
  try:
    service = OauthService(db)
    return await service.oauth_callback(form_data, request)
  except Exception as e:
    raise HTTPException(status_code=500, detail=str(e))
