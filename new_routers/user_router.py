from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from typing import List, Dict
from sqlalchemy.orm import Session

from database import get_db
from auth import create_access_token, get_current_user
from new_crud import user
from new_schemas.user import (
    UserCreate, UserUpdate, UserDetail, UserBrief, Token, 
    UserProjectCreate, UserInterestCreate,
    NotificationSettingsUpdate, UserSocialLinkCreate,
    UserProjectResponse, UserInterestResponse,
    UserSocialLinkResponse, CollaborationPreferenceResponse, CollaborationPreferenceCreate,
    OAuthLoginRequest
)
from new_schemas.notification import NotificationResponse
from new_schemas.project import ProjectDetail
from new_models.user import User
from new_routers.project_router import convert_project_to_project_detail
from utils.sse_manager import project_sse_manager
from new_crud import project
import json

router = APIRouter(
    prefix="/api/users",
    tags=["users"]
)

@router.post("/", response_model=UserDetail, status_code=status.HTTP_201_CREATED)
def create_user(user_in: UserCreate, db: Session = Depends(get_db)):
    """새 사용자 등록"""
    db_user = user.create(db=db, obj_in=user_in)
    return UserDetail.model_validate(db_user, from_attributes=True)

@router.post("/token", response_model=Token)
def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    """로그인 및 토큰 발급"""
    db_user = user.authenticate(db, email=form_data.username, password=form_data.password)
    if not db_user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="이메일 또는 비밀번호가 올바르지 않습니다.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token = create_access_token(data={"sub": db_user.email})
    return {
        "access_token": access_token, 
        "token_type": "bearer",
        "user_info": UserBrief.model_validate(db_user, from_attributes=True)
    }

@router.post("/oauth", response_model=Token)
def oauth_login(user_data: OAuthLoginRequest, db: Session = Depends(get_db)):
    """OAuth 로그인 및 토큰 발급"""
    try:
        # OAuth 사용자 조회 또는 생성
        db_user = user.get_or_create_oauth_user(db, user_data=user_data.model_dump())
        access_token = create_access_token(data={"sub": db_user.email})
        return {
            "status": "logged_in",
            "access_token": access_token,
            "user_info": UserBrief.model_validate(db_user, from_attributes=True)
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"OAuth 로그인 중 오류가 발생했습니다: {str(e)}"
        )

@router.get("/me", response_model=UserDetail)
def read_current_user(current_user: User = Depends(get_current_user)):
    """현재 로그인한 사용자 정보 조회"""
    return UserDetail.model_validate(current_user, from_attributes=True)

@router.put("/me", response_model=UserDetail)
async def update_current_user(user_in: UserUpdate, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """현재 로그인한 사용자 정보 수정"""
    db_user = user.update(db=db, db_obj=current_user, obj_in=user_in)
    if db_user.projects:
        for project_id in db_user.projects:
            project_data = convert_project_to_project_detail(project.get(db, project_id), db)
            await project_sse_manager.send_event(
                project_id,
                json.dumps(project_sse_manager.convert_to_dict(project_data))
            )
    return UserDetail.model_validate(db_user, from_attributes=True)

@router.post("/{user_id}/logout")
def logout_user(user_id: int, db: Session = Depends(get_db)):
    """사용자 로그아웃"""
    return user.logout(db=db, user_id=user_id)

@router.get("/{user_id}", response_model=UserDetail)
def read_user(user_id: int, db: Session = Depends(get_db)):
    """특정 사용자 정보 조회"""
    db_user = user.get(db=db, id=user_id)
    if db_user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="사용자를 찾을 수 없습니다.")
    return UserDetail.model_validate(db_user, from_attributes=True)

@router.get("/", response_model=List[UserBrief])
def read_users(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    """사용자 목록 조회"""
    users = user.get_multi(db=db, skip=skip, limit=limit)
    return [UserBrief.model_validate(u, from_attributes=True) for u in users]

@router.get("/{user_id}/projects", response_model=List[ProjectDetail])
def read_user_projects(user_id: int, db: Session = Depends(get_db)):
    """특정 사용자의 프로젝트 목록 조회"""
    projects = user.get_projects(db=db, user_id=user_id)
    return [convert_project_to_project_detail(p, db) for p in projects]



# 알림 설정 관련 엔드포인트
@router.get("/{user_id}/notification-settings", response_model=Dict[str, int])
def get_user_notification_settings(
    user_id: int, 
    db: Session = Depends(get_db), 
    current_user: User = Depends(get_current_user)
):
    """사용자 알림 설정 조회"""
    if current_user.id != user_id and not current_user.role == "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="접근 권한이 없습니다."
        )
    
    return user.get_notification_settings(db=db, user_id=user_id)

