from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from core.database.database import get_db
from api.v1.schemas.user.user_schema import UserCreate, UserDetail, UserUpdate
from api.v1.services.user.user_service import UserService
from core.security.auth import get_current_user
from typing import List

router = APIRouter(prefix="/api/v1/users", tags=["users"])

@router.post("/", response_model=UserDetail)
async def create_user(
  user: UserCreate,
  db: Session = Depends(get_db)
):
  try:
    service = UserService(db)
    return service.create_user(user)
  except HTTPException as e:
    raise e
  except Exception as e:
    raise HTTPException(status_code=400, detail=str(e))

@router.get("/me", response_model=UserDetail)
async def get_current_user(
  db: Session = Depends(get_db),
  current_user: dict = Depends(get_current_user)
):
  if not current_user:
    raise HTTPException(
      status_code=status.HTTP_403_FORBIDDEN,
      detail="Not authorized to perform this action"
    )
    
  try:
    service = UserService(db)
    return service.get_user(current_user.id)
  except HTTPException as e:
    raise e
  except Exception as e:
    raise HTTPException(status_code=404, detail=str(e))
  
@router.put("/me", response_model=UserDetail)
async def update_current_user(
  user: UserUpdate,
  db: Session = Depends(get_db),
  current_user: dict = Depends(get_current_user)
):
  if not current_user:
    raise HTTPException(
      status_code=status.HTTP_403_FORBIDDEN,
      detail="Not authorized to perform this action"
    )
    
  try:
    service = UserService(db)
    return service.update_user(current_user.id, user)
  except HTTPException as e:
    raise e
  except Exception as e:
    raise HTTPException(status_code=400, detail=str(e))

@router.get("/{user_id}", response_model=UserDetail)
async def get_user(
    user_id: int,
    db: Session = Depends(get_db)
):
  try:
    service = UserService(db)
    return service.get_user(user_id)
  except HTTPException as e:
    raise e
  except Exception as e:
    raise HTTPException(status_code=404, detail=str(e))

@router.put("/{user_id}", response_model=UserDetail)
async def update_user(
  user_id: int,
  user: UserUpdate,
  db: Session = Depends(get_db)
):
  try:
    service = UserService(db)
    return service.update_user(user_id, user)
  except HTTPException as e:
    raise e
  except Exception as e:
    raise HTTPException(status_code=400, detail=str(e))

@router.delete("/{user_id}")
async def delete_user(
  user_id: int,
  db: Session = Depends(get_db)
):
  try:
    service = UserService(db)
    return service.delete_user(user_id)
  except HTTPException as e:
    raise e
  except Exception as e:
    raise HTTPException(status_code=400, detail=str(e))
  
@router.get("/exclude/me", response_model=List[UserDetail])
async def get_users_exclude_me(
  db: Session = Depends(get_db),
  current_user: dict = Depends(get_current_user)
):
  try:
    if not current_user:
      raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail="Not authorized to perform this action"
      )
    
    service = UserService(db)
    return service.get_users_exclude_me(current_user.id)
  except HTTPException as e:
    raise e
  except Exception as e:
    raise HTTPException(status_code=400, detail=str(e))