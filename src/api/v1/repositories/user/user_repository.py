from fastapi import HTTPException
from sqlalchemy.orm import Session
from typing import List
from datetime import datetime

from core.security.password import get_password_hash
from api.v1.models.user.user import User
from api.v1.models.user.tech_stack import UserTechStack
from api.v1.models.user.interest import UserInterest
from api.v1.models.user.social_link import UserSocialLink
from api.v1.models.user.collaboration_preference import CollaborationPreference
from api.v1.schemas.user.user_schema import UserCreate, UserUpdate, UserDetail

class UserRepository:
  def __init__(self, db: Session):
    self.db = db
    
  def get(self, user_id: int) -> UserDetail:
    """Get user by ID with related resource URLs"""
    db_user = self.db.query(User).filter(User.id == user_id).first()
    if not db_user:
      raise HTTPException(status_code=404, detail="User not found")
    
    # Create user detail with related resource URLs
    user_dict = {
        "id": db_user.id,
        "name": db_user.name,
        "email": db_user.email,
        "profile_image": db_user.profile_image,
        "bio": db_user.bio,
        "role": db_user.role,
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
    }
    
    user_detail = UserDetail(**user_dict)
    return user_detail
  
  def get_by_email(self, email: str) -> User:
    return self.db.query(User).filter(User.email == email).first()
  
  def get_all(self) -> List[User]:
    return self.db.query(User).all()
  
  def get_multi(self, skip: int = 0, limit: int = 100) -> List[User]:
    return self.db.query(User).offset(skip).limit(limit).all()
    
  def create(self, user: UserCreate) -> User:
    db_user = self.get_by_email(user.email)
    if db_user:
      raise HTTPException(status_code=400, detail="이미 존재하는 이메일입니다.")
    
    # 기본 알림 설정
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
    
    # 사용자가 제공한 알림 설정이 있으면 병합
    if user.notification_settings:
      default_notification_settings.update(user.notification_settings)
    
    # OAuth 사용자의 경우 비밀번호가 없을 수 있음
    hashed_password = None
    if user.password:
      hashed_password = get_password_hash(user.password)
    
    db_obj = User(
      email=user.email,
      name=user.name,
      hashed_password=hashed_password,
      profile_image=user.profile_image,
      bio=user.bio,
      role=user.role,
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
    
  def update(self, user_id: int, user: UserUpdate) -> User:
    """사용자 정보 업데이트"""
    update_data = user.model_dump(exclude_unset=True)
    db_user = self.get(user_id)
    
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
    return db_user
  
  def remove(self, user_id: int) -> User:
    db_user = self.get(user_id)
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
    user = self.get(user_id)
    if not user:
      raise HTTPException(status_code=404, detail="User not found")
    
    other_users = self.db.query(User).filter(User.id != user_id).all()
    return [UserDetail.model_validate(user, from_attributes=True) for user in other_users]