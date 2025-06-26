from fastapi import APIRouter, Depends, HTTPException
from database import SessionLocal
from auth import create_access_token, verify_password, get_current_user
from schemas.login import LoginForm, SocialNewMember, Token
from schemas.member import Member
from crud.member import get_member_by_email
from crud.auth import get_github_user_info, get_github_access_token
from models.member import Member as MemberModel
import logging

router = APIRouter(
    tags=["auth"]
)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.post('/login', response_model=Token)
def login(login: LoginForm, db: SessionLocal = Depends(get_db)):  # type: ignore
    member = get_member_by_email(db, login.userEmail)
    if not member:
        raise HTTPException(
            status_code=401,
            detail="이메일이나 비밀번호가 올바르지 않습니다"
        )
    
    if not verify_password(login.password, member.password):
        raise HTTPException(
            status_code=401,
            detail="이메일이나 비밀번호가 올바르지 않습니다"
        )

    # Convert SQLAlchemy model to dict for JWT token
    member_data = {
        "id": member.id,
        "name": member.name,
        "email": member.email,
        "role": member.role,
        "status": member.status,
        "lastLogin": member.lastLogin,
        "createdAt": member.createdAt,
        "skills": member.skills,
        "projects": member.projects,
        "profileImage": member.profileImage,
        "contactNumber": member.contactNumber,
        "birthDate": member.birthDate,
        "introduction": member.introduction,
        "workingHours": member.workingHours,
        "languages": member.languages,
        "socialLinks": member.socialLinks,
        "notification": member.notification,
        "isGithub": member.isGithub,
        "github_id": member.github_id,
        "isGoogle": member.isGoogle,
        "google_id": member.google_id,
        "isApple": member.isApple,
        "apple_id": member.apple_id,
        "signupMethod": member.signupMethod
    }
    
    access_token = create_access_token(
      data={
        "sub": member.email,
        "user_info": member_data
      }
    )
    
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user_id": member.id,
        "user_name": member.name,
        "user_email": member.email
    }
    
@router.get("/me", response_model=Member)
def get_me(current_user: dict = Depends(get_current_user), db: SessionLocal = Depends(get_db)):  # type: ignore
    # Fetch fresh user data from the database using the email from token
    member = get_member_by_email(db, current_user['email'])
    logging.info(f"User data: {member}")
    if not member:
        raise HTTPException(
            status_code=404,
            detail="User not found"
        )
    return member 


