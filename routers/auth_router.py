from fastapi import APIRouter, Depends, HTTPException, status, Request
from schemas.auth import LoginRequest, OauthRequest, LogoutRequest
from sqlalchemy.orm import Session
import logging
from pydantic import BaseModel
from fastapi.responses import RedirectResponse
from crud.user import user
from schemas.user import UserCreate, UserDetail, Token, UserBrief
from utils.auth import create_access_token, get_current_user, verify_token
from database import get_db
import os
from crud.auth import get_github_user_info, get_google_user_info
from datetime import datetime
from crud.session import session as session_crud
from models.user import UserSession
from ua_parser import user_agent_parser

class TokenVerifyRequest(BaseModel):
    token: str

router = APIRouter(
    prefix="/api/auth",
    tags=["auth"]
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
async def login(form_data: LoginRequest, request: Request, db: Session = Depends(get_db)):
    """
    사용자 로그인
    """
    try:
        # 사용자 인증
        authenticated_user = user.authenticate(
            db, email=form_data.email, password=form_data.password
        )
        
        if not authenticated_user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="이메일이나 비밀번호가 올바르지 않습니다.",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        # Update user status and last login if needed
        if authenticated_user.status == "inactive":
            authenticated_user.status = "active"
        authenticated_user.last_login = datetime.now()
        db.commit()
        db.refresh(authenticated_user)
        
        existing_session = db.query(UserSession).filter(UserSession.session_id == form_data.session_id, UserSession.user_id == authenticated_user.id).first()
        if existing_session:
            session_crud.update_current_session(db, user_id=authenticated_user.id, session_id=form_data.session_id)
        else:
          try:
            ua_string = request.headers.get("user-agent", "")
            ua = user_agent_parser.Parse(ua_string)
            
            # 디바이스 유형 구분
            if ua["device"]["family"] == "Mobile":
                device_type = "Mobile"
            elif ua["device"]["family"] == "Tablet":
                device_type = "Tablet"
            else:
                device_type = "Desktop"
            
            db_session = UserSession(
                session_id=form_data.session_id,
                user_id=authenticated_user.id,
                device_id=form_data.device_id,
                user_agent=ua_string,
                ip_address=request.client.host or "",
                device=ua["device"]["family"],
                device_type=device_type,
                os=ua["os"]["family"],
                browser=ua["user_agent"]["family"],
                last_active_at=datetime.now(),
                is_current=True
            )
            db.add(db_session)
            db.commit()
            db.refresh(db_session)
          except Exception as e:
              db.rollback()
              logging.error(f"Error creating login session: {str(e)}")
        
        # Create access token with user info
        access_token = create_access_token(
            data={
                "sub": authenticated_user.email,
                "user_info": {
                    "id": authenticated_user.id,
                    "email": authenticated_user.email,
                    "role": authenticated_user.role,
                    "status": authenticated_user.status
                }
            }
        )
        
        # Create user brief info
        user_brief = UserBrief(
            id=authenticated_user.id,
            name=authenticated_user.name,
            email=authenticated_user.email,
            profile_image=authenticated_user.profile_image,
            role=authenticated_user.role,
            status=authenticated_user.status,
            created_at=authenticated_user.created_at,
            updated_at=authenticated_user.updated_at
        )
        
        return {
            "access_token": access_token,
            "token_type": "bearer",
            "user_info": user_brief
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
def login_for_access_token(form_data: LoginRequest, db: Session = Depends(get_db)):
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

@router.post("/{user_id}/logout")
def logout(user_id: int, form_data: LogoutRequest, db: Session = Depends(get_db)):
    """
    로그아웃 (클라이언트에서 토큰을 삭제하도록 안내)
    """
    user.logout(db, user_id=user_id, session_id=form_data.session_id)
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
    if provider == "google":
        return RedirectResponse(f"https://accounts.google.com/o/oauth2/v2/auth?client_id={os.getenv('GOOGLE_CLIENT_ID')}&redirect_uri={os.getenv('GOOGLE_REDIRECT_URI')}&response_type=code&scope=openid%20email%20profile")
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail=f"{provider} 소셜 로그인은 아직 구현되지 않았습니다."
    )

@router.post("/social/callback")
async def social_callback(form_data: OauthRequest, request: Request, db: Session = Depends(get_db)):
    """
    소셜 로그인 콜백 처리
    """
    if not form_data.code:
        raise HTTPException(status_code=400, detail="Authorization code is required")
      
    try:
        if form_data.provider == "github":
            social_access_token, github_user, github_username = await get_github_user_info(form_data.code)
            # Process GitHub login...
        elif form_data.provider == "google":
            social_access_token, google_user = await get_google_user_info(form_data.code)
            # Process Google login...
        else:
            raise HTTPException(status_code=400, detail=f"Unsupported social provider: {form_data.provider}")

        if form_data.provider == "github" and (not github_user or not github_user.get("email")):
            raise HTTPException(
                status_code=400,
                detail="Could not retrieve user email from GitHub. Please ensure your GitHub account has a verified email address and that you've granted email access permissions."
            )
        if form_data.provider == "google" and (not google_user or not google_user.get("email")):
            raise HTTPException(
                status_code=400,
                detail="Could not retrieve user email from Google. Please ensure your Google account has a verified email address and that you've granted email access permissions."
            )
        if form_data.provider == "github":
            existing = user.get_by_email(db, email=github_user.get("email"))
        elif form_data.provider == "google":
            existing = user.get_by_email(db, email=google_user.get("email"))
        
        if existing:
            # Update the existing user's GitHub access token and last login
            existing.last_login = datetime.now()
            existing.status = "active"
            existing.auth_provider_access_token = social_access_token # 소셜 로그인 토큰
            db.commit()
            db.refresh(existing)
            
            # Update user last login
            existing.last_login = datetime.now()
            db.commit()
            db.refresh(existing)
            
            existing_session = db.query(UserSession).filter(UserSession.session_id == form_data.session_id, UserSession.user_id == existing.id).first()
            if existing_session:
                session_crud.update_current_session(db, user_id=existing.id, session_id=form_data.session_id)
                logging.info(f"Successfully updated session: {existing_session.id}")
            else:
                try:
                  ua_string = request.headers.get("user-agent", "")
                  ua = user_agent_parser.Parse(ua_string)
                  
                  # 디바이스 유형 구분
                  if ua["device"]["family"] == "Mobile":
                      device_type = "Mobile"
                  elif ua["device"]["family"] == "Tablet":
                      device_type = "Tablet"
                  else:
                      device_type = "Desktop"
                      
                  db_session = UserSession(
                      session_id=form_data.session_id,
                      user_id=existing.id,
                      device_id=form_data.device_id,
                      user_agent=ua_string,
                      ip_address=request.client.host or "",
                      device=ua["device"]["family"],
                      device_type=device_type,
                      os=ua["os"]["family"],
                      browser=ua["user_agent"]["family"],
                      last_active_at=datetime.now(),
                      is_current=True
                  )
                  db.add(db_session)
                  db.commit()
                  db.refresh(db_session)
                except Exception as e:
                    db.rollback()
                    logging.error(f"Error creating session: {str(e)}")
            
            # Create access token with user info
            access_token = create_access_token(
                data={
                    "sub": existing.email,
                    "user_info": {
                        "id": existing.id,
                        "email": existing.email,
                        "role": existing.role,
                        "status": existing.status
                    }
                }
            )
            
            # Create user brief info
            user_brief = UserBrief(
                id=existing.id,
                name=existing.name,
                email=existing.email,
                profile_image=existing.profile_image,
                role=existing.role,
                status=existing.status,
                created_at=existing.created_at,
                updated_at=existing.updated_at
            )
            
            return {
                "status": "logged_in",
                "access_token": access_token,
                "token_type": "bearer",
                "user_info": user_brief
            }
        else:
            # Create new user
            if form_data.provider == "github":
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
            elif form_data.provider == "google":
              return {
                  "status": "need_additional_info",
                  "user_info": {
                      "name": google_user.get("name"),
                      "email": google_user.get("email"),
                      "profile_image": google_user.get("picture"),
                      "social_links": [{"platform": "google", "url": "https://www.google.com"}],
                      "bio": "안녕하세요.",
                      "auth_provider": "google",
                      "auth_provider_id": google_user.get("sub"),
                      "auth_provider_access_token": social_access_token
                  }
              }
              
    except Exception as e:
        logging.error(f"Social login callback error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="소셜 로그인 콜백 처리 중 오류가 발생했습니다."
        )