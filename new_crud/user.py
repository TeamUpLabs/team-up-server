from typing import Optional, List
from sqlalchemy.orm import Session
from fastapi import HTTPException, status
from new_models.user import User
from new_schemas.user import UserCreate, UserUpdate
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
        비밀번호 해싱 처리
        """
        user = db.query(User).filter(User.email == obj_in.email).first()
        if user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="이미 등록된 이메일입니다."
            )
            
        db_obj = User(
            email=obj_in.email,
            name=obj_in.name,
            hashed_password=get_password_hash(obj_in.password),
            profile_image=obj_in.profile_image,
            bio=obj_in.bio,
            role=obj_in.role,
        )
        
        db.add(db_obj)
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

# CRUDUser 클래스 인스턴스 생성
user = CRUDUser(User) 