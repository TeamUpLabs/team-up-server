from fastapi import APIRouter, Depends, HTTPException
from database import SessionLocal
from auth import create_access_token, verify_password, get_current_user
import schemas.login
from schemas.login import LoginForm
from schemas.member import Member
from crud.member import get_member_by_email
from fastapi.responses import RedirectResponse
import httpx, os
from dotenv import load_dotenv
from jose import jwt
from datetime import datetime, timezone
from models.member import Member as MemberModel

router = APIRouter(
    tags=["auth"]
)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.post('/login', response_model=schemas.login.Token)
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
  
  
load_dotenv()

CLIENT_ID = os.getenv("GITHUB_CLIENT_ID")
CLIENT_SECRET = os.getenv("GITHUB_CLIENT_SECRET")
JWT_SECRET = os.getenv("JWT_SECRET", "secret")

@router.get("/auth/github/callback")
async def github_callback(code: str, db: SessionLocal = Depends(get_db)):
    # 1. GitHub에 Access Token 요청
    async with httpx.AsyncClient() as client:
        token_res = await client.post(
            "https://github.com/login/oauth/access_token",
            headers={"Accept": "application/json"},
            data={
                "client_id": CLIENT_ID,
                "client_secret": CLIENT_SECRET,
                "code": code
            }
        )
        token_data = token_res.json()
        access_token = token_data["access_token"]

        user_res = await client.get(
            "https://api.github.com/user",
            headers={"Authorization": f"Bearer {access_token}"}
        )
        user = user_res.json()

        if not user.get("email"):
            emails_res = await client.get(
                "https://api.github.com/user/emails",
                headers={"Authorization": f"Bearer {access_token}"}
            )
            emails = emails_res.json()
            if emails:
                primary_email = next((email["email"] for email in emails if email["primary"]), None)
                if not primary_email:
                    primary_email = emails[0]["email"] # Fallback to the first email
                user["email"] = primary_email
        
        
    existing = db.query(MemberModel).filter(MemberModel.email == user.get("email")).first()
    if not existing:
        new_member = MemberModel(
            name=user.get("name"),
            email=user.get("email"),
            password="1234",
            role="개발자",
            status="활성",
            lastLogin=datetime.now(timezone.utc).isoformat().split(".")[0],
            createdAt=datetime.now(timezone.utc).isoformat().split("T")[0],
            skills=[],
            projects=[],
            profileImage=user.get("avatar_url"),
            contactNumber="",
            birthDate="",
            introduction=user.get("bio"),
            workingHours={
                "start": "09:00",  # Default start time
                "end": "18:00",    # Default end time
                "timezone": "Asia/Seoul"  # Default timezone
            },
            languages=[],
            socialLinks=[{"name": "github", "url": user.get("html_url")}],
            participationRequest=[]
        )
        db.add(new_member)
        db.commit()
        db.refresh(new_member)
        existing_member = new_member
    else:
      existing_member = db.query(MemberModel).filter(MemberModel.email == user.get("email")).first()
    member_data = {
      "id": existing_member.id,
      "name": existing_member.name,
      "email": existing_member.email,
      "role": existing_member.role,
      "status": existing_member.status,
      "lastLogin": existing_member.lastLogin,
      "createdAt": existing_member.createdAt,
      "skills": existing_member.skills,
      "projects": existing_member.projects,
      "profileImage": existing_member.profileImage,
      "contactNumber": existing_member.contactNumber,
      "birthDate": existing_member.birthDate,
      "introduction": existing_member.introduction,
      "workingHours": existing_member.workingHours,
      "languages": existing_member.languages,
      "socialLinks": existing_member.socialLinks,
      "notification": existing_member.notification
  }
    
    access_token = create_access_token(
        data={
            "sub": member_data["email"],
            "user_info": member_data
        }
    )

    # 4. 프론트로 리디렉션
    response = RedirectResponse(url=f"http://localhost:3000/auth/callback?token={access_token}")
    return response