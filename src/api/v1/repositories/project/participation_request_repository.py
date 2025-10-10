from sqlalchemy.orm import Session
from src.api.v1.schemas.project.participation_request_schema import ParticipationRequestCreate, ParticipationRequestDetail, ParticipationRequestUpdate
from src.api.v1.models.project.participation_request import ParticipationRequest
from fastapi import HTTPException, status
from typing import List
from datetime import datetime
from src.api.v1.services.project.project_service import ProjectService

class ParticipationRequestRepository:
  def __init__(self, db: Session):
    self.db = db
    
  def create(self, project_id: str, obj_in: ParticipationRequestCreate) -> ParticipationRequestDetail:
    """
    새 참여 요청 생성
    """
    try:
      db_participation_request = ParticipationRequest(
        project_id=project_id,
        **obj_in.model_dump(exclude={"project_id"}),
        status="pending"
      )
      
      self.db.add(db_participation_request)
      self.db.commit()
      self.db.refresh(db_participation_request)
      return ParticipationRequestDetail.model_validate(db_participation_request, from_attributes=True)
    except Exception as e:
      self.db.rollback()
      raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))
    
  def get(self, project_id: str, request_id: int) -> ParticipationRequestDetail:
    """
    참여 요청 조회
    """
    try:
      db_participation_request = self.db.query(ParticipationRequest).filter(ParticipationRequest.id == request_id, ParticipationRequest.project_id == project_id).first()
      if not db_participation_request:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Participation request not found")
      return ParticipationRequestDetail.model_validate(db_participation_request, from_attributes=True)
    except Exception as e:
      raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))
    
  def get_by_project(self, project_id: str) -> List[ParticipationRequestDetail]:
    """
    프로젝트의 모든 참여 요청 조회
    """
    try:
      db_participation_requests = self.db.query(ParticipationRequest).filter(ParticipationRequest.project_id == project_id).all()
      return [ParticipationRequestDetail.model_validate(db_participation_request, from_attributes=True) for db_participation_request in db_participation_requests]
    except Exception as e:
      raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))
    
  def get_by_user(self, project_id: str, user_id: int) -> List[ParticipationRequestDetail]:
    """
    사용자의 모든 참여 요청 조회
    """
    try:
      db_participation_requests = self.db.query(ParticipationRequest).filter(ParticipationRequest.project_id == project_id, ParticipationRequest.user_id == user_id).all()
      return [ParticipationRequestDetail.model_validate(db_participation_request, from_attributes=True) for db_participation_request in db_participation_requests]
    except Exception as e:
      raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))
    
  def update(self, project_id: str, request_id: int, obj_in: ParticipationRequestUpdate) -> ParticipationRequestDetail:
    """
    참여 요청 업데이트
    """
    try:
      db_participation_request = self.db.query(ParticipationRequest).filter(ParticipationRequest.id == request_id, ParticipationRequest.project_id == project_id).first()
      if not db_participation_request:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Participation request not found")
      
      db_participation_request.status = obj_in.status
      db_participation_request.processed_at = datetime.now()
      
      self.db.commit()
      self.db.refresh(db_participation_request)
      return ParticipationRequestDetail.model_validate(db_participation_request, from_attributes=True)
    except Exception as e:
      self.db.rollback()
      raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))
    
  def remove(self, project_id: str, request_id: int) -> ParticipationRequestDetail:
    """
    참여 요청 삭제
    """
    try:
      db_participation_request = self.db.query(ParticipationRequest).filter(ParticipationRequest.id == request_id, ParticipationRequest.project_id == project_id).first()
      if not db_participation_request:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Participation request not found")
      
      self.db.delete(db_participation_request)
      self.db.commit()
      return ParticipationRequestDetail.model_validate(db_participation_request, from_attributes=True)
    except Exception as e:
      self.db.rollback()
      raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))
    
  def check_existing_request(self, project_id: str, user_id: int) -> bool:
    """
    참여 요청이 이미 있는지 확인
    """
    try:
      db_participation_request = self.db.query(ParticipationRequest).filter(ParticipationRequest.project_id == project_id, ParticipationRequest.user_id == user_id).first()
      return db_participation_request is not None
    except Exception as e:
      raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))
    
    
  def accept(self, project_id: str, request_id: int) -> ParticipationRequestDetail:
    """
    참여 요청 수락
    """
    try:
      db_participation_request = self.db.query(ParticipationRequest).filter(ParticipationRequest.id == request_id, ParticipationRequest.project_id == project_id).first()
      if not db_participation_request:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Participation request not found")
      
      db_participation_request.status = "accepted"
      db_participation_request.processed_at = datetime.now()
      
      project_service = ProjectService(self.db)
      project_service.add_member(project_id, db_participation_request.user_id)
      
      self.db.commit()
      self.db.refresh(db_participation_request)
      return ParticipationRequestDetail.model_validate(db_participation_request, from_attributes=True)
    except HTTPException as e:
      # Keep transaction clean and propagate client/server error as-is
      self.db.rollback()
      raise e
    except Exception as e:
      self.db.rollback()
      raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))
    