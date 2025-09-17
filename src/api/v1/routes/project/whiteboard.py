from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from core.database.database import get_db
from api.v1.services.project.whiteboard_service import WhiteBoardService
from api.v1.schemas.project.whiteboard_schema import WhiteBoardCreate, WhiteBoardUpdate, WhiteBoardDetail
from core.security.auth import get_current_user
from typing import List

router = APIRouter(prefix="/api/v1/projects/{project_id}/whiteboards", tags=["whiteboards"])

@router.get("/", response_model=List[WhiteBoardDetail])
async def get_all_whiteboards(
  project_id: str,
  skip: int = 0,
  limit: int = 100,
  db: Session = Depends(get_db),
  current_user: dict = Depends(get_current_user)
):
  if not current_user:
    raise HTTPException(
      status_code=status.HTTP_403_FORBIDDEN,
      detail="Not authorized to perform this action"
    )
    
  try:
    service = WhiteBoardService(db)
    return service.get_by_project(project_id, skip, limit)
  except HTTPException as e:
    raise e
  except Exception as e:
    raise HTTPException(status_code=400, detail=str(e))
    
@router.get("/{whiteboard_id}", response_model=WhiteBoardDetail)
async def get_whiteboard_by_id(
  project_id: str,
  whiteboard_id: int,
  db: Session = Depends(get_db),
  current_user: dict = Depends(get_current_user)
):
  if not current_user:
    raise HTTPException(
      status_code=status.HTTP_403_FORBIDDEN,
      detail="Not authorized to perform this action"
    )
    
  try:
    service = WhiteBoardService(db)
    return service.get(project_id, whiteboard_id)
  except HTTPException as e:
    raise e
  except Exception as e:
    raise HTTPException(status_code=400, detail=str(e))
    
@router.post("/", response_model=WhiteBoardDetail)
async def create_whiteboard(
  project_id: str,
  whiteboard: WhiteBoardCreate,
  db: Session = Depends(get_db),
  current_user: dict = Depends(get_current_user)
):
  if not current_user:
    raise HTTPException(
      status_code=status.HTTP_403_FORBIDDEN,
      detail="Not authorized to perform this action"
    )
    
  try:
    service = WhiteBoardService(db)
    return service.create(project_id, whiteboard)
  except HTTPException as e:
    raise e
  except Exception as e:
    raise HTTPException(status_code=400, detail=str(e))
    
@router.put("/{whiteboard_id}", response_model=WhiteBoardDetail)
async def update_whiteboard(
  project_id: str,
  whiteboard_id: int,
  whiteboard: WhiteBoardUpdate,
  db: Session = Depends(get_db),
  current_user: dict = Depends(get_current_user)
):
  if not current_user:
    raise HTTPException(
      status_code=status.HTTP_403_FORBIDDEN,
      detail="Not authorized to perform this action"
    )
    
  try:
    service = WhiteBoardService(db)
    return service.update(project_id, whiteboard_id, whiteboard)
  except HTTPException as e:
    raise e
  except Exception as e:
    raise HTTPException(status_code=400, detail=str(e))
    
@router.delete("/{whiteboard_id}", response_model=WhiteBoardDetail)
async def delete_whiteboard(
  project_id: str,
  whiteboard_id: int,
  db: Session = Depends(get_db),
  current_user: dict = Depends(get_current_user)
):
  if not current_user:
    raise HTTPException(
      status_code=status.HTTP_403_FORBIDDEN,
      detail="Not authorized to perform this action"
    )
    
  try:
    service = WhiteBoardService(db)
    return service.delete(project_id, whiteboard_id)
  except HTTPException as e:
    raise e
  except Exception as e:
    raise HTTPException(status_code=400, detail=str(e))