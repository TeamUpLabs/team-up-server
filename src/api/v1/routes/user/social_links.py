from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

from src.core.database.database import get_db
from src.api.v1.schemas.user.social_link_schema import (
    SocialLink,
    SocialLinkCreate,
    SocialLinkUpdate
)
from src.api.v1.services.user.social_link_service import SocialLinkService
from src.core.security.auth import get_current_user

router = APIRouter(
  prefix="/api/v1/users/{user_id}/social-links",
  tags=["social-links"]
)

@router.get("/", response_model=List[SocialLink])
def list_social_links(
  user_id: int,
  db: Session = Depends(get_db),
  current_user: dict = Depends(get_current_user)
):
  """
  Get all social links for a user
  """
  if current_user.id != user_id:
    raise HTTPException(
      status_code=status.HTTP_403_FORBIDDEN,
      detail="Not authorized to access this resource"
    )
      
  service = SocialLinkService(db)
  return service.get_user_social_links(user_id)

@router.post("/", response_model=SocialLink, status_code=status.HTTP_201_CREATED)
def create_social_link(
  user_id: int,
  social_link: SocialLinkCreate,
  db: Session = Depends(get_db),
  current_user: dict = Depends(get_current_user)
):
  """
  Add a new social link for a user
  """
  if current_user.id != user_id:
    raise HTTPException(
      status_code=status.HTTP_403_FORBIDDEN,
      detail="Not authorized to perform this action"
    )
        
  service = SocialLinkService(db)
  return service.create_social_link(user_id, social_link)

@router.get("/{link_id}", response_model=SocialLink)
def get_social_link(
  user_id: int,
  link_id: int,
  db: Session = Depends(get_db),
  current_user: dict = Depends(get_current_user)
):
  """
  Get a specific social link by ID
  """
  if current_user.id != user_id:
    raise HTTPException(
      status_code=status.HTTP_403_FORBIDDEN,
      detail="Not authorized to access this resource"
    )
        
  service = SocialLinkService(db)
  return service.get_social_link(link_id, user_id)

@router.put("/{link_id}", response_model=SocialLink)
def update_social_link(
  user_id: int,
  link_id: int,
  social_link: SocialLinkUpdate,
  db: Session = Depends(get_db),
  current_user: dict = Depends(get_current_user)
):
  """
  Update a social link
  """
  if current_user.id != user_id:
    raise HTTPException(
      status_code=status.HTTP_403_FORBIDDEN,
      detail="Not authorized to perform this action"
    )
        
  service = SocialLinkService(db)
  return service.update_social_link(link_id, user_id, social_link)

@router.delete("/{link_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_social_link(
  user_id: int,
  link_id: int,
  db: Session = Depends(get_db),
  current_user: dict = Depends(get_current_user)
):
  """
  Delete a social link
  """
  if current_user.id != user_id:
    raise HTTPException(
      status_code=status.HTTP_403_FORBIDDEN,
      detail="Not authorized to perform this action"
    )
        
  service = SocialLinkService(db)
  service.delete_social_link(link_id, user_id)
  return None
