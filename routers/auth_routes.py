from fastapi import APIRouter, Depends, HTTPException
from database import SessionLocal
from auth import create_access_token, verify_password, get_current_user
from schemas.login import LoginForm, SocialNewMember, Token
from schemas.member import Member
from crud.member import get_member_by_email
from crud.auth import get_github_user_info
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
        "notification": member.notification
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
    if not member:
        raise HTTPException(
            status_code=404,
            detail="User not found"
        )
    return member 


@router.get("/auth/callback")
async def auth_callback(social: str, code: str, db: SessionLocal = Depends(get_db)):
  if social == "github":
    user = await get_github_user_info(code)
    
  if not user.get("email"):
    raise HTTPException(status_code=400, detail="GitHub 이메일 접근 실패")
  
  existing = db.query(MemberModel).filter(MemberModel.email == user.get("email")).first()
  
  if existing:
    access_token = create_access_token(
      data={
        "sub": user.get("email"),
        "user_info": existing.__dict__
      }
    )
    return {
      "status": "logged_in", 
      "access_token": access_token, 
      "user_info": existing.__dict__
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
      }
    }
    
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
      isGoogle=payload.isGoogle,
      google_id=payload.google_id,
      isApple=payload.isApple,
      apple_id=payload.apple_id,
      signupMethod=payload.signupMethod
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    # Create a minimal user info dict for the token
    user_info = {
        "id": new_user.id,
        "email": new_user.email,
        "name": new_user.name,
        "role": new_user.role
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