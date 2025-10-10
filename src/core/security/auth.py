from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from src.core.database.database import get_db
from src.core.security.password import verify_password
from src.core.security.jwt import create_access_token, verify_token
from src.api.v1.models.user import User

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")

def authenticate_user(db: Session, email: str, password: str) -> User:
  """이메일과 비밀번호로 사용자 인증"""
  user = db.query(User).filter(User.email == email).first()
  if not user or not verify_password(password, user.hashed_password):
    return None
  return user


def login(db: Session, email: str, password: str):
  """로그인 후 JWT 토큰 발급"""
  user = authenticate_user(db, email, password)
  if not user:
    raise HTTPException(
      status_code=status.HTTP_401_UNAUTHORIZED,
      detail="이메일 또는 비밀번호가 올바르지 않습니다.",
      headers={"WWW-Authenticate": "Bearer"},
    )
  access_token = create_access_token({"sub": user.email})
  return {"access_token": access_token, "token_type": "bearer"}


def get_current_user(
  db: Session = Depends(get_db), token: str = Depends(oauth2_scheme)
) -> User:
  """현재 로그인된 사용자 반환"""
  try:
    payload = verify_token(token)
    user_email = payload.get("sub")
  except Exception:
    raise HTTPException(status_code=401, detail="Invalid authentication token")

  user = db.query(User).filter(User.email == user_email).first()
  if user is None:
    raise HTTPException(status_code=401, detail="User not found")

  return user