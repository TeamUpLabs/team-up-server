from sqlalchemy.orm import Session
import os
from fastapi import HTTPException
from fastapi.responses import RedirectResponse
from core.security.oauth import get_github_user_info, get_google_user_info
from core.security.jwt import create_access_token
from fastapi import HTTPException, status
from datetime import datetime
from api.v1.schemas.user.oauth_schema import OauthRequest
from api.v1.services.user.user_service import UserService
from api.v1.services.user.session_service import SessionService
from api.v1.models.user.session import UserSession
from ua_parser import user_agent_parser
import logging
from api.v1.schemas.brief import UserBrief

class AuthRepository:
  def __init__(self, db: Session):
    self.db = db

  async def oauth_login(self, provider: str):
    """
    OAuth 로그인
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
    
  async def oauth_callback(self, form_data: OauthRequest):
    """
    OAuth 콜백 처리
    """
    try:
      logging.info(f"[OAUTH_CALLBACK] Starting OAuth callback for provider: {form_data.provider}")
      logging.info(f"[OAUTH_CALLBACK] Form data received: {form_data.dict()}")
      user_service = UserService(self.db)
      session_service = SessionService(self.db)
      if form_data.provider == "github":
        try:
          logging.info(f"[OAUTH_CALLBACK] Getting GitHub user info with code: {form_data.code}")
          social_access_token, github_user, github_username = await get_github_user_info(form_data.code)
          logging.info(f"[OAUTH_CALLBACK] GitHub user info received: {github_user}")
          logging.info(f"[OAUTH_CALLBACK] GitHub username: {github_username}")
          logging.info(f"[OAUTH_CALLBACK] GitHub access token: {'*' * 10}{social_access_token[-5:] if social_access_token else 'None'}")
        except Exception as e:
          raise HTTPException(status_code=500, detail=str(e))
      elif form_data.provider == "google":
        try:
          logging.info("[OAUTH_CALLBACK] Getting Google user info")
          social_access_token, google_user = await get_google_user_info(form_data.code)
          logging.info(f"[OAUTH_CALLBACK] Google user info received: {google_user}")
          logging.info(f"[OAUTH_CALLBACK] Google access token: {'*' * 10}{social_access_token[-5:] if social_access_token else 'None'}")
        except Exception as e:
          raise HTTPException(status_code=500, detail=str(e))
      else:
        raise HTTPException(status_code=400, detail=f"Unsupported social provider: {form_data.provider}")
      
      if form_data.provider == "github" and (not github_user or not github_user.get("email")):
        error_msg = "Could not retrieve user email from GitHub. Please ensure your GitHub account has a verified email address and that you've granted email access permissions."
        logging.error(f"[OAUTH_CALLBACK] {error_msg}")
        logging.error(f"[OAUTH_CALLBACK] GitHub user data: {github_user}")
        raise HTTPException(
          status_code=400,
          detail=error_msg
        )
      if form_data.provider == "google" and (not google_user or not google_user.get("email")):
        error_msg = "Could not retrieve user email from Google. Please ensure your Google account has a verified email address and that you've granted email access permissions."
        logging.error(f"[OAUTH_CALLBACK] {error_msg}")
        logging.error(f"[OAUTH_CALLBACK] Google user data: {google_user}")
        raise HTTPException(
          status_code=400,
          detail=error_msg
        )
      
      if form_data.provider == "github":
        try:
          email = github_user.get("email")
          logging.info(f"[OAUTH_CALLBACK] Looking for existing user with email: {email}")
          existing = user_service.get_user_by_email(email=email)
          logging.info(f"[OAUTH_CALLBACK] Existing user found: {existing.id if existing else 'None'}")
        except Exception as e:
          raise HTTPException(status_code=500, detail=str(e))
      elif form_data.provider == "google":
        try:
          email = google_user.get("email")
          logging.info(f"[OAUTH_CALLBACK] Looking for existing user with email: {email}")
          existing = user_service.get_user_by_email(email=email)
          logging.info(f"[OAUTH_CALLBACK] Existing user found: {existing.id if existing else 'None'}")
        except Exception as e:
          raise HTTPException(status_code=500, detail=str(e))
      if existing:
        try:
          existing.last_login = datetime.now()
          existing.status = "active"
          existing.auth_provider_access_token = social_access_token
          self.db.commit()
          self.db.refresh(existing)
          logging.info(f"Existing user updated: {existing}")
        except Exception as e:
          raise HTTPException(status_code=500, detail=str(e))
        
        existing_session = self.db.query(UserSession).filter(UserSession.session_id == form_data.session_id, UserSession.user_id == existing.id).first()
        if existing_session:
          try:
            session_service.update_current_session(user_id=existing.id, session_id=form_data.session_id)
            logging.info(f"Existing session updated: {existing_session}")
          except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))
        else:
          try:
            ua_string = form_data.user_agent
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
              ip_address=form_data.ip_address,
              device=ua["device"]["family"],
              device_type=device_type,
              os=ua["os"]["family"],
              browser=ua["user_agent"]["family"],
              last_active_at=datetime.now(),
              created_at=datetime.now(),
              updated_at=datetime.now()
            )
            self.db.add(db_session)
            self.db.commit()
            self.db.refresh(db_session)
            logging.info(f"New session created: {db_session}")
          except Exception as e:
            raise HTTPException(
              status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
              detail="Failed to create session"
            )
        
        try:
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
          logging.info(f"Access token created: {access_token}")
          
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
        except Exception as e:
          raise HTTPException(status_code=500, detail=str(e))    
      else:
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

    except HTTPException as he:
      logging.error(f"[OAUTH_CALLBACK] HTTPException occurred: {str(he)}", exc_info=True)
      raise he
    except Exception as e:
      logging.error(f"[OAUTH_CALLBACK] Unexpected error occurred: {str(e)}", exc_info=True)
      raise HTTPException(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        detail=f"소셜 로그인 중 오류가 발생했습니다: {str(e)}"
      )
        