from typing import List
from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from api.v1.repositories.user.user_repository import UserRepository
from api.v1.schemas.user.user_schema import (
    UserCreate,
    UserUpdate,
    UserDetail,
    UserNolinks
)
from api.v1.schemas.brief import UserBrief
from api.v1.models.user.user import User

class UserService:
  def __init__(self, db: Session):
    self.repository = UserRepository(db)
  
  def get_user(self, user_id: int) -> UserDetail:
    return self.repository.get(user_id)
        
  def get_user_brief(self, user_id: int) -> UserBrief:
    return self.repository.get_user_brief(user_id)
    
  def get_user_by_email(self, email: str) -> UserDetail:
    return self.repository.get_by_email(email)
    
  def create_user(self, user_data: UserCreate) -> UserDetail:
    return self.repository.create(user_data)
    
  def update_user(self, user_id: int, user_data: UserUpdate) -> UserDetail:
    return self.repository.update(user_id, user_data)
    
  def delete_user(self, user_id: int) -> dict:
    return self.repository.remove(user_id)
    
  def get_users_exclude_me(self, user_id: int) -> List[UserDetail]:
    return self.repository.get_users_exclude_me(user_id)
    
  def update_last_login(self, user_id: int) -> User:
    return self.repository.update_last_login(user_id)
  
  def get_user_by_id_no_links(self, user_id: int) -> UserNolinks:
    return self.repository.get_user_by_id_no_links(user_id)
    