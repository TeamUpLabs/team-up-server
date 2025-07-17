from typing import Optional, List, Dict, Any
from sqlalchemy.orm import Session
from fastapi import HTTPException, status
from models.user import (
    User, CollaborationPreference, 
    UserInterest, UserSocialLink, UserTechStack
)
from models.notification import Notification
from models.project import Project
from schemas.user import (
    UserCreate, UserUpdate, 
    CollaborationPreferenceCreate, UserProjectCreate,
    UserInterestCreate, NotificationSettingsUpdate,
    UserSocialLinkCreate
)
from crud.base import CRUDBase
import bcrypt
from datetime import datetime

# 패스워드 해싱 함수를 로컬에 정의
def verify_password(plain_password: str, hashed_password: str) -> bool:
    try:
        # Convert the stored hash back to bytes
        hashed_bytes = hashed_password.encode('utf-8')
        # Check the password
        return bcrypt.checkpw(plain_password.encode('utf-8'), hashed_bytes)
    except Exception:
        return False

def get_password_hash(password: str) -> str:
    # Generate a salt and hash the password
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(password.encode('utf-8'), salt)
    # Return the hash as a string
    return hashed.decode('utf-8')

class CRUDUser(CRUDBase[User, UserCreate, UserUpdate]):
    """사용자 모델에 대한 CRUD 작업"""
    
    def get_by_email(self, db: Session, *, email: str) -> Optional[User]:
        """이메일로 사용자 조회"""
        return db.query(User).filter(User.email == email).first()
    
    def get_user_by_id(self, db: Session, *, user_id: int) -> Optional[User]:
        """ID로 사용자 조회"""
        return db.query(User).filter(User.id == user_id).first()
    
    def create(self, db: Session, *, obj_in: UserCreate) -> User:
        """
        새 사용자 생성
        비밀번호 해싱 처리 및 관련 정보(협업 선호도, 관심분야, 알림설정, 소셜링크) 함께 생성
        """
        user = db.query(User).filter(User.email == obj_in.email).first()
        if user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="이미 등록된 이메일입니다."
            )
        
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
        if obj_in.notification_settings:
            default_notification_settings.update(obj_in.notification_settings)
        
        # OAuth 사용자의 경우 비밀번호가 없을 수 있음
        hashed_password = None
        if obj_in.password:
            hashed_password = get_password_hash(obj_in.password)
        
        db_obj = User(
            email=obj_in.email,
            name=obj_in.name,
            hashed_password=hashed_password,
            profile_image=obj_in.profile_image,
            bio=obj_in.bio,
            role=obj_in.role,
            status=obj_in.status,
            languages=obj_in.languages,
            phone=obj_in.phone,
            birth_date=obj_in.birth_date,
            auth_provider=obj_in.auth_provider,
            auth_provider_id=obj_in.auth_provider_id,
            auth_provider_access_token=obj_in.auth_provider_access_token,
            notification_settings=default_notification_settings,
        )
        db.add(db_obj)
        db.flush()  # db_obj.id 확보
        
        # 협업 선호도
        if obj_in.collaboration_preference:
            db.add(CollaborationPreference(
                user_id=db_obj.id,
                collaboration_style=obj_in.collaboration_preference.collaboration_style,
                preferred_project_type=obj_in.collaboration_preference.preferred_project_type,
                preferred_role=obj_in.collaboration_preference.preferred_role,
                available_time_zone=obj_in.collaboration_preference.available_time_zone,
                work_hours_start=obj_in.collaboration_preference.work_hours_start,
                work_hours_end=obj_in.collaboration_preference.work_hours_end,
                preferred_project_length=obj_in.collaboration_preference.preferred_project_length
            ))
                
        # 기술 스택
        if obj_in.tech_stacks:
            for tech_stack in obj_in.tech_stacks:
                db.add(UserTechStack(
                    user_id=db_obj.id,
                    tech=tech_stack.tech,
                    level=tech_stack.level
                ))
                
        # 관심분야
        if obj_in.interests:
            for interest in obj_in.interests:
                db.add(UserInterest(
                    user_id=db_obj.id,
                    interest_category=interest.interest_category,
                    interest_name=interest.interest_name
                ))
        # 소셜링크
        if obj_in.social_links:
            for link in obj_in.social_links:
                db.add(UserSocialLink(
                    user_id=db_obj.id,
                    platform=link.platform,
                    url=link.url
                ))
        db.commit()
        db.refresh(db_obj)
        return db_obj
    
    def update(self, db: Session, *, db_obj: User, obj_in: UserUpdate) -> User:
        """사용자 정보 업데이트"""
        update_data = obj_in.model_dump(exclude_unset=True)
        
        # 비밀번호가 제공되면 해싱 처리
        if "password" in update_data:
            hashed_password = get_password_hash(update_data["password"])
            update_data["hashed_password"] = hashed_password
            del update_data["password"]
            
        # Store relationship data and remove from update_data to prevent direct assignment
        social_links_data = update_data.pop("social_links", None)
        tech_stacks_data = update_data.pop("tech_stacks", None)
        interests_data = update_data.pop("interests", None)
        
        # First update the user object with non-relationship fields
        db_obj = super().update(db, db_obj=db_obj, obj_in=update_data)
        
        # Update relationships if they were provided
        if social_links_data is not None:
            self._update_social_links(db, db_obj, social_links_data)
            
        if tech_stacks_data is not None:
            self._update_tech_stacks(db, db_obj, tech_stacks_data)
            
        if interests_data is not None:
            self._update_interests(db, db_obj, interests_data)
            
        db.commit()
        db.refresh(db_obj)
        return db_obj
        
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
        existing_interests = {(i.interest_category, i.interest_name): i 
                            for i in db_obj.interests}
        
        # Track which interests are being updated
        updated_interests = set()
        
        for interest_data in interests_data:
            category = (interest_data.get("interest_category") 
                      if isinstance(interest_data, dict) 
                      else interest_data.interest_category)
            name = (interest_data.get("interest_name") 
                   if isinstance(interest_data, dict) 
                   else interest_data.interest_name)
            
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
    
    def update_last_login(self, db: Session, *, user_id: int) -> User:
        """사용자 마지막 로그인 시간 업데이트"""
        user = self.get(db, id=user_id)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="사용자를 찾을 수 없습니다."
            )
        
        user.last_login = datetime.utcnow()
        db.commit()
        db.refresh(user)
        return user
    
    def logout(self, db: Session, *, user_id: int) -> Dict:
        """사용자 로그아웃"""
        user = self.get(db, id=user_id)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="사용자를 찾을 수 없습니다."
            )
        user.status = "inactive"
        db.commit()
        db.refresh(user)
        return {"status": "success", "message": "로그아웃되었습니다."}
    
    def authenticate(self, db: Session, *, email: str, password: str) -> Optional[User]:
        """
        사용자 인증
        이메일과 비밀번호로 사용자를 인증하고, 성공 시 사용자 객체 반환
        """
        user = self.get_by_email(db, email=email)
        if not user:
            return None
        if not verify_password(password, user.hashed_password):
            return None
        
        # 로그인 성공 시 last_login 업데이트
        self.update_last_login(db, user_id=user.id)
        return user
    
    def authenticate_oauth(self, db: Session, *, email: str, auth_provider: str, auth_provider_id: str) -> Optional[User]:
        """
        OAuth 사용자 인증
        이메일과 OAuth 제공자 정보로 사용자를 인증하고, 성공 시 사용자 객체 반환
        """
        user = self.get_by_email(db, email=email)
        if not user:
            return None
        if user.auth_provider != auth_provider or user.auth_provider_id != auth_provider_id:
            return None
        
        # 로그인 성공 시 last_login 업데이트
        self.update_last_login(db, user_id=user.id)
        return user
    
    def get_or_create_oauth_user(self, db: Session, *, user_data: dict) -> User:
        """
        OAuth 사용자 조회 또는 생성
        기존 사용자가 있으면 반환하고, 없으면 새로 생성
        """
        # 기존 사용자 조회
        user = self.get_by_email(db, email=user_data["email"])
        if user:
            # 기존 사용자의 OAuth 정보 업데이트
            user.auth_provider = user_data.get("auth_provider", user.auth_provider)
            user.auth_provider_id = user_data.get("auth_provider_id", user.auth_provider_id)
            user.auth_provider_access_token = user_data.get("auth_provider_access_token", user.auth_provider_access_token)
            user.last_login = datetime.now()
            user.status = "active"
            db.commit()
            db.refresh(user)
            return user
        
        # 새 사용자 생성
        user_create_data = UserCreate(
            email=user_data["email"],
            name=user_data["name"],
            password=None,  # OAuth 사용자는 비밀번호 없음
            profile_image=user_data.get("profile_image"),
            bio=user_data.get("bio"),
            role=user_data.get("role"),
            status=user_data.get("status", "active"),
            languages=user_data.get("languages"),
            phone=user_data.get("phone"),
            birth_date=user_data.get("birth_date"),
            auth_provider=user_data.get("auth_provider", "github"),
            auth_provider_id=user_data.get("auth_provider_id"),
            auth_provider_access_token=user_data.get("auth_provider_access_token"),
            collaboration_preference=user_data.get("collaboration_preference"),
            interests=user_data.get("interests"),
            notification_settings=user_data.get("notification_settings"),
            social_links=user_data.get("social_links"),
            tech_stacks=user_data.get("tech_stacks")
        )
        
        return self.create(db, obj_in=user_create_data)
    
    def get_projects(self, db: Session, *, user_id: int) -> List:
        """사용자의 프로젝트 목록 조회"""
        user = self.get(db, id=user_id)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="사용자를 찾을 수 없습니다."
            )
        return user.projects
    

    
    # 알림 설정 관련 CRUD 메서드
    def update_notification_settings(self, db: Session, *, user_id: int, settings_in: NotificationSettingsUpdate) -> Dict[str, int]:
        """사용자 알림 설정 업데이트"""
        # 사용자 조회
        user = db.query(self.model).filter(self.model.id == user_id).first()
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
    
    def get_notification_settings(self, db: Session, *, user_id: int) -> Dict[str, int]:
        """사용자 알림 설정 조회"""
        user = db.query(self.model).filter(self.model.id == user_id).first()
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="사용자를 찾을 수 없습니다."
            )
        
        # 기본값 반환 (None인 경우 기본값 사용)
        default_settings = {
            "emailEnable": 1,
            "taskNotification": 1,
            "milestoneNotification": 1,
            "scheduleNotification": 1,
            "deadlineNotification": 1,
            "weeklyReport": 1,
            "pushNotification": 1,
            "securityNotification": 1
        }
        
        current_settings = getattr(user, 'notification_settings', None)
        if not current_settings:
            return default_settings
            
        # 기존 설정에 기본값 병합 (누락된 키가 있으면 기본값으로 채움)
        return {**default_settings, **current_settings}
    # 협업 선호도 관련 CRUD 메서드
    def create_collaboration_preference(self, db: Session, *, user_id: int, pref_in: CollaborationPreferenceCreate) -> CollaborationPreference:
        """사용자의 협업 선호도 생성 또는 업데이트"""
        user = self.get(db, id=user_id)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="사용자를 찾을 수 없습니다."
            )
        
        # 이미 협업 선호도가 있는지 확인
        existing = db.query(CollaborationPreference).filter(
            CollaborationPreference.user_id == user_id
        ).first()
        
        if existing:
            # 업데이트
            for field, value in pref_in.model_dump(exclude_unset=True).items():
                setattr(existing, field, value)
            db.commit()
            db.refresh(existing)
            return existing
        
        # 새로 생성
        db_obj = CollaborationPreference(
            user_id=user_id,
            collaboration_style=pref_in.collaboration_style,
            preferred_project_type=pref_in.preferred_project_type,
            preferred_role=pref_in.preferred_role,
            available_time_zone=pref_in.available_time_zone,
            work_hours_start=pref_in.work_hours_start,
            work_hours_end=pref_in.work_hours_end,
            preferred_project_length=pref_in.preferred_project_length
        )
        
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        
        return db_obj
    
    def delete_collaboration_preference(self, db: Session, *, user_id: int) -> Dict:
        """사용자의 협업 선호도 삭제"""
        pref = db.query(CollaborationPreference).filter(
            CollaborationPreference.user_id == user_id
        ).first()
        
        if not pref:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="해당 협업 선호도를 찾을 수 없습니다."
            )
        
        db.delete(pref)
        db.commit()
        
        return {"status": "success", "message": "협업 선호도가 삭제되었습니다."}
    
    # 사용자 관심분야 관련 CRUD 메서드
    def create_user_interest(self, db: Session, *, user_id: int, interest_in: UserInterestCreate) -> UserInterest:
        """사용자 관심분야 생성"""
        user = self.get(db, id=user_id)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="사용자를 찾을 수 없습니다."
            )
        
        # 이미 동일한 관심분야가 있는지 확인
        existing = db.query(UserInterest).filter(
            UserInterest.user_id == user_id,
            UserInterest.interest_category == interest_in.interest_category,
            UserInterest.interest_name == interest_in.interest_name
        ).first()
        
        if existing:
            return existing
        
        # 새로 생성
        db_obj = UserInterest(
            user_id=user_id,
            interest_category=interest_in.interest_category,
            interest_name=interest_in.interest_name
        )
        
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        
        return db_obj
    
    def delete_user_interest(self, db: Session, *, user_id: int, interest_id: int) -> Dict:
        """사용자 관심분야 삭제"""
        interest = db.query(UserInterest).filter(
            UserInterest.id == interest_id,
            UserInterest.user_id == user_id
        ).first()
        
        if not interest:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="해당 관심분야를 찾을 수 없습니다."
            )
        
        db.delete(interest)
        db.commit()
        
        return {"status": "success", "message": "관심분야가 삭제되었습니다."}
    
    # 소셜 링크 관련 CRUD 메서드
    def create_social_link(self, db: Session, *, user_id: int, link_in: UserSocialLinkCreate) -> UserSocialLink:
        """사용자 소셜 링크 생성"""
        user = self.get(db, id=user_id)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="사용자를 찾을 수 없습니다."
            )
        
        # 이미 동일한 플랫폼의 링크가 있는지 확인
        existing = db.query(UserSocialLink).filter(
            UserSocialLink.user_id == user_id,
            UserSocialLink.platform == link_in.platform
        ).first()
        
        if existing:
            # 업데이트
            existing.url = link_in.url
            db.commit()
            db.refresh(existing)
            return existing
        
        # 새로 생성
        db_obj = UserSocialLink(
            user_id=user_id,
            platform=link_in.platform,
            url=link_in.url
        )
        
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        
        return db_obj
    
    def delete_social_link(self, db: Session, *, user_id: int, link_id: int) -> Dict:
        """사용자 소셜 링크 삭제"""
        link = db.query(UserSocialLink).filter(
            UserSocialLink.id == link_id,
            UserSocialLink.user_id == user_id
        ).first()
        
        if not link:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="해당 소셜 링크를 찾을 수 없습니다."
            )
        
        db.delete(link)
        db.commit()
        
        return {"status": "success", "message": "소셜 링크가 삭제되었습니다."}
    
    # 알림 관련 CRUD 메서드
    def get_notifications(self, db: Session, *, user_id: int, skip: int = 0, limit: int = 50) -> List[Notification]:
        """사용자의 알림 목록 조회"""
        user = self.get(db, id=user_id)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="사용자를 찾을 수 없습니다."
            )
        
        return db.query(Notification).filter(
            Notification.receiver_id == user_id
        ).order_by(Notification.timestamp.desc()).offset(skip).limit(limit).all()
    
    def get_unread_notification_count(self, db: Session, *, user_id: int) -> int:
        """사용자의 읽지 않은 알림 개수 조회"""
        user = self.get(db, id=user_id)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="사용자를 찾을 수 없습니다."
            )
        
        return db.query(Notification).filter(
            Notification.receiver_id == user_id,
            Notification.is_read == False
        ).count()

# CRUDUser 클래스 인스턴스 생성
user = CRUDUser(User) 