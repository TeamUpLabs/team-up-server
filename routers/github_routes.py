from stat import SF_DATALESS
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from database import SessionLocal
import requests
import logging
from fastapi import HTTPException, Depends
from crud.project import get_project
from utils.sse_manager import project_sse_manager
import json

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/project",
    tags=["github"]
)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

class CreateOrgRepo(BaseModel):
    github_access_token: str
    repo_name: str
    repo_description: str
    isPrivate: bool
    
@router.post("/{project_id}/github/org/create-repo")
async def create_org_repo(project_id: str, repo: CreateOrgRepo, db: SessionLocal = Depends(get_db)):
    github_token = repo.github_access_token
    headers = {"Authorization": f"token {github_token}", "Accept": "application/vnd.github+json"}
    payload = {
        "name": repo.repo_name,
        "description": repo.repo_description,
        "auto_init": True,
        "private": repo.isPrivate
    }
    org = "TeamUpLabs"
    res = requests.post(f"https://api.github.com/orgs/{org}/repos", json=payload, headers=headers)
    if res.status_code == 201:
      try:
        project = get_project(db, project_id)
        if project:
          project.github_repo_url = res.json()["html_url"]
          db.add(project)
          db.commit()
          
          await project_sse_manager.send_event(
                project_id,
                json.dumps(project_sse_manager.convert_to_dict(project))
            )
          return {"success": True, "repo": res.json()}
        else:
          raise HTTPException(status_code=404, detail="Project not found")
      except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    else:
        raise HTTPException(status_code=res.status_code, detail=res.json())
  
@router.delete("/{project_id}/github/org/delete-repo")
async def delete_org_repo(project_id: str, db: SessionLocal = Depends(get_db)):
  try:
    project = get_project(db, project_id)
    if project:
      project.github_repo_url = None
      db.add(project)
      db.commit()
      
      await project_sse_manager.send_event(
            project_id,
            json.dumps(project_sse_manager.convert_to_dict(project))
        )
      return {"success": True}
    else:
      raise HTTPException(status_code=404, detail="Project not found")
  except Exception as e:
    raise HTTPException(status_code=500, detail=str(e))