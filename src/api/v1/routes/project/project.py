from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from core.database.database import get_db
from api.v1.services.project.project_service import ProjectService
from api.v1.schemas.project.project_schema import ProjectCreate, ProjectUpdate, ProjectDetail
from core.security.auth import get_current_user
from typing import List, Dict, Any
from core.utils.sse_manager import project_sse_manager
from fastapi.responses import StreamingResponse
from fastapi import Request
import json

router = APIRouter(prefix="/api/v1/projects", tags=["projects"])

@router.post("/", response_model=ProjectDetail, status_code=status.HTTP_201_CREATED)
async def create_project(
  project: ProjectCreate,
  db: Session = Depends(get_db),
  current_user: dict = Depends(get_current_user)
):
  if not current_user:
    raise HTTPException(
      status_code=status.HTTP_403_FORBIDDEN,
      detail="Not authorized to perform this action"
    )
    
  try:
    service = ProjectService(db)
    return service.create_project(project)
  except HTTPException as e:
    raise e
  except Exception as e:
    raise HTTPException(status_code=400, detail=str(e))
  
@router.get("/ids", response_model=List[str])
async def get_all_project_ids(
  db: Session = Depends(get_db),
  current_user: dict = Depends(get_current_user)
):
  if not current_user:
    raise HTTPException(
      status_code=status.HTTP_403_FORBIDDEN,
      detail="Not authorized to perform this action"
    )
    
  try:
    service = ProjectService(db)
    return service.get_all_project_ids()
  except HTTPException as e:
    raise e
  except Exception as e:
    raise HTTPException(status_code=400, detail=str(e))
  
@router.get("/", response_model=List[ProjectDetail])
async def get_all_projects_by_user(
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
    service = ProjectService(db)
    return service.get_by_user_id(user_id)
  except HTTPException as e:
    raise e
  except Exception as e:
    raise HTTPException(status_code=400, detail=str(e))
  
@router.get("/all", response_model=List[ProjectDetail])
async def get_all_projects(
  db: Session = Depends(get_db),
  current_user: dict = Depends(get_current_user)
):
  if not current_user:
    raise HTTPException(
      status_code=status.HTTP_403_FORBIDDEN,
      detail="Not authorized to perform this action"
    )
    
  try:
    service = ProjectService(db)
    return service.get_all_projects()
  except HTTPException as e:
    raise e
  except Exception as e:
    raise HTTPException(status_code=400, detail=str(e))
  
@router.get("/exclude", response_model=List[ProjectDetail])
async def get_all_projects_excluding_my(
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
    service = ProjectService(db)
    return service.get_all_projects_excluding_my(user_id)
  except HTTPException as e:
    raise e
  except Exception as e:
    raise HTTPException(status_code=400, detail=str(e))

@router.get("/{project_id}", response_model=ProjectDetail)
async def get_project(
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
    service = ProjectService(db)
    return service.get_project(project_id)
  except HTTPException as e:
    raise e
  except Exception as e:
    raise HTTPException(status_code=404, detail=str(e))


@router.put("/{project_id}", response_model=ProjectDetail)
async def update_project(
  project_id: str,
  project: ProjectUpdate,
  db: Session = Depends(get_db),
  current_user: dict = Depends(get_current_user)
):
  if not current_user:
    raise HTTPException(
      status_code=status.HTTP_403_FORBIDDEN,
      detail="Not authorized to perform this action"
    )
    
  try:
    service = ProjectService(db)
    return service.update_project(project_id, project)
  except HTTPException as e:
    raise e
  except Exception as e:
    raise HTTPException(status_code=400, detail=str(e))
  
  
@router.delete("/{project_id}", response_model=ProjectDetail)
async def delete_project(
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
    service = ProjectService(db)
    return service.delete_project(project_id)
  except HTTPException as e:
    raise e
  except Exception as e:
    raise HTTPException(status_code=400, detail=str(e))

@router.get("/{project_id}/members", response_model=List[Dict[str, Any]])
async def get_project_members(
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
    service = ProjectService(db)
    return service.get_project_members(project_id)
  except HTTPException as e:
    raise e
  except Exception as e:
    raise HTTPException(status_code=400, detail=str(e))
  
@router.get("/{project_id}/sse")
async def read_project_sse(project_id: str, request: Request, db: Session = Depends(get_db)):
  """프로젝트 SSE 연결"""
  queue = await project_sse_manager.connect(project_id)
  
  async def event_generator():
    try:
      service = ProjectService(db)
      db_project = service.get_project(project_id)
      if db_project:
        project_dict = project_sse_manager.convert_to_dict(db_project)
        yield f"data: {json.dumps(project_dict)}\n\n"
    finally:
      db.close()
        
    async for event in project_sse_manager.event_generator(project_id, queue):
      if await request.is_disconnected():
        await project_sse_manager.disconnect(project_id, queue)
        break
      yield event
          
  return StreamingResponse(
    event_generator(),
    media_type="text/event-stream",
    headers={
      "Cache-Control": "no-cache",
      "Connection": "keep-alive",
      "X-Accel-Buffering": "no",
      "Access-Control-Allow-Origin": "*"  # Add CORS header
    }
  )

