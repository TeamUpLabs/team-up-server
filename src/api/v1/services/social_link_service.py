from typing import List, Optional
from sqlalchemy.orm import Session
from fastapi import HTTPException, status
from api.v1.models.user import UserSocialLink as DBSocialLink
from api.v1.schemas.social_link_schema import (
    SocialLinkCreate,
    SocialLinkUpdate,
    SocialLink
)

class SocialLinkService:
    def __init__(self, db: Session):
        self.db = db

    def get_user_social_links(self, user_id: int) -> List[SocialLink]:
        return self.db.query(DBSocialLink).filter(
            DBSocialLink.user_id == user_id
        ).all()

    def get_social_link(self, link_id: int, user_id: int) -> SocialLink:
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
        self, user_id: int, social_link: SocialLinkCreate
    ) -> SocialLink:
        # Check if platform already exists for user
        existing_link = self.db.query(DBSocialLink).filter(
            DBSocialLink.user_id == user_id,
            DBSocialLink.platform == social_link.platform
        ).first()
        
        if existing_link:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Social link for platform {social_link.platform} already exists for user {user_id}"
            )
            
        db_link = DBSocialLink(
            user_id=user_id,
            **social_link.dict()
        )
        self.db.add(db_link)
        self.db.commit()
        self.db.refresh(db_link)
        return db_link

    def update_social_link(
        self, link_id: int, user_id: int, social_link: SocialLinkUpdate
    ) -> SocialLink:
        db_link = self.get_social_link(link_id, user_id)
        
        update_data = social_link.dict(exclude_unset=True)
        for field, value in update_data.items():
            setattr(db_link, field, value)
            
        self.db.commit()
        self.db.refresh(db_link)
        return db_link

    def delete_social_link(self, link_id: int, user_id: int) -> dict:
        db_link = self.get_social_link(link_id, user_id)
        self.db.delete(db_link)
        self.db.commit()
        return {"message": "Social link deleted successfully"}
