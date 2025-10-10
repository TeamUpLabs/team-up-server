from fastapi import HTTPException
from sqlalchemy.orm import Session
from typing import List
from datetime import datetime

from src.core.security.password import get_password_hash
from src.api.v1.models.user.user import User
from src.api.v1.models.user.tech_stack import UserTechStack
from src.api.v1.models.user.interest import UserInterest
from src.api.v1.models.user.social_link import UserSocialLink
from src.api.v1.models.user.collaboration_preference import CollaborationPreference
from src.api.v1.schemas.user.user_schema import UserCreate, UserUpdate, UserDetail, UserNolinks
from src.api.v1.schemas.brief import UserBrief
from src.api.v1.schemas.user.follow_schema import FollowList
from src.api.v1.schemas.user.user_schema import UserNolinks

class UserRepository:
  def __init__(self, db: Session):
    self.db = db
    
  def get(self, user_id: int) -> UserDetail:
    """Get user by ID with related resource URLs"""
    db_user = self.db.query(User).filter(User.id == user_id).first()
    if not db_user:
      raise HTTPException(status_code=404, detail="User not found")
    
    following_users = db_user.following.all()
    followers_users = db_user.followers.all()
    
    following_briefs = [UserBrief.model_validate(user, from_attributes=True) for user in following_users]
    followers_briefs = [UserBrief.model_validate(user, from_attributes=True) for user in followers_users]
    
    following_list = FollowList(count=len(following_briefs), users=following_briefs)
    followers_list = FollowList(count=len(followers_briefs), users=followers_briefs)
    
    user_dict = {
        "id": db_user.id,
        "name": db_user.name,
        "email": db_user.email,
        "profile_image": db_user.profile_image,
        "bio": db_user.bio,
        "job": db_user.job,
        "languages": db_user.languages,
        "phone": db_user.phone,
        "birth_date": db_user.birth_date,
        "status": db_user.status,
        "created_at": db_user.created_at,
        "updated_at": db_user.updated_at,
        "last_login": db_user.last_login,
        "auth_provider": db_user.auth_provider,
        "auth_provider_id": db_user.auth_provider_id,
        "auth_provider_access_token": db_user.auth_provider_access_token,
        "notification_settings": db_user.notification_settings,
        "following": following_list,
        "followers": followers_list,
    }
    
    user_detail = UserDetail(**user_dict)
    return user_detail
  def get_user_brief(self, user_id: int) -> UserBrief:
    db_user = self.db.query(User).filter(User.id == user_id).first()
    if not db_user:
      raise HTTPException(status_code=404, detail="User not found")
    
    user_brief = UserBrief.model_validate(db_user, from_attributes=True)
    return user_brief
  
  def get_by_email(self, email: str) -> User:
    return self.db.query(User).filter(User.email == email).first()
  
  def get_all(self) -> List[User]:
    return self.db.query(User).all()
  
  def get_multi(self, skip: int = 0, limit: int = 100) -> List[User]:
    return self.db.query(User).offset(skip).limit(limit).all()
    
  def create(self, user: UserCreate) -> User:
    existing = self.get_by_email(user.email)
    if existing:
      raise HTTPException(status_code=400, detail=f"User with email {user.email} already exists")

    try:
      default_notification_settings = {
        "emailEnable": 1,
        "taskNotification": 1,
        "milestoneNotification": 1,
        "scheduleNotification": 1,
        "deadlineNotification": 1,
        "weeklyReport": 1,
        "pushNotification": 1,
        "securityNotification": 1
      }
      
      if user.notification_settings:
        default_notification_settings.update(user.notification_settings)
      
      hashed_password = None
      if user.password:
        hashed_password = get_password_hash(user.password)
      
      db_obj = User(
        email=user.email,
        name=user.name,
        hashed_password=hashed_password,
        profile_image=user.profile_image,
        bio=user.bio,
        job=user.job,
        status=user.status,
        languages=user.languages,
        phone=user.phone,
        birth_date=user.birth_date,
        auth_provider=user.auth_provider,
        auth_provider_id=user.auth_provider_id,
        auth_provider_access_token=user.auth_provider_access_token,
        notification_settings=default_notification_settings,
      )
      self.db.add(db_obj)
      self.db.flush()  # db_obj.id 확보
      
      # 협업 선호도
      if user.collaboration_preference:
        self.db.add(CollaborationPreference(
          user_id=db_obj.id,
          collaboration_style=user.collaboration_preference.collaboration_style,
          preferred_project_type=user.collaboration_preference.preferred_project_type,
          preferred_role=user.collaboration_preference.preferred_role,
          available_time_zone=user.collaboration_preference.available_time_zone,
          work_hours_start=user.collaboration_preference.work_hours_start,
          work_hours_end=user.collaboration_preference.work_hours_end,
          preferred_project_length=user.collaboration_preference.preferred_project_length
        ))
              
      # 기술 스택
      if user.tech_stacks:
        for tech_stack in user.tech_stacks:
          self.db.add(UserTechStack(
            user_id=db_obj.id,
            tech=tech_stack.tech,
            level=tech_stack.level
          ))
              
      # 관심분야
      if user.interests:
        for interest in user.interests:
          self.db.add(UserInterest(
            user_id=db_obj.id,
            interest_category=interest.interest_category,
            interest_name=interest.interest_name
          ))
      # 소셜링크
      if user.social_links:
        for link in user.social_links:
          self.db.add(UserSocialLink(
            user_id=db_obj.id,
            platform=link.platform,
            url=link.url
          ))

      self.db.commit()
      self.db.refresh(db_obj)
      
      return db_obj
    except Exception as e:
      raise HTTPException(status_code=500, detail=str(e))
    
    
  def update(self, user_id: int, user: UserUpdate) -> UserDetail:
    """사용자 정보 업데이트"""
    update_data = user.model_dump(exclude_unset=True)
    
    # Get the actual SQLAlchemy User model instead of UserDetail schema
    db_user = self.db.query(User).filter(User.id == user_id).first()
    if not db_user:
      raise HTTPException(status_code=404, detail="User not found")
    
    # 비밀번호가 제공되면 해싱 처리
    if "password" in update_data:
      hashed_password = get_password_hash(update_data["password"])
      update_data["hashed_password"] = hashed_password
      del update_data["password"]
        
    # Store relationship data and remove from update_data to prevent direct assignment
    social_links_data = update_data.pop("social_links", None)
    tech_stacks_data = update_data.pop("tech_stacks", None)
    interests_data = update_data.pop("interests", None)
    collaboration_preference_data = update_data.pop("collaboration_preference", None)
    
    # Update basic user fields
    for field, value in update_data.items():
      if hasattr(db_user, field):
        setattr(db_user, field, value)
    
    # Update relationships if they were provided
    if social_links_data is not None:
        self._update_social_links(self.db, db_user, social_links_data)
        
    if tech_stacks_data is not None:
        self._update_tech_stacks(self.db, db_user, tech_stacks_data)
        
    if interests_data is not None:
        self._update_interests(self.db, db_user, interests_data)
        
    if collaboration_preference_data is not None:
        self._update_collaboration_preference(self.db, db_user, collaboration_preference_data)
        
    self.db.commit()
    self.db.refresh(db_user)
    
    # Return UserDetail schema
    return self.get(user_id)
  
  def remove(self, user_id: int) -> User:
    # Get the actual SQLAlchemy User model instead of UserDetail schema
    db_user = self.db.query(User).filter(User.id == user_id).first()
    if not db_user:
      raise HTTPException(status_code=404, detail="User not found")
    self.db.delete(db_user)
    self.db.commit()
    return db_user
          
  def update_last_login(self, user_id: int) -> User:
    """Update the user's last login time"""
    user = self.db.get(User, user_id)
    if not user:
      raise HTTPException(
        status_code=404,
        detail="User not found"
      )
    
    user.last_login = datetime.now()
    self.db.commit()
    self.db.refresh(user)
    return user
  

  def get_users_exclude_me(self, user_id: int) -> List[UserDetail]:
    """Get all users except the current user"""
    user = self.db.query(User).filter(User.id == user_id).first()
    if not user:
      raise HTTPException(status_code=404, detail="User not found")
    
    other_users = self.db.query(User).filter(User.id != user_id).all()
    
    result = []
    for user in other_users:
      following_users = user.following.all()
      followers_users = user.followers.all()
      
      following_briefs = [UserBrief.model_validate(u, from_attributes=True) for u in following_users]
      followers_briefs = [UserBrief.model_validate(u, from_attributes=True) for u in followers_users]
      
      following_list = FollowList(count=len(following_briefs), users=following_briefs)
      followers_list = FollowList(count=len(followers_briefs), users=followers_briefs)
      
      user_dict = {
        "id": user.id,
        "name": user.name,
        "email": user.email,
        "profile_image": user.profile_image,
        "bio": user.bio,
        "job": user.job,
        "languages": user.languages,
        "phone": user.phone,
        "birth_date": user.birth_date,
        "status": user.status,
        "created_at": user.created_at,
        "updated_at": user.updated_at,
        "last_login": user.last_login,
        "auth_provider": user.auth_provider,
        "auth_provider_id": user.auth_provider_id,
        "auth_provider_access_token": user.auth_provider_access_token,
        "notification_settings": user.notification_settings,
        "following": following_list,
        "followers": followers_list,
      }
      user_detail = UserDetail(**user_dict)
      result.append(user_detail)
    
    return result
  
  def get_user_by_id_no_links(self, user_id: int) -> UserNolinks:
    from api.v1.schemas.user.collaboration_preference_schema import CollaborationPreference
    from api.v1.schemas.user.tech_stack_schema import TechStack
    from api.v1.schemas.user.interest_schema import Interest
    from api.v1.schemas.user.social_link_schema import SocialLink
    from api.v1.services.project.project_service import ProjectService
    from api.v1.services.user.collaboration_preference_service import CollaborationPreferenceService
    from api.v1.services.user.tech_stack_service import TechStackService
    from api.v1.services.user.interest_service import InterestService
    from api.v1.services.user.social_link_service import SocialLinkService
    
    db_user = self.db.query(User).filter(User.id == user_id).first()
    if not db_user:
      return None
      
    following_users = db_user.following.all()
    followers_users = db_user.followers.all()
    
    following_briefs = [UserBrief.model_validate(u, from_attributes=True) for u in following_users]
    followers_briefs = [UserBrief.model_validate(u, from_attributes=True) for u in followers_users]
    
    following_list = FollowList(count=len(following_briefs), users=following_briefs)
    followers_list = FollowList(count=len(followers_briefs), users=followers_briefs)
    
    project_service = ProjectService(self.db)
    projects = project_service.get_by_user_id(user_id)
    
    collaboration_preference_service = CollaborationPreferenceService(self.db)
    collaboration_preference = collaboration_preference_service.get(user_id)
    
    tech_stack_service = TechStackService(self.db)
    tech_stacks = tech_stack_service.get_user_tech_stacks(user_id)
    
    interest_service = InterestService(self.db)
    interests = interest_service.get_user_interests(user_id)
    
    social_link_service = SocialLinkService(self.db)
    social_links = social_link_service.get_user_social_links(user_id)
    
    user_dict = {
      "id": db_user.id,
      "name": db_user.name,
      "email": db_user.email,
      "profile_image": db_user.profile_image,
      "bio": db_user.bio,
      "job": db_user.job,
      "languages": db_user.languages,
      "phone": db_user.phone,
      "birth_date": db_user.birth_date,
      "status": db_user.status,
      "created_at": db_user.created_at,
      "updated_at": db_user.updated_at,
      "last_login": db_user.last_login,
      "auth_provider": db_user.auth_provider,
      "auth_provider_id": db_user.auth_provider_id,
      "auth_provider_access_token": db_user.auth_provider_access_token,
      "notification_settings": db_user.notification_settings or {},
      "following": following_list,
      "followers": followers_list,
      "projects": projects,
      "collaboration_preference": collaboration_preference,
      "tech_stacks": [{"id": ts.id, "user_id": ts.user_id, "tech": ts.tech} for ts in tech_stacks] if tech_stacks else [],
      "interests": [{"id": i.id, "user_id": i.user_id, "interest_category": i.interest_category, "interest_name": i.interest_name} for i in interests] if interests else [],
      "social_links": [{"id": sl.id, "user_id": sl.user_id, "platform": sl.platform, "url": sl.url} for sl in social_links] if social_links else [],
      "notifications": db_user.received_notifications or [],
      "sessions": db_user.sessions or [],
    }
    
    return UserNolinks(**user_dict)
  
  def _update_social_links(self, db: Session, user: User, social_links_data: List[UserSocialLink]):
    for link in social_links_data:
      db.query(UserSocialLink).filter(UserSocialLink.user_id == user.id, UserSocialLink.platform == link.platform).delete()
      db.add(UserSocialLink(user_id=user.id, **link.model_dump(exclude_unset=True)))
      db.commit()
    return user
  
  def _update_tech_stacks(self, db: Session, user: User, tech_stacks_data: List[UserTechStack]):
    for tech_stack in tech_stacks_data:
      db.query(UserTechStack).filter(UserTechStack.user_id == user.id, UserTechStack.tech == tech_stack.tech).delete()
      db.add(UserTechStack(user_id=user.id, **tech_stack.model_dump(exclude_unset=True)))
      db.commit()
    return user
  
  def _update_interests(self, db: Session, user: User, interests_data: List[UserInterest]):
    for interest in interests_data:
      db.query(UserInterest).filter(UserInterest.user_id == user.id, UserInterest.interest_category == interest.interest_category, UserInterest.interest_name == interest.interest_name).delete()
      db.add(UserInterest(user_id=user.id, **interest.model_dump(exclude_unset=True)))
      db.commit()
    return user
  
  def _update_collaboration_preference(self, db: Session, user: User, collaboration_preference_data: CollaborationPreference):
    db.query(CollaborationPreference).filter(CollaborationPreference.user_id == user.id).delete()
    db.add(CollaborationPreference(user_id=user.id, **collaboration_preference_data.model_dump(exclude_unset=True)))
    db.commit()
    return user