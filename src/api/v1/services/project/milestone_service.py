from api.v1.models.project.milestone import Milestone
from api.v1.repositories.project.milestone_repository import MilestoneRepository
from api.v1.schemas.project.milestone_schema import MilestoneCreate, MilestoneUpdate, MilestoneDetail
from api.v1.schemas.project.task_schema import TaskDetail
from api.v1.schemas.brief import UserBrief
from sqlalchemy.orm import Session
from typing import List

class MilestoneService:
  def __init__(self, db: Session):
    self.repository = MilestoneRepository(db)
  
  def create(self, project_id: str, milestone: MilestoneCreate) -> Milestone:
    return self.repository.create(project_id, milestone)
  
  def update(self, project_id: str, milestone_id: int, milestone: MilestoneUpdate) -> Milestone:
    return self.repository.update(project_id, milestone_id, milestone)
    
  def remove(self, project_id: str, milestone_id: int) -> Milestone:
    return self.repository.remove(project_id, milestone_id)
  
  def get(self, project_id: str, milestone_id: int) -> MilestoneDetail:
    return self.repository.get(project_id, milestone_id)
    
  def get_by_project(self, *, project_id: str, skip: int = 0, limit: int = 100) -> List[MilestoneDetail]:
    return self.repository.get_by_project(project_id=project_id, skip=skip, limit=limit)
    
  def get_by_assignee(self, *, user_id: int, skip: int = 0, limit: int = 100) -> List[MilestoneDetail]:
    return self.repository.get_by_assignee(user_id=user_id, skip=skip, limit=limit)
    
  def get_tasks(self, *, project_id: str, milestone_id: int) -> List[TaskDetail]:
    return self.repository.get_tasks(project_id=project_id, milestone_id=milestone_id)
    
  def get_assignees(self, *, project_id: str, milestone_id: int) -> List[UserBrief]:
    return self.repository.get_assignees(project_id=project_id, milestone_id=milestone_id)
    
  def add_assignee(self, project_id: str, milestone_id: int, user_id: int) -> Milestone:
    return self.repository.add_assignee(project_id, milestone_id, user_id)
    
  def remove_assignee(self, project_id: str, milestone_id: int, user_id: int) -> Milestone:
    return self.repository.remove_assignee(project_id, milestone_id, user_id)
    
  def is_project_manager(self, project_id: str, milestone_id: int, user_id: int) -> bool:
    return self.repository.is_project_manager(project_id, milestone_id, user_id)