from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from fastapi import HTTPException
from fastapi import status
from api.v1.models.association_tables import user_follows
from api.v1.models.user import User
from api.v1.schemas.user.follow_schema import FollowList, FollowCreate, FollowResponse

class FollowRepository:
  def __init__(self, db: Session):
    self.db = db
    
  def _user_exists(self, user_id: int) -> bool:
    return self.db.query(User).filter(User.id == user_id).first() is not None
    
  def create(self, follow_create: FollowCreate) -> FollowResponse:
    # Check if both users exist
    if not self._user_exists(follow_create.follower_id):
      raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail=f"User with id {follow_create.follower_id} not found"
      )
    
    if not self._user_exists(follow_create.followed_id):
      raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail=f"User with id {follow_create.followed_id} not found"
      )
    
    try:
      self.db.execute(
        user_follows.insert().values(
          follower_id=follow_create.follower_id,
          followed_id=follow_create.followed_id
        )
      )
      self.db.commit()
    except IntegrityError as e:
      self.db.rollback()
      if "duplicate key" in str(e).lower():
        raise HTTPException(
          status_code=status.HTTP_409_CONFLICT,
          detail="This follow relationship already exists"
        )
      raise
    
  def delete(self, follow_create: FollowCreate) -> FollowResponse:
    self.db.execute(user_follows.delete().where(user_follows.c.follower_id == follow_create.follower_id, user_follows.c.followed_id == follow_create.followed_id))
    self.db.commit()
    
  def get_followers(self, user_id: int) -> FollowList:
    followers = self.db.query(user_follows.c.follower_id).filter(user_follows.c.followed_id == user_id).all()
    return FollowList(count=len(followers), users=followers)
    
  def get_followed(self, user_id: int) -> FollowList:
    followed = self.db.query(user_follows.c.followed_id).filter(user_follows.c.follower_id == user_id).all()
    return FollowList(count=len(followed), users=followed)
    