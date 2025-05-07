from fastapi import APIRouter, Depends, HTTPException
from database import SessionLocal
from auth import create_access_token, verify_password, get_current_user
import schemas.login
from schemas.login import LoginForm
from schemas.member import Member
from crud.member import get_member_by_email

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
def login(login: LoginForm, db: SessionLocal = Depends(get_db)):
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
def get_me(current_user: dict = Depends(get_current_user), db: SessionLocal = Depends(get_db)):
    # Fetch fresh user data from the database using the email from token
    member = get_member_by_email(db, current_user['email'])
    if not member:
        raise HTTPException(
            status_code=404,
            detail="User not found"
        )
    return member 