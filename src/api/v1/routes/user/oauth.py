from fastapi import APIRouter, Request
from src.api.v1.services.user.oauth_service import OauthService
from src.api.v1.schemas.user.oauth_schema import OauthRequest
from src.core.database.database import get_db
from sqlalchemy.orm import Session
from fastapi import Depends, HTTPException
from src.api.v1.schemas.user.user_schema import UserCreate

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

@router.post("/additional-info")
async def oauth_additional_info(
  form_data: UserCreate,
  db: Session = Depends(get_db)
):
  """
  OAuth 추가 정보 처리
  """
  try:
    service = OauthService(db)
    return await service.oauth_additional_info(form_data)
  except Exception as e:
    raise HTTPException(status_code=500, detail=str(e))
