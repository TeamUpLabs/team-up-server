from api.v1.repositories.user.oauth_repository import AuthRepository
from sqlalchemy.orm import Session
from fastapi import Request
from api.v1.schemas.user.user_schema import UserCreate, UserDetail
from api.v1.schemas.user.oauth_schema import OauthRequest

class OauthService:
  def __init__(self, db: Session):
    self.repository = AuthRepository(db)
    
  async def oauth_login(self, provider: str):
    return await self.repository.oauth_login(provider)
    
  async def oauth_callback(self, form_data: OauthRequest, request: Request):
    return await self.repository.oauth_callback(form_data, request)
  
  async def oauth_additional_info(self, form_data: UserCreate) -> UserDetail:
    return await self.repository.oauth_additional_info(form_data)