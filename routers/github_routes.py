from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from database import SessionLocal
import requests
import logging
from fastapi import HTTPException

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/github",
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
    
@router.post("/org/create-repo")
def create_org_repo(repo: CreateOrgRepo):
    github_token = repo.github_access_token
    headers = {"Authorization": f"token {github_token}", "Accept": "application/vnd.github+json"}
    payload = {
        "name": repo.repo_name,
        "private": True,
        "auto_init": True,
    }
    org = "TeamUpLabs"
    res = requests.post(f"https://api.github.com/orgs/{org}/repos", json=payload, headers=headers)
    if res.status_code == 201:
        return {"success": True, "repo": res.json()}
    else:
        raise HTTPException(status_code=res.status_code, detail=res.json())