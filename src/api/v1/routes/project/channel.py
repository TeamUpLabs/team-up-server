from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from core.database.database import get_db
from api.v1.services.project.channel_service import ChannelService
from api.v1.schemas.project.channel_schema import ChannelCreate, ChannelUpdate, ChannelDetail
from api.v1.schemas.brief import UserBrief
from core.security.auth import get_current_user
from typing import List

router = APIRouter(prefix="/api/v1/projects/{project_id}/channels", tags=["channels"])

@router.post("/", response_model=ChannelDetail)
def create_channel(
  project_id: str,
  channel: ChannelCreate,
  db: Session = Depends(get_db),
  current_user: dict = Depends(get_current_user)
):
  if not current_user:
    raise HTTPException(
      status_code=status.HTTP_403_FORBIDDEN,
      detail="Not authorized to perform this action"
    )
    
  try:
    service = ChannelService(db)
    return service.create(project_id, channel)
  except HTTPException as e:
    raise e
  except Exception as e:
    raise HTTPException(status_code=400, detail=str(e))
  
@router.get("/", response_model=List[ChannelDetail])
def get_channels(
  project_id: str,
  db: Session = Depends(get_db),
  current_user: dict = Depends(get_current_user)
):
  if not current_user:
    raise HTTPException(
      status_code=status.HTTP_403_FORBIDDEN,
      detail="Not authorized to perform this action"
    )
    
  try:
    service = ChannelService(db)
    return service.get_by_project_id(project_id)
  except HTTPException as e:
    raise e
  except Exception as e:
    raise HTTPException(status_code=400, detail=str(e))
  
@router.get("/public", response_model=List[ChannelDetail])
def get_public_channels_by_project(
  project_id: str,
  db: Session = Depends(get_db),
  current_user: dict = Depends(get_current_user)
):
  if not current_user:
    raise HTTPException(
      status_code=status.HTTP_403_FORBIDDEN,
      detail="Not authorized to perform this action"
    )
    
  try:
    service = ChannelService(db)
    return service.get_public_channels_by_project(project_id)
  except HTTPException as e:
    raise e
  except Exception as e:
    raise HTTPException(status_code=400, detail=str(e))

@router.get("/{channel_id}", response_model=ChannelDetail)
def get_channel(
  project_id: str,
  channel_id: str,
  db: Session = Depends(get_db),
  current_user: dict = Depends(get_current_user)
):
  if not current_user:
    raise HTTPException(
      status_code=status.HTTP_403_FORBIDDEN,
      detail="Not authorized to perform this action"
    )
    
  try:
    service = ChannelService(db)
    return service.get(project_id, channel_id)
  except HTTPException as e:
    raise e
  except Exception as e:
    raise HTTPException(status_code=400, detail=str(e))

@router.put("/{channel_id}", response_model=ChannelDetail)
def update_channel(
  project_id: str,
  channel_id: str,
  channel: ChannelUpdate,
  db: Session = Depends(get_db),
  current_user: dict = Depends(get_current_user)
):
  if not current_user:
    raise HTTPException(
      status_code=status.HTTP_403_FORBIDDEN,
      detail="Not authorized to perform this action"
    )
    
  try:
    service = ChannelService(db)
    return service.update(project_id, channel_id, channel)
  except HTTPException as e:
    raise e
  except Exception as e:
    raise HTTPException(status_code=400, detail=str(e))
  
@router.delete("/{channel_id}", response_model=ChannelDetail)
def delete_channel(
  project_id: str,
  channel_id: str,
  db: Session = Depends(get_db),
  current_user: dict = Depends(get_current_user)
):
  if not current_user:
    raise HTTPException(
      status_code=status.HTTP_403_FORBIDDEN,
      detail="Not authorized to perform this action"
    )
    
  try:
    service = ChannelService(db)
    return service.delete(project_id, channel_id)
  except HTTPException as e:
    raise e
  except Exception as e:
    raise HTTPException(status_code=400, detail=str(e))
  
@router.post("/{channel_id}/members", response_model=ChannelDetail)
def add_member_to_channel(
  project_id: str,
  channel_id: str,
  user_id: int,
  db: Session = Depends(get_db),
  current_user: dict = Depends(get_current_user)
):
  if not current_user:
    raise HTTPException(
      status_code=status.HTTP_403_FORBIDDEN,
      detail="Not authorized to perform this action"
    )
    
  try:
    service = ChannelService(db)
    return service.add_member_to_channel(project_id, channel_id, user_id)
  except HTTPException as e:
    raise e
  except Exception as e:
    raise HTTPException(status_code=400, detail=str(e))
  
@router.delete("/{channel_id}/members", response_model=ChannelDetail)
def remove_member_from_channel(
  project_id: str,
  channel_id: str,
  user_id: int,
  db: Session = Depends(get_db),
  current_user: dict = Depends(get_current_user)
):
  if not current_user:
    raise HTTPException(
      status_code=status.HTTP_403_FORBIDDEN,
      detail="Not authorized to perform this action"
    )
    
  try:
    service = ChannelService(db)
    return service.remove_member_from_channel(project_id, channel_id, user_id)
  except HTTPException as e:
    raise e
  except Exception as e:
    raise HTTPException(status_code=400, detail=str(e))
  
@router.get("/{channel_id}/members", response_model=List[UserBrief])
def get_channel_members(
  project_id: str,
  channel_id: str,
  db: Session = Depends(get_db),
  current_user: dict = Depends(get_current_user)
):
  if not current_user:
    raise HTTPException(
      status_code=status.HTTP_403_FORBIDDEN,
      detail="Not authorized to perform this action"
    )
    
  try:
    service = ChannelService(db)
    return service.get_channel_members(project_id, channel_id)
  except HTTPException as e:
    raise e
  except Exception as e:
    raise HTTPException(status_code=400, detail=str(e))
  
@router.get("/{channel_id}/is-member", response_model=bool)
def is_user_member_of_channel(
  project_id: str,
  channel_id: str,
  user_id: int,
  db: Session = Depends(get_db),
  current_user: dict = Depends(get_current_user)
):
  if not current_user:
    raise HTTPException(
      status_code=status.HTTP_403_FORBIDDEN,
      detail="Not authorized to perform this action"
    )
    
  try:
    service = ChannelService(db)
    return service.is_user_member_of_channel(project_id, channel_id, user_id)
  except HTTPException as e:
    raise e
  except Exception as e:
    raise HTTPException(status_code=400, detail=str(e))
