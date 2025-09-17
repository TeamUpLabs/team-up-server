from sqlalchemy.orm import Session
from api.v1.repositories.project.schedule_repository import ScheduleRepository
from api.v1.schemas.project.schedule_schema import ScheduleCreate, ScheduleUpdate, ScheduleDetail
from typing import List

class ScheduleService:
  def __init__(self, db: Session):
    self.repository = ScheduleRepository(db)
    
  def create(self, project_id: str, obj_in: ScheduleCreate) -> ScheduleDetail:
    return self.repository.create(project_id, obj_in)
    
  def get_by_project(self, project_id: str) -> List[ScheduleDetail]:
    return self.repository.get_by_project(project_id)
    
  def get_by_assignee(self, project_id: str, user_id: int) -> List[ScheduleDetail]:
    return self.repository.get_by_assignee(project_id, user_id)
    
  def get_by_id(self, project_id: str, schedule_id: int) -> ScheduleDetail:
    return self.repository.get_by_id(project_id, schedule_id)
    
  def update(self, project_id: str, schedule_id: int, obj_in: ScheduleUpdate) -> ScheduleDetail:
    return self.repository.update(project_id, schedule_id, obj_in)
    
  def remove(self, project_id: str, schedule_id: int) -> ScheduleDetail:
    return self.repository.remove(project_id, schedule_id)
  
  def is_project_manager(self, project_id: str, user_id: int) -> bool:
    return self.repository.is_project_manager(project_id, user_id)