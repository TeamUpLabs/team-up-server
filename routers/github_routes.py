from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from typing import Optional, Dict, Any
from database import SessionLocal
from crud.auth import get_github_access_token
from auth import get_current_user
from models.member import Member
import requests
import logging
from fastapi.security import OAuth2PasswordBearer

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

class CreateRepoRequest(BaseModel):
    repo_name: str
    github_token: str

@router.post("/org/create-repo")
def create_org_repo(payload: CreateRepoRequest):
    headers = {
        "Authorization": f"token {payload.github_token}",
        "Accept": "application/vnd.github+json",
    }

    org = "TeamUpLabs"
    repo_payload = {
        "name": payload.repo_name,
        "private": True,
        "auto_init": True,
    }

    res = requests.post(
        f"https://api.github.com/orgs/{org}/repos",
        json=repo_payload,
        headers=headers
    )

    if res.status_code == 201:
        return {"success": True, "repo": res.json()}
    else:
        raise HTTPException(
            status_code=res.status_code,
            detail={
                "error": "GitHub 레포 생성 실패",
                "github_response": res.json()
            }
        )