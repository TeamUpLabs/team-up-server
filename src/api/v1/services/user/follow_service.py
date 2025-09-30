from sqlalchemy.orm import Session
from api.v1.repositories.user.follow_repository import FollowRepository
from api.v1.schemas.user.follow_schema import FollowCreate, FollowList, FollowResponse

class FollowService:
  def __init__(self, db: Session):
    self.repository = FollowRepository(db)
    
  def create(self, follow_create: FollowCreate) -> FollowResponse:
    return self.repository.create(follow_create)
    
  def delete(self, follow_create: FollowCreate) -> FollowResponse:
    return self.repository.delete(follow_create)
    
  def get_followers(self, user_id: int) -> FollowList:
    return self.repository.get_followers(user_id)
    
  def get_followed(self, user_id: int) -> FollowList:
    return self.repository.get_followed(user_id)