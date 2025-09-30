from pydantic import BaseModel

class CreateOrgRepo(BaseModel):
  github_access_token: str
  repo_name: str
  repo_description: str
  is_private: bool