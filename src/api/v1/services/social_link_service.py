from typing import List
from fastapi import HTTPException
from sqlalchemy.orm import Session
from api.v1.schemas.social_link_schema import (
    SocialLinkCreate,
    SocialLinkUpdate,
    SocialLinkInDB
)
from api.v1.repositories.social_link_repository import SocialLinkRepository

class SocialLinkService:
  def __init__(self, db: Session):
    self.repository = SocialLinkRepository(db)

  def get_user_social_links(self, user_id: int) -> List[SocialLinkInDB]:
    """Get all social links for a user"""
    return self.repository.get_user_social_links(user_id)

  def get_social_link(self, link_id: int, user_id: int) -> SocialLinkInDB:
    """Get a specific social link for a user"""
    db_link = self.repository.get_social_link(link_id, user_id)
      
    if not db_link:
      raise HTTPException(
        status_code=404,
        detail=f"Social link with id {link_id} not found for user {user_id}"
      )
    return db_link
      
  def create_social_link(
    self, 
    user_id: int, 
    link: SocialLinkCreate
  ) -> SocialLinkInDB:
    """Create a new social link for a user"""
    # Check if platform already exists for user
    existing_link = self.repository.get_user_social_links(user_id)
    for existing in existing_link:
      if existing.platform == link.platform:
        raise HTTPException(
          status_code=400,
          detail=f"Social link for platform {link.platform} already exists for user {user_id}"
        )
    return self.repository.create_social_link(user_id, link)
      
  def update_social_link(
    self, 
    link_id: int, 
    user_id: int, 
    link: SocialLinkUpdate
  ) -> SocialLinkInDB:
    """Update an existing social link"""
    db_link = self.get_social_link(link_id, user_id)
    return self.repository.update_social_link(link_id, user_id, link)
      
  def delete_social_link(self, link_id: int, user_id: int) -> dict:
    """Delete a social link"""
    self.get_social_link(link_id, user_id)
    self.repository.delete_social_link(link_id, user_id)
    return {"message": "Social link deleted successfully"}
