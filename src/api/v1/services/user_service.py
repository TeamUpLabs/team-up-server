from sqlalchemy.orm import Session
from api.v1.repositories.user_repository import UserRepository
from api.v1.schemas.user_schema import UserCreate, UserUpdate

class UserService:
  def __init__(self, db: Session):
    self.repo = UserRepository(db)
    
  def get_user(self, user_id: int):
    user = self.repo.get(user_id)
    if not user:
      raise ValueError("존재하지 않는 사용자입니다.")
    return user
  
  def get_user_by_email(self, email: str):
    user = self.repo.get_by_email(email)
    if not user:
      raise ValueError("존재하지 않는 사용자입니다.")
    return user
    
  def create_user(self, user: UserCreate):
    if self.repo.get_by_email(user.email):
      raise ValueError("이미 존재하는 이메일입니다.")
    return self.repo.create(user)
  
  def update_user(self, user_id: int, user: UserUpdate):
    user = self.get_user(user_id)
    if not user:
      raise ValueError("존재하지 않는 사용자입니다.")
    return self.repo.update(user_id, user)
  
  def delete_user(self, user_id: int):
    user = self.get_user(user_id)
    if not user:
      raise ValueError("존재하지 않는 사용자입니다.")
    return self.repo.remove(user_id)