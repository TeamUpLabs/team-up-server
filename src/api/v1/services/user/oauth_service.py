from api.v1.repositories.user.oauth_repository import AuthRepository
from sqlalchemy.orm import Session
from api.v1.schemas.user.oauth_schema import OauthRequest

class OauthService:
  def __init__(self, db: Session):
    self.repository = AuthRepository(db)
    
  async def oauth_login(self, provider: str):
    return await self.repository.oauth_login(provider)
    
  async def oauth_callback(self, form_data: OauthRequest):
    return await self.repository.oauth_callback(form_data)