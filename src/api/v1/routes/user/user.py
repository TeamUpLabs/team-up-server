from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from core.database.database import get_db
from api.v1.schemas.user.user_schema import UserCreate, UserDetail, UserUpdate
from api.v1.services.user.user_service import UserService

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