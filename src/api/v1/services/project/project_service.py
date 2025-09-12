from api.v1.repositories.project.project_repository import ProjectRepository
from api.v1.schemas.project.project_schema import ProjectDetail
from fastapi import HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Dict, Any
from api.v1.schemas.project.project_schema import ProjectCreate, ProjectUpdate
from api.v1.models.project.project import Project

class ProjectService:
  def __init__(self, db: Session):
    self.repository = ProjectRepository(db)
  
  def get_project(self, project_id: str) -> ProjectDetail:
    try:
      return self.repository.get(project_id)
    except HTTPException as e:
      if e.status_code == 404:
        raise HTTPException(
          status_code=status.HTTP_404_NOT_FOUND,
          detail=f"Project with id {project_id} not found"
        )
  
  def get_by_user_id(self, user_id: int) -> List[ProjectDetail]:
    try:
      return self.repository.get_by_user_id(user_id)
    except HTTPException as e:
      if e.status_code == 404:
        raise HTTPException(
          status_code=status.HTTP_404_NOT_FOUND,
          detail=f"User with id {user_id} not found"
        )
  
  def get_all_projects_excluding_my(self, user_id: int) -> List[ProjectDetail]:
    try:
      return self.repository.get_all_projects_excluding_my(user_id)
    except HTTPException as e:
      if e.status_code == 404:
        raise HTTPException(
          status_code=status.HTTP_404_NOT_FOUND,
          detail=f"User with id {user_id} not found"
        )
  
  def get_all_project_ids(self) -> List[str]:
    try:
      return self.repository.get_all_project_ids()
    except HTTPException as e:
      if e.status_code == 404:
        raise HTTPException(
          status_code=status.HTTP_404_NOT_FOUND,
          detail="No projects found"
        )
    
  def create_project(self, project: ProjectCreate) -> Project:
    try:
      return self.repository.create(project)
    except HTTPException as e:
      if e.status_code == 404:
        raise HTTPException(
          status_code=status.HTTP_404_NOT_FOUND,
          detail="User with id {project.owner_id} not found"
        )
  
  def update_project(self, project_id: str, project: ProjectUpdate) -> Project:
    try:
      return self.repository.update(project_id, project)
    except HTTPException as e:
      if e.status_code == 404:
        raise HTTPException(
          status_code=status.HTTP_404_NOT_FOUND,
          detail=f"Project with id {project_id} not found"
        )
    
  def remove_project(self, project_id: str) -> Project:
    try:
      return self.repository.remove(project_id)
    except HTTPException as e:
      if e.status_code == 404:
        raise HTTPException(
          status_code=status.HTTP_404_NOT_FOUND,
          detail=f"Project with id {project_id} not found"
        )
  
  def get_project_members(self, project_id: str) -> List[Dict[str, Any]]:
    try:
      return self.repository.get_project_members(project_id)
    except HTTPException as e:
      if e.status_code == 404:
        raise HTTPException(
          status_code=status.HTTP_404_NOT_FOUND,
          detail=f"Project with id {project_id} not found"
        )
    
  def add_member(self, project_id: str, user_id: int) -> Project:
    try:
      return self.repository.add_member(project_id, user_id)
    except HTTPException as e:
      if e.status_code == 404:
        raise HTTPException(
          status_code=status.HTTP_404_NOT_FOUND,
          detail=f"Project with id {project_id} not found"
        )
  
  def remove_member(self, project_id: str, user_id: int) -> Project:
    try:
      return self.repository.remove_member(project_id, user_id)
    except HTTPException as e:
      if e.status_code == 404:
        raise HTTPException(
          status_code=status.HTTP_404_NOT_FOUND,
          detail=f"Project with id {project_id} not found"
        )
        
  def update_project_member_permission(self, project_id: str, user_id: int, permission: str) -> Project:
    try:
      return self.repository.update_project_member_permission(project_id, user_id, permission)
    except HTTPException as e:
      if e.status_code == 404:
        raise HTTPException(
          status_code=status.HTTP_404_NOT_FOUND,
          detail=f"Project with id {project_id} not found"
        )