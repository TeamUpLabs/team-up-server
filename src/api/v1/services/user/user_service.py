from typing import List
from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from api.v1.repositories.user.user_repository import UserRepository
from api.v1.schemas.user.user_schema import (
    UserCreate,
    UserUpdate,
    UserDetail
)

class UserService:
  def __init__(self, db: Session):
    self.repository = UserRepository(db)
  
  def get_user(self, user_id: int) -> UserDetail:
    """Get a user by ID"""
    try:
      return self.repository.get(user_id)
    except HTTPException as e:
      if e.status_code == 404:
        raise HTTPException(
          status_code=status.HTTP_404_NOT_FOUND,
          detail=f"User with id {user_id} not found"
        )
  
  def get_user_by_email(self, email: str) -> UserDetail:
    """Get a user by email"""
    try:
      return self.repository.get_by_email(email)
    except HTTPException as e:
      if e.status_code == 404:
        raise HTTPException(
          status_code=status.HTTP_404_NOT_FOUND,
          detail=f"User with email {email} not found"
        )
  
  def create_user(self, user_data: UserCreate) -> UserDetail:
    """Create a new user"""
    try:
      # Check if user with email already exists
      self.repository.get_by_email(user_data.email)
      raise HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST,
        detail=f"User with email {user_data.email} already exists"
      )
    except HTTPException as e:
      if e.status_code == 404:  # User not found, safe to create
        return self.repository.create(user_data)
  
  def update_user(
      self, 
      user_id: int, 
      user_data: UserUpdate
  ) -> UserDetail:
    """Update an existing user"""
    try:
      return self.repository.update(user_id, user_data)
    except HTTPException as e:
      if e.status_code == 404:
        raise HTTPException(
          status_code=status.HTTP_404_NOT_FOUND,
          detail=f"User with id {user_id} not found"
        )

  def delete_user(self, user_id: int) -> dict:
    """Delete a user by ID"""
    try:
      self.repository.delete(user_id)
      return {"message": f"User with id {user_id} has been deleted"}
    except HTTPException as e:
      if e.status_code == 404:
        raise HTTPException(
          status_code=status.HTTP_404_NOT_FOUND,
          detail=f"User with id {user_id} not found"
        )
        
  def get_users_exclude_me(self, user_id: int) -> List[UserDetail]:
    """Get all users except the current user"""
    return self.repository.get_users_exclude_me(user_id)