@router.put("/{user_id}/notification-settings", response_model=Dict[str, int])
def update_user_notification_settings(
    user_id: int, 
    settings_in: NotificationSettingsUpdate,
    db: Session = Depends(get_db), 
    current_user: User = Depends(get_current_user)
):
    """사용자 알림 설정 업데이트"""
    if current_user.id != user_id and not current_user.role == "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="접근 권한이 없습니다."
        )
    
    return user.update_notification_settings(db=db, user_id=user_id, settings_in=settings_in)

# 협업 선호도 관련 엔드포인트
@router.post("/{user_id}/collaboration-preference", response_model=CollaborationPreferenceResponse)
def create_user_collaboration_preference(
    user_id: int, pref_in: CollaborationPreferenceCreate, 
    db: Session = Depends(get_db), current_user: User = Depends(get_current_user)
):
    """사용자 협업 선호도 생성 또는 업데이트"""
    if current_user.id != user_id and not current_user.role == "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="접근 권한이 없습니다."
        )
    
    db_pref = user.create_collaboration_preference(db=db, user_id=user_id, pref_in=pref_in)
    return CollaborationPreferenceResponse.model_validate(db_pref, from_attributes=True)

@router.delete("/{user_id}/collaboration-preference", response_model=Dict)
def delete_user_collaboration_preference(
    user_id: int, 
    db: Session = Depends(get_db), current_user: User = Depends(get_current_user)
):
    """사용자 협업 선호도 삭제"""
    if current_user.id != user_id and not current_user.role == "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="접근 권한이 없습니다."
        )
    
    return user.delete_collaboration_preference(db=db, user_id=user_id)

@router.put("/{user_id}/collaboration-preference", response_model=CollaborationPreferenceResponse)
def update_user_collaboration_preference(
    user_id: int, pref_in: CollaborationPreferenceCreate,
    db: Session = Depends(get_db), current_user: User = Depends(get_current_user)
):
    """사용자 협업 선호도 업데이트"""
    if current_user.id != user_id and not current_user.role == "admin":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="접근 권한이 없습니다.")
    
    db_pref = user.create_collaboration_preference(db=db, user_id=user_id, pref_in=pref_in)
    return CollaborationPreferenceResponse.model_validate(db_pref, from_attributes=True)

# 사용자 프로젝트 관련 엔드포인트
@router.post("/{user_id}/detailed-projects", response_model=UserProjectResponse)
def create_user_detailed_project(
    user_id: int, proj_in: UserProjectCreate, 
    db: Session = Depends(get_db), current_user: User = Depends(get_current_user)
):
    """사용자 프로젝트 상세 정보 생성"""
    if current_user.id != user_id and not current_user.role == "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="접근 권한이 없습니다."
        )
    
    db_proj = user.create_user_project(db=db, user_id=user_id, proj_in=proj_in)
    return UserProjectResponse.model_validate(db_proj, from_attributes=True)

@router.delete("/{user_id}/detailed-projects/{user_project_id}", response_model=Dict)
def delete_user_detailed_project(
    user_id: int, user_project_id: int, 
    db: Session = Depends(get_db), current_user: User = Depends(get_current_user)
):
    """사용자 프로젝트 상세 정보 삭제"""
    if current_user.id != user_id and not current_user.role == "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="접근 권한이 없습니다."
        )
    
    return user.delete_user_project(db=db, user_id=user_id, user_project_id=user_project_id)

# 사용자 관심분야 관련 엔드포인트
@router.post("/{user_id}/interests", response_model=UserInterestResponse)
def create_user_interest_endpoint(
    user_id: int, interest_in: UserInterestCreate, 
    db: Session = Depends(get_db), current_user: User = Depends(get_current_user)
):
    """사용자 관심분야 생성"""
    if current_user.id != user_id and not current_user.role == "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="접근 권한이 없습니다."
        )
    
    db_interest = user.create_user_interest(db=db, user_id=user_id, interest_in=interest_in)
    return UserInterestResponse.model_validate(db_interest, from_attributes=True)