@router.get("/auth/callback")
async def auth_callback(social: str, code: str, db: SessionLocal = Depends(get_db)):
    if not code:
        raise HTTPException(status_code=400, detail="Authorization code is required")
        
    try:
        if social == "github":
            social_access_token, user, github_username = await get_github_user_info(code)
            logging.info(f"Social access token received for GitHub user: {github_username}")
        else:
            raise HTTPException(status_code=400, detail=f"Unsupported social provider: {social}")
            
        if not user or not user.get("email"):
            raise HTTPException(
                status_code=400,
                detail="Could not retrieve user email from GitHub. Please ensure your GitHub account has a verified email address and that you've granted email access permissions."
            )
            
        existing = db.query(MemberModel).filter(MemberModel.email == user.get("email")).first()
        
        if existing:
            # Update the existing user's GitHub access token and last login
            existing.github_access_token = social_access_token
            existing.github_id = github_username
            existing.isGithub = True
            db.commit()
            db.refresh(existing)
            
            # Create a serializable dictionary of user info
            user_info = {
                "id": existing.id,
                "name": existing.name,
                "email": existing.email,
                "role": existing.role,
                "status": existing.status,
                "lastLogin": existing.lastLogin,
                "createdAt": existing.createdAt,
                "skills": existing.skills,
                "projects": existing.projects,
                "profileImage": existing.profileImage,
                "contactNumber": existing.contactNumber,
                "birthDate": existing.birthDate,
                "introduction": existing.introduction,
                "workingHours": existing.workingHours,
                "languages": existing.languages,
                "socialLinks": existing.socialLinks,
                "notification": existing.notification,
                "isGithub": existing.isGithub,
                "github_id": existing.github_id,
                "github_access_token": existing.github_access_token,
                "isGoogle": existing.isGoogle,
                "google_id": existing.google_id,
                "google_access_token": existing.google_access_token,
                "isApple": existing.isApple,
                "apple_id": existing.apple_id,
                "apple_access_token": existing.apple_access_token,
                "signupMethod": existing.signupMethod
            }
            
            # Create token with serialized user info
            access_token = create_access_token(
                data={
                    "sub": user.get("email"),
                    "user_info": user_info
                }
            )
            return {
                "status": "logged_in",
                "access_token": access_token,
                "user_info": user_info
            }
        else:
            return {
                "status": "need_additional_info",
                "user_info": {
                    "name": user.get("name"),
                    "email": user.get("email"),
                    "profileImage": user.get("avatar_url"),
                    "socialLinks": [{"name": "github", "url": user.get("html_url")}],
                    "introduction": user.get("bio"),
                    "social_id": user.get("login") if social == "github" else None,
                    "social_access_token": social_access_token
                }
            }
    except HTTPException as he:
        logging.error(f"HTTP Exception in auth_callback: {str(he)}")
        raise
    except Exception as e:
        import traceback
        error_detail = f"An error occurred during authentication: {str(e)}\n{traceback.format_exc()}"
        logging.error(error_detail)
        raise HTTPException(
            status_code=500,
            detail="An error occurred during authentication. Please try again later."
        )
    
@router.post("/auth/signup")
def register_with_social(payload: SocialNewMember, db: SessionLocal = Depends(get_db)):
  # 중복 방지
  if db.query(MemberModel).filter(MemberModel.email == payload.email).first():
      raise HTTPException(status_code=400, detail="이미 가입된 이메일입니다.")
  try:
    # Convert Pydantic models to dictionaries for JSON serialization
    working_hours_dict = payload.workingHours.model_dump() if payload.workingHours else None
    social_links_list = [link.model_dump() for link in payload.socialLinks] if payload.socialLinks else []
    
    new_user = MemberModel(
      name=payload.name,
      email=payload.email,
      password=payload.password,
      role=payload.role,
      status=payload.status,
      contactNumber=payload.contactNumber,
      birthDate=payload.birthDate,
      introduction=payload.introduction,
      workingHours=working_hours_dict,
      languages=payload.languages,
      skills=payload.skills,
      socialLinks=social_links_list,
      profileImage=payload.profileImage,
      lastLogin=payload.lastLogin,
      createdAt=payload.createdAt,
      isGithub=payload.isGithub,
      github_id=payload.github_id,
      github_access_token=payload.github_access_token,
      isGoogle=payload.isGoogle,
      google_id=payload.google_id,
      google_access_token=payload.google_access_token,
      isApple=payload.isApple,
      apple_id=payload.apple_id,
      apple_access_token=payload.apple_access_token,
      signupMethod=payload.signupMethod
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    # Create a serializable dictionary of user info
    user_info = {
        "id": new_user.id,
        "name": new_user.name,
        "email": new_user.email,
        "role": new_user.role,
        "status": new_user.status,
        "profileImage": new_user.profileImage,
        "isGithub": new_user.isGithub,
        "github_id": new_user.github_id,
        "isGoogle": new_user.isGoogle,
        "google_id": new_user.google_id,
        "isApple": new_user.isApple,
        "apple_id": new_user.apple_id,
        "signupMethod": new_user.signupMethod
    }
    
    token = create_access_token(
      data={
        "sub": new_user.email,
        "user_info": user_info
      }
    )
    member = db.query(MemberModel).filter(MemberModel.email == payload.email).first()
    return {"status": "registered", "access_token": token, "user_info": member.__dict__}
  except Exception as e:
    import traceback
    traceback.print_exc()
    raise HTTPException(status_code=500, detail=str(e))