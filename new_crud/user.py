from typing import Optional, List, Dict, Any
from sqlalchemy.orm import Session
from fastapi import HTTPException, status
from new_models.user import (
    User, CollaborationPreference, 
    UserInterest, UserSocialLink
)
from new_models.tech_stack import TechStack
from new_models.project import Project
from new_schemas.user import (
    UserCreate, UserUpdate, UserTechStackCreate, 
    CollaborationPreferenceCreate, UserProjectCreate,
    UserInterestCreate, NotificationSettingsUpdate,
    UserSocialLinkCreate
)
from new_crud.base import CRUDBase
import bcrypt

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
        
        db_obj = User(
            email=obj_in.email,
            name=obj_in.name,
            hashed_password=get_password_hash(obj_in.password),
            profile_image=obj_in.profile_image,
            bio=obj_in.bio,
            role=obj_in.role,
            notification_settings=default_notification_settings,
        )
        db.add(db_obj)
        db.flush()  # db_obj.id 확보
        
        # 협업 선호도
        if obj_in.collaboration_preferences:
            for pref in obj_in.collaboration_preferences:
                db.add(CollaborationPreference(
                    user_id=db_obj.id,
                    preference_type=pref.preference_type,
                    preference_value=pref.preference_value
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
            
        return super().update(db, db_obj=db_obj, obj_in=update_data)
    
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
        return user
    
    def get_projects(self, db: Session, *, user_id: int) -> List:
        """사용자의 프로젝트 목록 조회"""
        user = self.get(db, id=user_id)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="사용자를 찾을 수 없습니다."
            )
        return user.projects
    
    def get_tasks(self, db: Session, *, user_id: int) -> List:
        """사용자의 업무 목록 조회"""
        user = self.get(db, id=user_id)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="사용자를 찾을 수 없습니다."
            )
        return user.assigned_tasks
    
    # 알림 설정 관련 CRUD 메서드
    def update_notification_settings(self, db: Session, *, user_id: int, settings_in: NotificationSettingsUpdate) -> Dict[str, int]:
        """사용자 알림 설정 업데이트"""
        user = self.get(db, id=user_id)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="사용자를 찾을 수 없습니다."
            )
        
        # 현재 설정 가져오기
        current_settings = user.notification_settings or {}
        
        # 새 설정으로 업데이트
        update_data = settings_in.model_dump(exclude_unset=True)
        current_settings.update(update_data)
        
        # 데이터베이스 업데이트
        user.notification_settings = current_settings
        db.commit()
        db.refresh(user)
        
        return current_settings
    
    def get_notification_settings(self, db: Session, *, user_id: int) -> Dict[str, int]:
        """사용자 알림 설정 조회"""
        user = self.get(db, id=user_id)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="사용자를 찾을 수 없습니다."
            )
        
        return user.notification_settings or {
            "emailEnable": 1,
            "taskNotification": 1,
            "milestoneNotification": 1,
            "scheduleNotification": 1,
            "deadlineNotification": 1,
            "weeklyReport": 1,
            "pushNotification": 1,
            "securityNotification": 1
        }
    
    # 기술 스택 관련 CRUD 메서드
    def add_tech_stack(self, db: Session, *, user_id: int, tech_stack_in: UserTechStackCreate) -> Dict:
        """사용자에게 기술 스택 추가"""
        user = self.get(db, id=user_id)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="사용자를 찾을 수 없습니다."
            )
        
        tech_stack = db.query(TechStack).filter(TechStack.id == tech_stack_in.tech_stack_id).first()
        if not tech_stack:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="기술 스택을 찾을 수 없습니다."
            )
        
        # 이미 연결되어 있는지 확인
        existing = db.execute(
            """
            SELECT * FROM user_tech_stacks 
            WHERE user_id = :user_id AND tech_stack_id = :tech_stack_id
            """,
            {"user_id": user_id, "tech_stack_id": tech_stack_in.tech_stack_id}
        ).fetchone()
        
        if existing:
            # 이미 있으면 업데이트
            db.execute(
                """
                UPDATE user_tech_stacks 
                SET proficiency_level = :proficiency_level, 
                    years_experience = :years_experience
                WHERE user_id = :user_id AND tech_stack_id = :tech_stack_id
                """,
                {
                    "user_id": user_id, 
                    "tech_stack_id": tech_stack_in.tech_stack_id,
                    "proficiency_level": tech_stack_in.proficiency_level,
                    "years_experience": tech_stack_in.years_experience
                }
            )
        else:
            # 없으면 새로 추가
            db.execute(
                """
                INSERT INTO user_tech_stacks 
                (user_id, tech_stack_id, proficiency_level, years_experience) 
                VALUES (:user_id, :tech_stack_id, :proficiency_level, :years_experience)
                """,
                {
                    "user_id": user_id, 
                    "tech_stack_id": tech_stack_in.tech_stack_id,
                    "proficiency_level": tech_stack_in.proficiency_level,
                    "years_experience": tech_stack_in.years_experience
                }
            )
        
        db.commit()
        
        # 응답 데이터 구성
        result = {
            "tech_stack": tech_stack,
            "proficiency_level": tech_stack_in.proficiency_level,
            "years_experience": tech_stack_in.years_experience
        }
        
        return result
    
    def remove_tech_stack(self, db: Session, *, user_id: int, tech_stack_id: int) -> Dict:
        """사용자에서 기술 스택 제거"""
        user = self.get(db, id=user_id)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="사용자를 찾을 수 없습니다."
            )
        
        # 연결 삭제
        result = db.execute(
            """
            DELETE FROM user_tech_stacks 
            WHERE user_id = :user_id AND tech_stack_id = :tech_stack_id
            RETURNING user_id
            """,
            {"user_id": user_id, "tech_stack_id": tech_stack_id}
        ).fetchone()
        
        if not result:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="사용자에게 해당 기술 스택이 없습니다."
            )
        
        db.commit()
        
        return {"status": "success", "message": "기술 스택이 삭제되었습니다."}
    
    def get_tech_stacks(self, db: Session, *, user_id: int) -> List[Dict]:
        """사용자의 기술 스택 목록 조회"""
        user = self.get(db, id=user_id)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="사용자를 찾을 수 없습니다."
            )
        
        # 사용자의 기술 스택과 추가 정보 조회
        tech_stacks_with_info = db.execute(
            """
            SELECT ts.*, uts.proficiency_level, uts.years_experience 
            FROM tech_stacks ts
            JOIN user_tech_stacks uts ON ts.id = uts.tech_stack_id
            WHERE uts.user_id = :user_id
            """,
            {"user_id": user_id}
        ).fetchall()
        
        result = []
        for row in tech_stacks_with_info:
            tech_stack = TechStack(
                id=row.id,
                name=row.name,
                category=row.category,
                icon_url=row.icon_url
            )
            
            result.append({
                "tech_stack": tech_stack,
                "proficiency_level": row.proficiency_level,
                "years_experience": row.years_experience
            })
        
        return result
    
    # 협업 선호도 관련 CRUD 메서드
    def create_collaboration_preference(self, db: Session, *, user_id: int, pref_in: CollaborationPreferenceCreate) -> CollaborationPreference:
        """사용자의 협업 선호도 생성"""
        user = self.get(db, id=user_id)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="사용자를 찾을 수 없습니다."
            )
        
        # 이미 같은 타입의 선호도가 있는지 확인
        existing = db.query(CollaborationPreference).filter(
            CollaborationPreference.user_id == user_id,
            CollaborationPreference.preference_type == pref_in.preference_type
        ).first()
        
        if existing:
            # 업데이트
            existing.preference_value = pref_in.preference_value
            db.commit()
            db.refresh(existing)
            return existing
        
        # 새로 생성
        db_obj = CollaborationPreference(
            user_id=user_id,
            preference_type=pref_in.preference_type,
            preference_value=pref_in.preference_value
        )
        
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        
        return db_obj
    
    def delete_collaboration_preference(self, db: Session, *, user_id: int, pref_id: int) -> Dict:
        """사용자의 협업 선호도 삭제"""
        pref = db.query(CollaborationPreference).filter(
            CollaborationPreference.id == pref_id,
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

# CRUDUser 클래스 인스턴스 생성
user = CRUDUser(User) 