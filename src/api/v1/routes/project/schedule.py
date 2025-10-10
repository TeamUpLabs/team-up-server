from fastapi import APIRouter
from sqlalchemy.orm import Session
from src.core.database.database import get_db
from src.api.v1.services.project.schedule_service import ScheduleService
from src.api.v1.schemas.project.schedule_schema import ScheduleCreate, ScheduleUpdate, ScheduleDetail
from src.core.security.auth import get_current_user
from typing import List
from fastapi import HTTPException, status, Depends

router = APIRouter(prefix="/api/v1/projects/{project_id}/schedules", tags=["schedules"])

@router.post("/", response_model=ScheduleDetail)
def create_schedule(
  project_id: str,
  obj_in: ScheduleCreate,
  db: Session = Depends(get_db),
  current_user: dict = Depends(get_current_user)
):
  if not current_user:
    raise HTTPException(
      status_code=status.HTTP_403_FORBIDDEN,
      detail="Not authorized to perform this action"
    )
    
  try:
    service = ScheduleService(db)
    return service.create(project_id, obj_in)
  except HTTPException as e:
    raise e
  except Exception as e:
    raise HTTPException(status_code=400, detail=str(e))

@router.get("/", response_model=List[ScheduleDetail])
def get_by_project(
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
    service = ScheduleService(db)
    return service.get_by_project(project_id)
  except HTTPException as e:
    raise e
  except Exception as e:
    raise HTTPException(status_code=400, detail=str(e))

@router.get("/{schedule_id}", response_model=ScheduleDetail)
def get_by_id(
  project_id: str,
  schedule_id: int, 
  db: Session = Depends(get_db), 
  current_user: dict = Depends(get_current_user)
):
  if not current_user:
    raise HTTPException(
      status_code=status.HTTP_403_FORBIDDEN,
      detail="Not authorized to perform this action"
    )
    
  try:
    service = ScheduleService(db)
    return service.get_by_id(project_id, schedule_id)
  except HTTPException as e:
    raise e
  except Exception as e:
    raise HTTPException(status_code=400, detail=str(e))

@router.put("/{schedule_id}", response_model=ScheduleDetail)
def update(
  project_id: str,
  schedule_id: int, 
  obj_in: ScheduleUpdate, 
  db: Session = Depends(get_db), 
  current_user: dict = Depends(get_current_user)
):
  if not current_user:
    raise HTTPException(
      status_code=status.HTTP_403_FORBIDDEN,
      detail="Not authorized to perform this action"
    )
    
  try:
    service = ScheduleService(db)
    return service.update(project_id, schedule_id, obj_in)
  except HTTPException as e:
    raise e
  except Exception as e:
    raise HTTPException(status_code=400, detail=str(e))

@router.delete("/{schedule_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete(
  project_id: str,
  schedule_id: int, 
  db: Session = Depends(get_db), 
  current_user: dict = Depends(get_current_user)
):
  if not current_user:
    raise HTTPException(
      status_code=status.HTTP_403_FORBIDDEN,
      detail="Not authorized to perform this action"
    )
    
  try:
    service = ScheduleService(db)
    service.delete(project_id, schedule_id)
    return None
  except HTTPException as e:
    raise e
  except Exception as e:
    raise HTTPException(status_code=400, detail=str(e))
