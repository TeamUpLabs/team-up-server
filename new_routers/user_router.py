from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from typing import List
from sqlalchemy.orm import Session

from database import get_db
from auth import create_access_token, get_current_user
from new_crud import user
from new_schemas.user import UserCreate, UserUpdate, UserDetail, UserBrief, Token
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
        "user": UserBrief.model_validate(db_user, from_attributes=True)
    }

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

@router.get("/{user_id}/projects", response_model=List)
def read_user_projects(user_id: int, db: Session = Depends(get_db)):
    """특정 사용자의 프로젝트 목록 조회"""
    from new_schemas.project import ProjectBrief
    projects = user.get_projects(db=db, user_id=user_id)
    return [ProjectBrief.model_validate(p, from_attributes=True) for p in projects]

@router.get("/{user_id}/tasks", response_model=List)
def read_user_tasks(user_id: int, db: Session = Depends(get_db)):
    """특정 사용자의 업무 목록 조회"""
    from new_schemas.task import TaskBrief
    tasks = user.get_tasks(db=db, user_id=user_id)
    return [TaskBrief.model_validate(t, from_attributes=True) for t in tasks] 