@router.delete("/{user_id}/interests/{interest_id}", response_model=Dict)
def delete_user_interest_endpoint(
    user_id: int, interest_id: int, 
    db: Session = Depends(get_db), current_user: User = Depends(get_current_user)
):
    """사용자 관심분야 삭제"""
    if current_user.id != user_id and not current_user.role == "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="접근 권한이 없습니다."
        )
    
    return user.delete_user_interest(db=db, user_id=user_id, interest_id=interest_id)

@router.put("/{user_id}/interests/{interest_id}", response_model=UserInterestResponse)
def update_user_interest(
    user_id: int, interest_id: int, interest_in: UserInterestCreate,
    db: Session = Depends(get_db), current_user: User = Depends(get_current_user)
):
    if current_user.id != user_id and not current_user.role == "admin":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="접근 권한이 없습니다.")
    db_interest = db.query(user.UserInterest).filter(
        user.UserInterest.id == interest_id,
        user.UserInterest.user_id == user_id
    ).first()
    if not db_interest:
        raise HTTPException(status_code=404, detail="해당 관심분야를 찾을 수 없습니다.")
    db_interest.interest_category = interest_in.interest_category
    db_interest.interest_name = interest_in.interest_name
    db.commit()
    db.refresh(db_interest)
    return UserInterestResponse.model_validate(db_interest, from_attributes=True)

# 소셜 링크 관련 엔드포인트
@router.post("/{user_id}/social-links", response_model=UserSocialLinkResponse)
def create_user_social_link(
    user_id: int, link_in: UserSocialLinkCreate, 
    db: Session = Depends(get_db), current_user: User = Depends(get_current_user)
):
    """사용자 소셜 링크 생성"""
    if current_user.id != user_id and not current_user.role == "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="접근 권한이 없습니다."
        )
    
    db_link = user.create_social_link(db=db, user_id=user_id, link_in=link_in)
    return UserSocialLinkResponse.model_validate(db_link, from_attributes=True)

@router.delete("/{user_id}/social-links/{link_id}", response_model=Dict)
def delete_user_social_link(
    user_id: int, link_id: int, 
    db: Session = Depends(get_db), current_user: User = Depends(get_current_user)
):
    """사용자 소셜 링크 삭제"""
    if current_user.id != user_id and not current_user.role == "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="접근 권한이 없습니다."
        )
    
    return user.delete_social_link(db=db, user_id=user_id, link_id=link_id)

@router.put("/{user_id}/social-links/{link_id}", response_model=UserSocialLinkResponse)
def update_user_social_link(
    user_id: int, link_id: int, link_in: UserSocialLinkCreate,
    db: Session = Depends(get_db), current_user: User = Depends(get_current_user)
):
    if current_user.id != user_id and not current_user.role == "admin":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="접근 권한이 없습니다.")
    db_link = db.query(user.UserSocialLink).filter(
        user.UserSocialLink.id == link_id,
        user.UserSocialLink.user_id == user_id
    ).first()
    if not db_link:
        raise HTTPException(status_code=404, detail="해당 소셜 링크를 찾을 수 없습니다.")
    db_link.platform = link_in.platform
    db_link.url = link_in.url
    db.commit()
    db.refresh(db_link)
    return UserSocialLinkResponse.model_validate(db_link, from_attributes=True)

# 알림 관련 엔드포인트
@router.get("/{user_id}/notifications", response_model=List[NotificationResponse])
def get_user_notifications(
    user_id: int, 
    skip: int = 0, 
    limit: int = 50,
    db: Session = Depends(get_db), 
    current_user: User = Depends(get_current_user)
):
    """사용자의 알림 목록 조회"""
    if current_user.id != user_id and not current_user.role == "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="접근 권한이 없습니다."
        )
    
    notifications = user.get_notifications(db=db, user_id=user_id, skip=skip, limit=limit)
    return [NotificationResponse.model_validate(n, from_attributes=True) for n in notifications]

@router.get("/{user_id}/notifications/unread-count")
def get_user_unread_notification_count(
    user_id: int,
    db: Session = Depends(get_db), 
    current_user: User = Depends(get_current_user)
):
    """사용자의 읽지 않은 알림 개수 조회"""
    if current_user.id != user_id and not current_user.role == "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="접근 권한이 없습니다."
        )
    
    count = user.get_unread_notification_count(db=db, user_id=user_id)
    return {"unread_count": count} 