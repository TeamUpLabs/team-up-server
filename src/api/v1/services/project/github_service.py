from sqlalchemy.orm import Session
from api.v1.repositories.project.github_repository import GitHubRepository
from api.v1.schemas.project.github_schema import CreateOrgRepo

class GitHubService:
  def __init__(self, db: Session):
    self.repository = GitHubRepository(db)
  
  async def create_org_repo(self, project_id: str, repo: CreateOrgRepo):
    return await self.repository.create_org_repo(project_id, repo)
  
  async def delete_org_repo(self, project_id: str):
    return await self.repository.delete_org_repo(project_id)