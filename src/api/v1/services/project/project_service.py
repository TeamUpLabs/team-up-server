from src.api.v1.repositories.project.project_repository import ProjectRepository
from src.api.v1.schemas.project.project_schema import ProjectDetail
from sqlalchemy.orm import Session
from typing import List, Dict, Any
from src.api.v1.schemas.project.project_schema import ProjectCreate, ProjectUpdate
from src.api.v1.models.project.project import Project

class ProjectService:
  def __init__(self, db: Session):
    self.repository = ProjectRepository(db)
  
  def get_project(self, project_id: str) -> ProjectDetail:
    return self.repository.get(project_id)
        
  def get_all_projects(self) -> List[ProjectDetail]:
    return self.repository.get_all_projects()
  
  def get_by_user_id(self, user_id: int) -> List[ProjectDetail]:
    return self.repository.get_by_user_id(user_id)
  
  def get_all_projects_excluding_my(self, user_id: int) -> List[ProjectDetail]:
    return self.repository.get_all_projects_excluding_my(user_id)
  
  def get_all_project_ids(self) -> List[str]:
    return self.repository.get_all_project_ids()
    
  def create_project(self, project: ProjectCreate) -> Project:
    return self.repository.create(project)
  
  def update_project(self, project_id: str, project: ProjectUpdate) -> Project:
    return self.repository.update(project_id, project)
    
  def delete_project(self, project_id: str) -> Project:
    return self.repository.delete(project_id)
  
  def get_project_members(self, project_id: str) -> List[Dict[str, Any]]:
    return self.repository.get_project_members(project_id)
    
  def add_member(self, project_id: str, user_id: int) -> Project:
    return self.repository.add_member(project_id, user_id)
    
  def remove_member(self, project_id: str, user_id: int) -> Project:
    return self.repository.remove_member(project_id, user_id)
    
  def update_project_member_permission(self, project_id: str, user_id: int, permission: str) -> Project:
    return self.repository.update_project_member_permission(project_id, user_id, permission)
  
  def remove_member(self, project_id: str, user_id: int) -> Project:
    return self.repository.remove_member(project_id, user_id)
        
  def update_project_member_permission(self, project_id: str, user_id: int, permission: str) -> Project:
    return self.repository.update_project_member_permission(project_id, user_id, permission)