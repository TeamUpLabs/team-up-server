from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from typing import Optional
import logging
from pydantic import BaseModel
from fastapi.responses import RedirectResponse
from new_crud.user import user
from new_schemas.user import UserCreate, UserDetail, Token, UserBrief, UserUpdate
from auth import create_access_token, get_current_user, verify_token
from database import get_db
import os
from crud.auth import get_github_user_info
from datetime import datetime

class TokenVerifyRequest(BaseModel):
    token: str

router = APIRouter(
    prefix="/api/auth",
    tags=["authentication"]
)

@router.post("/register", response_model=UserDetail)
def register(user_in: UserCreate, db: Session = Depends(get_db)):
    """
    새 사용자 회원가입
    """
    try:
        return user.create(db, obj_in=user_in)
    except HTTPException as e:
        raise e
    except Exception as e:
        logging.error(f"Registration error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="회원가입 중 오류가 발생했습니다."
        )

@router.post("/login", response_model=Token)
def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    """
    사용자 로그인
    """
    try:
        # 사용자 인증
        authenticated_user = user.authenticate(
            db, email=form_data.username, password=form_data.password
        )
        
        if not authenticated_user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="이메일이나 비밀번호가 올바르지 않습니다.",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        # 액세스 토큰 생성
        access_token = create_access_token(
            data={"sub": authenticated_user.email}
        )
        
        # UserBrief 객체 생성
        user_brief = UserBrief(
            id=authenticated_user.id,
            name=authenticated_user.name,
            profile_image=authenticated_user.profile_image,
            role=authenticated_user.role,
            status=authenticated_user.status
        )
        
        return {
            "access_token": access_token,
            "token_type": "bearer",
            "user": user_brief
        }
        
    except HTTPException as e:
        raise e
    except Exception as e:
        logging.error(f"Login error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="로그인 중 오류가 발생했습니다."
        )

@router.post("/token", response_model=Token)
def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    """
    OAuth2 호환 토큰 엔드포인트
    """
    return login(form_data, db)

@router.get("/me", response_model=UserDetail)
def get_current_user_info(current_user: dict = Depends(get_current_user), db: Session = Depends(get_db)):
    """
    현재 로그인한 사용자 정보 조회
    """
    try:
        return current_user
    except Exception as e:
        logging.error(f"Get current user error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="사용자 정보 조회 중 오류가 발생했습니다."
        )

@router.post("/verify-token")
def verify_access_token(token_request: TokenVerifyRequest):
    """
    토큰 유효성 검증
    """
    try:
        payload = verify_token(token_request.token)
        if payload is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="유효하지 않은 토큰입니다."
            )
        return {"valid": True, "payload": payload}
    except HTTPException as e:
        raise e
    except Exception as e:
        logging.error(f"Token verification error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="토큰 검증 중 오류가 발생했습니다."
        )

@router.post("/refresh-token")
def refresh_access_token(current_user: dict = Depends(get_current_user)):
    """
    액세스 토큰 갱신
    """
    try:
        # 새로운 액세스 토큰 생성
        new_access_token = create_access_token(
            data={"sub": current_user.email}
        )
        
        # UserBrief 객체 생성
        user_brief = UserBrief(
            id=current_user.id,
            name=current_user.name,
            profile_image=current_user.profile_image,
            role=current_user.role,
            status=current_user.status
        )
        
        return {
            "access_token": new_access_token,
            "token_type": "bearer",
            "user": user_brief
        }
        
    except Exception as e:
        logging.error(f"Token refresh error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="토큰 갱신 중 오류가 발생했습니다."
        )

@router.post("/logout")
def logout():
    """
    로그아웃 (클라이언트에서 토큰을 삭제하도록 안내)
    """
    return {"message": "로그아웃되었습니다. 클라이언트에서 토큰을 삭제해주세요."}

# 소셜 로그인 관련 엔드포인트 (향후 확장 가능)
@router.get("/social/{provider}/login")
def social_login(provider: str):
    """
    소셜 로그인 URL 생성
    """
    # GitHub, Google, Apple 등 소셜 로그인 구현 예정
    if provider == "github":
        return RedirectResponse(f"https://github.com/login/oauth/authorize?client_id={os.getenv('GITHUB_CLIENT_ID')}&scope=user:email,repo,admin:org")
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail=f"{provider} 소셜 로그인은 아직 구현되지 않았습니다."
    )

@router.get("/social/{provider}/callback")
async def social_callback(provider: str, code: str, db: Session = Depends(get_db)):
    """
    소셜 로그인 콜백 처리
    """
    if not code:
        raise HTTPException(status_code=400, detail="Authorization code is required")
    
    try:
        if provider == "github":
            social_access_token, github_user, github_username = await get_github_user_info(code)
            logging.info(f"Social access token received for GitHub user: {github_username}")
        else:
            raise HTTPException(status_code=400, detail=f"Unsupported social provider: {provider}")
            
        if not github_user or not github_user.get("email"):
            raise HTTPException(
                status_code=400,
                detail="Could not retrieve user email from GitHub. Please ensure your GitHub account has a verified email address and that you've granted email access permissions."
            ) 
            
        existing = user.get_by_email(db, email=github_user.get("email"))
        
        if existing:
            # Update the existing user's GitHub access token and last login
            existing.last_login = datetime.now()
            existing.status = "active"
            existing.auth_provider = "github" # 소셜 로그인 플랫폼
            existing.auth_provider_id = github_username # 소셜 로그인 아이디
            existing.auth_provider_access_token = social_access_token # 소셜 로그인 토큰
            db.commit()
            db.refresh(existing)
            
            # 액세스 토큰 생성
            access_token = create_access_token(
                data={
                    "sub": existing.email,
                    "user_info": existing
                }
            )
            
            # UserBrief 객체 생성
            user_brief = UserBrief(
                id=existing.id,
                name=existing.name,
                profile_image=existing.profile_image,
                role=existing.role,
                status=existing.status
            )
            
            return {
                "status": "logged_in",
                "access_token": access_token,
                "user_info": user_brief
            }
        else:
            # Create new user
            return {
                "status": "need_additional_info",
                "user_info": {
                    "name": github_user.get("name"),
                    "email": github_user.get("email"),
                    "profile_image": github_user.get("avatar_url"),
                    "social_links": [{"platform": "github", "url": github_user.get("html_url")}],
                    "bio": github_user.get("bio"),
                    "auth_provider": "github",
                    "auth_provider_id": github_user.get("login"),
                    "auth_provider_access_token": social_access_token
                }
            }
            
    except Exception as e:
        logging.error(f"Social login callback error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="소셜 로그인 콜백 처리 중 오류가 발생했습니다."
        )