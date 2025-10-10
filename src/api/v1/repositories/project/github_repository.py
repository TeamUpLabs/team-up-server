from sqlalchemy.orm import Session
from src.api.v1.schemas.project.github_schema import CreateOrgRepo
import requests
from src.api.v1.models.project.project import Project
from fastapi import HTTPException


class GitHubRepository:
  def __init__(self, db: Session):
    self.db = db
    
  async def create_org_repo(self, project_id: str, repo: CreateOrgRepo):
    try:
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
          db_project = self.db.query(Project).filter(Project.id == project_id).first()
          if db_project:
            db_project.github_url = res.json()["html_url"]
            self.db.add(db_project)
            self.db.commit()
            self.db.refresh(db_project)
            
            return {"success": True, "repo": res.json()}
          else:
            raise HTTPException(status_code=404, detail="Project not found")
        except Exception as e:
          raise HTTPException(status_code=500, detail=str(e))
      else:
        raise HTTPException(status_code=res.status_code, detail=res.json())
    except Exception as e:
      raise HTTPException(status_code=500, detail=str(e))
      
  async def delete_org_repo(self, project_id: str):
    try:
      db_project = self.db.query(Project).filter(Project.id == project_id).first()
      if db_project:
        db_project.github_url = None
        self.db.add(db_project)
        self.db.commit()
        self.db.refresh(db_project)
        
        return {"success": True}
      else:
        raise HTTPException(status_code=404, detail="Project not found")
    except Exception as e:
      raise HTTPException(status_code=500, detail=str(e))