from fastapi import APIRouter, Depends, HTTPException, status, Path, Body
from sqlalchemy.orm import Session
from src.core.database.database import get_db
from src.api.v1.services.project.milestone_service import MilestoneService
from src.api.v1.schemas.project.milestone_schema import MilestoneCreate, MilestoneUpdate, MilestoneDetail
from src.api.v1.schemas.project.task_schema import TaskDetail
from src.api.v1.schemas.brief import UserBrief
from src.core.security.auth import get_current_user
from typing import List

router = APIRouter(prefix="/api/v1/projects/{project_id}/milestones", tags=["milestones"])

@router.post("/", response_model=MilestoneDetail, status_code=status.HTTP_201_CREATED)
def create_milestone(
  project_id: str,
  milestone: MilestoneCreate,
  db: Session = Depends(get_db),
  current_user: dict = Depends(get_current_user)
):
  if not current_user:
    raise HTTPException(
      status_code=status.HTTP_403_FORBIDDEN,
      detail="Not authorized to perform this action"
    )
    
  try:
    service = MilestoneService(db)
    return service.create(project_id=project_id, milestone=milestone)
  except HTTPException as e:
    raise e
  except Exception as e:
    raise HTTPException(status_code=400, detail=str(e))
  
@router.get("/", response_model=List[MilestoneDetail])
def get_all_milestones(
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
    service = MilestoneService(db)
    return service.get_by_project(project_id=project_id)
  except HTTPException as e:
    raise e
  except Exception as e:
    raise HTTPException(status_code=400, detail=str(e))

@router.get("/{milestone_id}", response_model=MilestoneDetail)
def get_milestone_by_id(
  project_id: str,
  milestone_id: int,
  db: Session = Depends(get_db),
  current_user: dict = Depends(get_current_user)
):
  if not current_user:
    raise HTTPException(
      status_code=status.HTTP_403_FORBIDDEN,
      detail="Not authorized to perform this action"
    )
    
  try:
    service = MilestoneService(db)
    return service.get(project_id=project_id, milestone_id=milestone_id)
  except HTTPException as e:
    raise e
  except Exception as e:
    raise HTTPException(status_code=400, detail=str(e))
  
@router.put("/{milestone_id}", response_model=MilestoneDetail)
def update_milestone(
  project_id: str,
  milestone_id: int,
  milestone: MilestoneUpdate,
  db: Session = Depends(get_db),
  current_user: dict = Depends(get_current_user)
):
  if not current_user:
    raise HTTPException(
      status_code=status.HTTP_403_FORBIDDEN,
      detail="Not authorized to perform this action"
    )
    
  try:
    service = MilestoneService(db)
    return service.update(project_id=project_id, milestone_id=milestone_id, milestone=milestone)
  except HTTPException as e:
    raise e
  except Exception as e:
    raise HTTPException(status_code=400, detail=str(e))
  
@router.delete("/{milestone_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_milestone(
  project_id: str,
  milestone_id: int,
  db: Session = Depends(get_db),
  current_user: dict = Depends(get_current_user)
):
  if not current_user:
    raise HTTPException(
      status_code=status.HTTP_403_FORBIDDEN,
      detail="Not authorized to perform this action"
    )
    
  try:
    service = MilestoneService(db)
    service.delete(project_id=project_id, milestone_id=milestone_id)
    return None
  except HTTPException as e:
    raise e
  except Exception as e:
    raise HTTPException(status_code=400, detail=str(e))
  
@router.get("/{milestone_id}/tasks", response_model=List[TaskDetail])
def get_all_tasks_by_milestone_id(
  db: Session = Depends(get_db),
  project_id: str = Path(..., title="Project ID"),
  milestone_id: int = Path(..., title="Milestone ID"),
  current_user: dict = Depends(get_current_user)
):
  if not current_user:
    raise HTTPException(
      status_code=status.HTTP_403_FORBIDDEN,
      detail="Not authorized to perform this action"
    )
    
  try:
    service = MilestoneService(db)
    return service.get_all_tasks_by_milestone_id(project_id=project_id, milestone_id=milestone_id)
  except HTTPException as e:
    raise e
  except Exception as e:
    raise HTTPException(status_code=400, detail=str(e))
  
@router.get("/{milestone_id}/assignees", response_model=List[UserBrief])
def get_all_assignees_by_milestone_id(
  db: Session = Depends(get_db),
  project_id: str = Path(..., title="Project ID"),
  milestone_id: int = Path(..., title="Milestone ID"),
  current_user: dict = Depends(get_current_user)
):
  if not current_user:
    raise HTTPException(
      status_code=status.HTTP_403_FORBIDDEN,
      detail="Not authorized to perform this action"
    )
    
  try:
    service = MilestoneService(db)
    return service.get_all_assignees_by_milestone_id(project_id=project_id, milestone_id=milestone_id)
  except HTTPException as e:
    raise e
  except Exception as e:
    raise HTTPException(status_code=400, detail=str(e))
  
@router.post("/{milestone_id}/assignees", response_model=MilestoneDetail)
def add_assignee_to_milestone(
  db: Session = Depends(get_db),
  project_id: str = Path(..., title="Project ID"),
  milestone_id: int = Path(..., title="Milestone ID"),
  user_id: int = Path(..., title="User ID"),
  current_user: dict = Depends(get_current_user)
):
  if not current_user:
    raise HTTPException(
      status_code=status.HTTP_403_FORBIDDEN,
      detail="Not authorized to perform this action"
    )
    
  try:
    service = MilestoneService(db)
    return service.add_assignee_to_milestone(project_id=project_id, milestone_id=milestone_id, user_id=user_id)
  except HTTPException as e:
    raise e
  except Exception as e:
    raise HTTPException(status_code=400, detail=str(e))
  
@router.delete("/{milestone_id}/assignees", response_model=MilestoneDetail)
def remove_assignee_from_milestone(
  db: Session = Depends(get_db),
  project_id: str = Path(..., title="Project ID"),
  milestone_id: int = Path(..., title="Milestone ID"),
  user_id: int = Path(..., title="User ID"),
  current_user: dict = Depends(get_current_user)
):
  if not current_user:
    raise HTTPException(
      status_code=status.HTTP_403_FORBIDDEN,
      detail="Not authorized to perform this action"
    )
    
  try:
    service = MilestoneService(db)
    return service.remove_assignee_from_milestone(project_id=project_id, milestone_id=milestone_id, user_id=user_id)
  except HTTPException as e:
    raise e
  except Exception as e:
    raise HTTPException(status_code=400, detail=str(e))
  
@router.get("/{milestone_id}/is-project-manager", response_model=bool)
def is_project_manager(
  db: Session = Depends(get_db),
  project_id: str = Path(..., title="Project ID"),
  milestone_id: int = Path(..., title="Milestone ID"),
  current_user: dict = Depends(get_current_user)
):
  if not current_user:
    raise HTTPException(
      status_code=status.HTTP_403_FORBIDDEN,
      detail="Not authorized to perform this action"
    )
    
  try:
    service = MilestoneService(db)
    return service.is_project_manager(project_id=project_id, milestone_id=milestone_id)
  except HTTPException as e:
    raise e
  except Exception as e:
    raise HTTPException(status_code=400, detail=str(e))
