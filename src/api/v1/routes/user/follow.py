from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from api.v1.services.user.follow_service import FollowService
from api.v1.schemas.user.follow_schema import FollowCreate, FollowList
from core.security.auth import get_current_user
from core.database.database import get_db

router = APIRouter(prefix="/api/v1/users/{user_id}/follow", tags=["follow"])

@router.post("/")
def create_follow(
  user_id: int,
  follow_create: FollowCreate,
  db: Session = Depends(get_db),
  current_user: dict = Depends(get_current_user)
):
  if not current_user or current_user.id != user_id:
    raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Unauthorized")
  
  try: 
    follow_service = FollowService(db)
    return follow_service.create(follow_create)
  except Exception as e:
    raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))
  
@router.delete("/")
def delete_follow(
  user_id: int,
  follow_create: FollowCreate,
  db: Session = Depends(get_db),
  current_user: dict = Depends(get_current_user)
):
  if not current_user or current_user.id != user_id:
    raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Unauthorized")
  
  try: 
    follow_service = FollowService(db)
    return follow_service.delete(follow_create)
  except Exception as e:
    raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

@router.get("/followers", response_model=FollowList)
def get_followers(
  user_id: int,
  db: Session = Depends(get_db),
  current_user: dict = Depends(get_current_user)
):
  if not current_user or current_user.id != user_id:
    raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Unauthorized")
  
  try: 
    follow_service = FollowService(db)
    return follow_service.get_followers(user_id)
  except Exception as e:
    raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

@router.get("/followed", response_model=FollowList)
def get_followed(
  user_id: int,
  db: Session = Depends(get_db),
  current_user: dict = Depends(get_current_user)
):
  if not current_user or current_user.id != user_id:
    raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Unauthorized")
  
  try: 
    follow_service = FollowService(db)
    return follow_service.get_followed(user_id)
  except Exception as e:
    raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


