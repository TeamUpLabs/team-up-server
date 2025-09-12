from fastapi import HTTPException
from sqlalchemy.orm import Session, joinedload
from typing import List, Any, Union, Dict, Optional
from api.v1.models.user import User, CollaborationPreference, UserTechStack, UserInterest, UserSocialLink
from api.v1.schemas.user_schema import UserCreate, UserUpdate, NotificationSettings, UserDetail
from api.v1.schemas.brief import ProjectBrief
from datetime import datetime

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
        # These fields will be populated by the UserDetail model's __init__
        "collaboration_preference": None,
        "tech_stacks": None,
        "interests": None,
        "social_links": None,
        "received_notifications": None,
        "sessions": None
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
  
  def _update_social_links(self, db: Session, db_obj: User, social_links_data: List[Any]) -> None:
    """Helper method to update social links"""
    existing_links = {link.platform: link for link in db_obj.social_links}
    
    for link_data in social_links_data:
      platform = link_data.get("platform") if isinstance(link_data, dict) else link_data.platform
      url = link_data.get("url") if isinstance(link_data, dict) else link_data.url
      
      if platform in existing_links:
        # Update existing link
        existing_link = existing_links.pop(platform)
        if existing_link.url != url:
          existing_link.url = url
      else:
        # Add new link
        new_link = UserSocialLink(
          user_id=db_obj.id,
          platform=platform,
          url=url
        )
        db.add(new_link)
    
    # Remove links that are no longer in the update data
    for link in existing_links.values():
      db.delete(link)
      
  def _update_tech_stacks(self, db: Session, db_obj: User, tech_stacks_data: List[Any]) -> None:
    """Helper method to update tech stacks"""
    existing_stacks = {stack.tech: stack for stack in db_obj.tech_stacks}
    
    for stack_data in tech_stacks_data:
      tech = stack_data.get("tech") if isinstance(stack_data, dict) else stack_data.tech
      level = stack_data.get("level") if isinstance(stack_data, dict) else stack_data.level
      
      if tech in existing_stacks:
        # Update existing stack
        existing_stack = existing_stacks.pop(tech)
        if existing_stack.level != level:
          existing_stack.level = level
      else:
        # Add new stack
        new_stack = UserTechStack(
          user_id=db_obj.id,
          tech=tech,
          level=level
        )
        db.add(new_stack)
    
    # Remove stacks that are no longer in the update data
    for stack in existing_stacks.values():
      db.delete(stack)
      
  def _update_interests(self, db: Session, db_obj: User, interests_data: List[Any]) -> None:
    """Helper method to update interests"""
    existing_interests = {(i.interest_category, i.interest_name): i for i in db_obj.interests}
    
    # Track which interests are being updated
    updated_interests = set()
    
    for interest_data in interests_data:
      category = (interest_data.get("interest_category") if isinstance(interest_data, dict) else interest_data.interest_category)
      name = (interest_data.get("interest_name") if isinstance(interest_data, dict) else interest_data.interest_name)
      
      interest_key = (category, name)
      updated_interests.add(interest_key)
      
      if interest_key not in existing_interests:
        # Add new interest
        new_interest = UserInterest(
          user_id=db_obj.id,
          interest_category=category,
          interest_name=name
        )
        db.add(new_interest)
    
    # Remove interests that are no longer in the update data
    for interest_key, interest in existing_interests.items():
      if interest_key not in updated_interests:
        db.delete(interest)
        
  def _update_collaboration_preference(self, db: Session, db_obj: User, preference_data: Union[Dict, Any]) -> None:
    """Helper method to update user's collaboration preference"""
    # Get the existing preference or create a new one if it doesn't exist
    preference = db_obj.collaboration_preference
    
    # If preference_data is a Pydantic model, convert to dict
    if hasattr(preference_data, 'model_dump'):
      preference_data = preference_data.model_dump(exclude_unset=True)
    
    if preference is None:
      # Create new preference
      preference = CollaborationPreference(
        user_id=db_obj.id,
        **preference_data
      )
      db.add(preference)
    else:
      # Update existing preference
      for field, value in preference_data.items():
        if hasattr(preference, field):
          setattr(preference, field, value)
          
  def _update_notification_settings(self, db: Session, *, user_id: int, settings_in: NotificationSettings) -> Dict[str, int]:
    """사용자 알림 설정 업데이트"""
    # 사용자 조회
    user = self.get(db, id=user_id)
    if not user:
      raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail="사용자를 찾을 수 없습니다."
      )
    
    # 현재 설정 가져오기 (기본값이 있는 경우를 위해 getattr 사용)
    current_settings = getattr(user, 'notification_settings', {})
    if current_settings is None:
      current_settings = {}
    
    # 새 설정으로 업데이트 (None이 아닌 값만 업데이트)
    update_data = {k: v for k, v in settings_in.model_dump(exclude_unset=True).items() if v is not None}
    current_settings.update(update_data)
    
    try:
      # 데이터베이스 업데이트
      user.notification_settings = current_settings
      db.add(user)
      db.commit()
      db.refresh(user)
      return current_settings
    except Exception as e:
      db.rollback()
      raise HTTPException(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        detail=f"알림 설정 업데이트 중 오류가 발생했습니다: {str(e)}"
      )
          
  def update_last_login(self, db: Session, *, user_id: int) -> User:
    """사용자 마지막 로그인 시간 업데이트"""
    user = self.get(db, id=user_id)
    if not user:
      raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail="사용자를 찾을 수 없습니다."
      )
    
    user.last_login = datetime.now()
    db.commit()
    db.refresh(user)
    return user