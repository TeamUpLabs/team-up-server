from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from database import SessionLocal
import requests
import logging
from fastapi import HTTPException, Depends
from crud import project
from utils.sse_manager import project_sse_manager
import json
from models.user import User
from utils.auth import get_current_user

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/api/github",
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
    is_private: bool
    
@router.post("/project/{project_id}/create-repo")
async def create_org_repo(project_id: str, repo: CreateOrgRepo, db: SessionLocal = Depends(get_db)):
    headers = {"Authorization": f"token {repo.github_access_token}", "Accept": "application/vnd.github+json"}
    payload = {
        "name": repo.repo_name,
        "description": repo.repo_description,
        "auto_init": True,
        "private": repo.is_private
    }
    org = "TeamUpLabs"
    res = requests.post(f"https://api.github.com/orgs/{org}/repos", json=payload, headers=headers)
    if res.status_code == 201:
      try:
        db_project = project.get(db, project_id)
        if db_project:
          db_project.github_url = res.json()["html_url"]
          db.add(db_project)
          db.commit()
          
          await project_sse_manager.send_event(
                project_id,
                json.dumps(project_sse_manager.convert_to_dict(db_project))
            )
          return {"success": True, "repo": res.json()}
        else:
          raise HTTPException(status_code=404, detail="Project not found")
      except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    else:
        raise HTTPException(status_code=res.status_code, detail=res.json())
  
@router.delete("/project/{project_id}/delete-repo")
async def delete_org_repo(project_id: str, db: SessionLocal = Depends(get_db)):
  try:
    db_project = project.get(db, project_id)
    if db_project:
      db_project.github_url = None
      db.add(db_project)
      db.commit()
      
      await project_sse_manager.send_event(
            project_id,
            json.dumps(project_sse_manager.convert_to_dict(db_project))
        )
      return {"success": True}
    else:
      raise HTTPException(status_code=404, detail="Project not found")
  except Exception as e:
    raise HTTPException(status_code=500, detail=str(e))