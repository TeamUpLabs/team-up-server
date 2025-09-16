from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from core.database.database import get_db
from api.v1.services.project.task_service import TaskService
from api.v1.schemas.project.task_schema import TaskCreate, TaskUpdate, CommentCreate, CommentUpdate
from core.security.auth import get_current_user
from typing import List, Optional
from api.v1.schemas.project.task_schema import TaskDetail, CommentDetail

router = APIRouter(prefix="/api/v1/projects/{project_id}/tasks", tags=["tasks"])

@router.get("/", response_model=List[TaskDetail])
async def get_all_tasks(
  project_id: str,
  milestone_id: Optional[int] = None,
  assignee_id: Optional[int] = None,
  db: Session = Depends(get_db),
  current_user: dict = Depends(get_current_user)
):
  if not current_user:
    raise HTTPException(
      status_code=status.HTTP_403_FORBIDDEN,
      detail="Not authorized to perform this action"
    )
    
  try:
    service = TaskService(db)
    if milestone_id:
      return service.get_all_tasks_by_milestone_id(project_id, milestone_id)
    elif assignee_id:
      return service.get_all_tasks_by_assignee_id(project_id, assignee_id)
    else:
      return service.get_all_tasks_by_project_id(project_id)
  except HTTPException as e:
    raise e
  except Exception as e:
    raise HTTPException(status_code=400, detail=str(e))
  
@router.get("/{task_id}", response_model=TaskDetail)
async def get_task_by_id(
  project_id: str,
  task_id: int,
  db: Session = Depends(get_db),
  current_user: dict = Depends(get_current_user)
):
  if not current_user:
    raise HTTPException(
      status_code=status.HTTP_403_FORBIDDEN,
      detail="Not authorized to perform this action"
    )
    
  try:
    service = TaskService(db)
    return service.get(project_id, task_id)
  except HTTPException as e:
    raise e
  except Exception as e:
    raise HTTPException(status_code=400, detail=str(e))
  
@router.post("/", response_model=TaskDetail)
async def create_task(
  project_id: str,
  task: TaskCreate,
  db: Session = Depends(get_db),
  current_user: dict = Depends(get_current_user)
):
  if not current_user:
    raise HTTPException(
      status_code=status.HTTP_403_FORBIDDEN,
      detail="Not authorized to perform this action"
    )
    
  try:
    service = TaskService(db)
    return service.create(project_id, task)
  except HTTPException as e:
    raise e
  except Exception as e:
    raise HTTPException(status_code=400, detail=str(e))
  
@router.put("/{task_id}", response_model=TaskDetail)
async def update_task(
  project_id: str,
  task_id: int,
  task: TaskUpdate,
  db: Session = Depends(get_db),
  current_user: dict = Depends(get_current_user)
):
  if not current_user:
    raise HTTPException(
      status_code=status.HTTP_403_FORBIDDEN,
      detail="Not authorized to perform this action"
    )
    
  try:
    service = TaskService(db)
    return service.update(project_id, task_id, task)
  except HTTPException as e:
    raise e
  except Exception as e:
    raise HTTPException(status_code=400, detail=str(e))
  
@router.delete("/{task_id}", response_model=TaskDetail)
async def delete_task(
  project_id: str,
  task_id: int,
  db: Session = Depends(get_db),
  current_user: dict = Depends(get_current_user)
):
  if not current_user:
    raise HTTPException(
      status_code=status.HTTP_403_FORBIDDEN,
      detail="Not authorized to perform this action"
    )
    
  try:
    service = TaskService(db)
    return service.delete(project_id, task_id)
  except HTTPException as e:
    raise e
  except Exception as e:
    raise HTTPException(status_code=400, detail=str(e))
  
@router.get("/{task_id}/comments", response_model=List[CommentDetail])
async def get_task_comments(
  project_id: str,
  task_id: int,
  db: Session = Depends(get_db),
  current_user: dict = Depends(get_current_user)
):
  if not current_user:
    raise HTTPException(
      status_code=status.HTTP_403_FORBIDDEN,
      detail="Not authorized to perform this action"
    )
    
  try:
    service = TaskService(db)
    return service.get_comments(project_id, task_id)
  except HTTPException as e:
    raise e
  except Exception as e:
    raise HTTPException(status_code=400, detail=str(e))
  
@router.post("/{task_id}/comments", response_model=CommentDetail)
async def create_task_comment(
  project_id: str,
  task_id: int,
  comment: CommentCreate,
  db: Session = Depends(get_db),
  current_user: dict = Depends(get_current_user)
):
  if not current_user:
    raise HTTPException(
      status_code=status.HTTP_403_FORBIDDEN,
      detail="Not authorized to perform this action"
    )
    
  try:
    service = TaskService(db)
    return service.add_comment(project_id, task_id, comment)
  except HTTPException as e:
    raise e
  except Exception as e:
    raise HTTPException(status_code=400, detail=str(e)) 
  
@router.put("/{task_id}/comments/{comment_id}", response_model=CommentDetail)
async def update_task_comment(
  project_id: str,
  task_id: int,
  comment_id: int,
  comment: CommentUpdate,
  db: Session = Depends(get_db),
  current_user: dict = Depends(get_current_user)
):
  if not current_user:
    raise HTTPException(
      status_code=status.HTTP_403_FORBIDDEN,
      detail="Not authorized to perform this action"
    )
    
  try:
    service = TaskService(db)
    return service.update_comment(project_id, task_id, comment_id, comment)
  except HTTPException as e:
    raise e
  except Exception as e:
    raise HTTPException(status_code=400, detail=str(e))

@router.delete("/{task_id}/comments/{comment_id}", response_model=CommentDetail)
async def delete_task_comment(
  project_id: str,
  task_id: int,
  comment_id: int,
  db: Session = Depends(get_db),
  current_user: dict = Depends(get_current_user)
):
  if not current_user:
    raise HTTPException(
      status_code=status.HTTP_403_FORBIDDEN,
      detail="Not authorized to perform this action"
    )
    
  try:
    service = TaskService(db)
    return service.remove_comment(project_id, task_id, comment_id)
  except HTTPException as e:
    raise e
  except Exception as e:
    raise HTTPException(status_code=400, detail=str(e))