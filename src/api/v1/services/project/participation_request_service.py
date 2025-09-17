from typing import List
from sqlalchemy.orm import Session
from api.v1.repositories.project.participation_request_repository import ParticipationRequestRepository
from api.v1.schemas.project.participation_request_schema import ParticipationRequestCreate, ParticipationRequestUpdate, ParticipationRequestDetail

class ParticipationRequestService:
  def __init__(self, db: Session):
    self.repository = ParticipationRequestRepository(db)
    
  def create(self, project_id: str, obj_in: ParticipationRequestCreate) -> ParticipationRequestDetail:
    return self.repository.create(project_id, obj_in)
    
  def get(self, project_id: str, request_id: int) -> ParticipationRequestDetail:
    return self.repository.get(project_id, request_id)
      
  def get_by_project(self, project_id: str) -> List[ParticipationRequestDetail]:
    return self.repository.get_by_project(project_id)
  
  def get_by_user(self, project_id: str, user_id: int) -> List[ParticipationRequestDetail]:
    return self.repository.get_by_user(project_id, user_id)
    
  def update(self, project_id: str, request_id: int, obj_in: ParticipationRequestUpdate) -> ParticipationRequestDetail:
    return self.repository.update(project_id, request_id, obj_in)
    
  def remove(self, project_id: str, request_id: int) -> ParticipationRequestDetail:
    return self.repository.remove(project_id, request_id)
  
  def check_existing_request(self, project_id: str, user_id: int) -> bool:
    return self.repository.check_existing_request(project_id, user_id)