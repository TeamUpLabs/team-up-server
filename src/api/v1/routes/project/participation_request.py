from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from core.database.database import get_db
from api.v1.services.project.participation_request_service import ParticipationRequestService
from api.v1.schemas.project.participation_request_schema import ParticipationRequestCreate, ParticipationRequestUpdate, ParticipationRequestDetail
from core.security.auth import get_current_user
from typing import List, Optional

router = APIRouter(prefix="/api/v1/projects/{project_id}/participation_requests", tags=["participation_requests"])

@router.post("/", response_model=ParticipationRequestDetail, status_code=status.HTTP_201_CREATED)
def create_participation_request(
  project_id: str,
  participation_request: ParticipationRequestCreate,
  db: Session = Depends(get_db),
  current_user: dict = Depends(get_current_user)
):
  if not current_user:
    raise HTTPException(
      status_code=status.HTTP_403_FORBIDDEN,
      detail="Not authorized to perform this action"
    )
    
  try:
    service = ParticipationRequestService(db)
    return service.create(project_id, participation_request)
  except HTTPException as e:
    raise e
  except Exception as e:
    raise HTTPException(status_code=400, detail=str(e))
  
@router.get("/", response_model=List[ParticipationRequestDetail])
def get_participation_requests(
  project_id: str,
  request_id: Optional[int] = None,
  user_id: Optional[int] = None,
  db: Session = Depends(get_db),
  current_user: dict = Depends(get_current_user)
):
  if not current_user:
    raise HTTPException(
      status_code=status.HTTP_403_FORBIDDEN,
      detail="Not authorized to perform this action"
    )
    
  try:
    service = ParticipationRequestService(db)
    if request_id:
      return service.get(project_id, request_id)
    elif user_id:
      return service.get_by_user(project_id, user_id)
    else:
      return service.get_by_project(project_id)
  except HTTPException as e:
    raise e
  except Exception as e:
    raise HTTPException(status_code=400, detail=str(e))
  
@router.put("/{request_id}", response_model=ParticipationRequestDetail)
def update_participation_request(
  project_id: str,
  request_id: int,
  participation_request: ParticipationRequestUpdate,
  db: Session = Depends(get_db),
  current_user: dict = Depends(get_current_user)
):
  if not current_user:
    raise HTTPException(
      status_code=status.HTTP_403_FORBIDDEN,
      detail="Not authorized to perform this action"
    )
    
  try:
    service = ParticipationRequestService(db)
    return service.update(project_id, request_id, participation_request)
  except HTTPException as e:
    raise e
  except Exception as e:
    raise HTTPException(status_code=400, detail=str(e))
  
@router.delete("/{request_id}", response_model=ParticipationRequestDetail)
def delete_participation_request(
  project_id: str,
  request_id: int,
  db: Session = Depends(get_db),
  current_user: dict = Depends(get_current_user)
):
  if not current_user:
    raise HTTPException(
      status_code=status.HTTP_403_FORBIDDEN,
      detail="Not authorized to perform this action"
    )
    
  try:
    service = ParticipationRequestService(db)
    return service.remove(project_id, request_id)
  except HTTPException as e:
    raise e
  except Exception as e:
    raise HTTPException(status_code=400, detail=str(e))
  
@router.get("/check", response_model=bool)
def check_existing_participation_request(
  project_id: str,
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
    service = ParticipationRequestService(db)
    return service.check_existing_request(project_id, user_id)
  except HTTPException as e:
    raise e
  except Exception as e:
    raise HTTPException(status_code=400, detail=str(e))

@router.put("/accept/{request_id}", response_model=ParticipationRequestDetail)
def accept_participation_request(
  project_id: str,
  request_id: int,
  db: Session = Depends(get_db),
  current_user: dict = Depends(get_current_user)
):
  if not current_user:
    raise HTTPException(
      status_code=status.HTTP_403_FORBIDDEN,
      detail="Not authorized to perform this action"
    )
    
  try:
    service = ParticipationRequestService(db)
    return service.accept(project_id, request_id)
  except HTTPException as e:
    raise e
  except Exception as e:
    raise HTTPException(status_code=400, detail=str(e))
