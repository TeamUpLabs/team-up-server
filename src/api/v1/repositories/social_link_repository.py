from typing import List
from sqlalchemy.orm import Session
from fastapi import HTTPException, status
from api.v1.models.user import UserSocialLink as DBSocialLink
from api.v1.schemas.social_link_schema import (
    SocialLinkCreate,
    SocialLinkUpdate
)

class SocialLinkRepository:
  def __init__(self, db: Session):
    self.db = db
  
  def get_user_social_links(self, user_id: int) -> List[DBSocialLink]:
    """Get all social links for a user"""
    return self.db.query(DBSocialLink).filter(
      DBSocialLink.user_id == user_id
    ).all()
  
  def get_social_link(self, link_id: int, user_id: int) -> DBSocialLink:
    """Get a specific social link for a user"""
    db_link = self.db.query(DBSocialLink).filter(
      DBSocialLink.id == link_id,
      DBSocialLink.user_id == user_id
    ).first()
      
    if not db_link:
      raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail=f"Social link with id {link_id} not found for user {user_id}"
      )
    return db_link
  
  def create_social_link(
    self, 
    user_id: int, 
    link_data: SocialLinkCreate
  ) -> DBSocialLink:
    """Create a new social link for a user"""
    # Check if the same platform already exists for the user
    existing_link = self.db.query(DBSocialLink).filter(
      DBSocialLink.user_id == user_id,
      DBSocialLink.platform == link_data.platform
    ).first()
      
    if existing_link:
      raise HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST,
        detail=f"Social link for platform '{link_data.platform}' already exists"
      )
          
    db_link = DBSocialLink(
      user_id=user_id,
      **link_data.model_dump()
    )
      
    self.db.add(db_link)
    self.db.commit()
    self.db.refresh(db_link)
    return db_link
  
  def update_social_link(
    self, 
    link_id: int, 
    user_id: int, 
    link_data: SocialLinkUpdate
  ) -> DBSocialLink:
    """Update an existing social link"""
    db_link = self.get_social_link(link_id, user_id)
      
    # If platform is being updated, check for conflicts
    if hasattr(link_data, 'platform') and link_data.platform != db_link.platform:
      existing_link = self.db.query(DBSocialLink).filter(
        DBSocialLink.id != link_id,
        DBSocialLink.user_id == user_id,
        DBSocialLink.platform == link_data.platform
      ).first()
          
      if existing_link:
        raise HTTPException(
          status_code=status.HTTP_400_BAD_REQUEST,
          detail=f"Social link for platform '{link_data.platform}' already exists"
        )
      
      update_data = link_data.model_dump(exclude_unset=True)
      for field, value in update_data.items():
        setattr(db_link, field, value)
          
      self.db.add(db_link)
      self.db.commit()
      self.db.refresh(db_link)
      return db_link
  
  def delete_social_link(self, link_id: int, user_id: int) -> None:
    """Delete a social link"""
    db_link = self.get_social_link(link_id, user_id)
    self.db.delete(db_link)
    self.db.commit()
    return None
