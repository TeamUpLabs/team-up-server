from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from src.core.database.database import get_db
from src.core.security.auth import get_current_user
from src.api.v1.services.community.community_service import CommunityService

router = APIRouter(prefix="/api/v1/community", tags=["community"])

@router.get("/")
def get_community(
  db: Session = Depends(get_db),
  current_user: dict = Depends(get_current_user)
):
  try:
    if not current_user:
      raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Unauthorized")
    community_service = CommunityService(db)
    return community_service.get_info(current_user.id)
  except HTTPException as e:
    raise e
  except Exception as e:
    raise HTTPException(status_code=400, detail=str(e))
  
@router.get("/tags")
def get_all_post_tags(
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
    limit: int = None
):
  try:
    if not current_user:
      raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Unauthorized")
    community_service = CommunityService(db)
    return community_service.get_all_tags(limit=limit)
  except HTTPException as e:
    raise e
  except Exception as e:
    raise HTTPException(status_code=400, detail=str(e))