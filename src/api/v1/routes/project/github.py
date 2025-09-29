from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from api.v1.services.project.github_service import GitHubService
from api.v1.schemas.project.github_schema import CreateOrgRepo
from core.database.database import get_db
from core.security.auth import get_current_user

router = APIRouter(prefix="/api/v1/projects/{project_id}/github", tags=["github"])

@router.post("/create-repo", response_model=dict, status_code=status.HTTP_201_CREATED)
async def create_org_repo(
  project_id: str,
  repo: CreateOrgRepo,
  db: Session = Depends(get_db),
  current_user: dict = Depends(get_current_user)
):
  if not current_user:
    raise HTTPException(
      status_code=status.HTTP_403_FORBIDDEN,
      detail="Not authorized to perform this action"
    )
    
  try:
    service = GitHubService(db)
    return await service.create_org_repo(project_id, repo)
  except HTTPException as e:
    raise e
  except Exception as e:
    raise HTTPException(status_code=400, detail=str(e))
  
@router.delete("/delete-repo", response_model=dict)
async def delete_org_repo(
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
    service = GitHubService(db)
    return await service.delete_org_repo(project_id)
  except HTTPException as e:
    raise e
  except Exception as e:
    raise HTTPException(status_code=400, detail=str(e))