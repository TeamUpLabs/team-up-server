from sqlalchemy.orm import Session
from api.v1.schemas.project.schedule_schema import ScheduleCreate, ScheduleUpdate, ScheduleDetail
from api.v1.models.project.schedule import Schedule
from api.v1.models.association_tables import project_members
from api.v1.models.project import Project
from api.v1.models.user import User
from fastapi import HTTPException, status
from typing import List

class ScheduleRepository:
  def __init__(self, db: Session):
    self.db = db
  
  def create(self, project_id: str, obj_in: ScheduleCreate) -> ScheduleDetail:
    """
    새 스케줄 생성
    """
    try:
      schedule_data_for_db = obj_in.model_dump(exclude={"assignee_ids"})
      schedule_data_for_db["project_id"] = project_id
      db_schedule = Schedule(**schedule_data_for_db)
      self.db.add(db_schedule)
      self.db.flush()
      
      if obj_in.assignee_ids:
        for user_id in obj_in.assignee_ids:
          user = self.db.query(User).filter(User.id == user_id).first()
          if user:
            db_schedule.assignees.append(user)
      
      self.db.commit()
      self.db.refresh(db_schedule)
      return ScheduleDetail.model_validate(db_schedule, from_attributes=True)
    except Exception as e:
      self.db.rollback()
      raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))
  
  def get_by_project(self, project_id: str) -> List[ScheduleDetail]:
    """
    프로젝트의 모든 스케줄 조회
    """
    schedules = self.db.query(Schedule).filter(Schedule.project_id == project_id).all()
    return [ScheduleDetail.model_validate(schedule, from_attributes=True) for schedule in schedules]
  
  
  def get_by_assignee(self, project_id: str, user_id: int) -> List[ScheduleDetail]:
    """
    할당된 스케줄 조회
    """
    schedules = self.db.query(Schedule).join(Schedule.assignees).filter(User.id == user_id, Schedule.project_id == project_id).all()
    return [ScheduleDetail.model_validate(schedule, from_attributes=True) for schedule in schedules]
  
  def get_by_id(self, project_id: str, schedule_id: int) -> ScheduleDetail:
    """
    스케줄 ID로 조회
    """
    schedule = self.db.query(Schedule).filter(Schedule.id == schedule_id, Schedule.project_id == project_id).first()
    return ScheduleDetail.model_validate(schedule, from_attributes=True)
  
  def update(self, project_id: str, schedule_id: int, obj_in: ScheduleUpdate) -> ScheduleDetail:
    """
    스케줄 업데이트
    """
    try: 
      obj = self.db.query(Schedule).filter(Schedule.id == schedule_id, Schedule.project_id == project_id).first()
      if not obj:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Schedule not found")
      
      obj_data = obj.__dict__
      update_data = obj_in.model_dump(exclude_unset=True, exclude={"assignee_ids"})
      
      for field in obj_data:
        if field in update_data:
          setattr(obj, field, update_data[field])
      
      if hasattr(obj_in, "assignee_ids") and obj_in.assignee_ids is not None:
        obj.assignees = []
        for user_id in obj_in.assignee_ids:
          user = self.db.query(User).filter(User.id == user_id).first()
          if user:
            obj.assignees.append(user)
      
      self.db.add(obj)
      self.db.commit()
      self.db.refresh(obj)
      return ScheduleDetail.model_validate(obj, from_attributes=True)
    except Exception as e:
      self.db.rollback()
      raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))
  
  def remove(self, project_id: str, schedule_id: int) -> ScheduleDetail:
    """
    스케줄 삭제
    """
    try:
      obj = self.db.query(Schedule).filter(Schedule.id == schedule_id, Schedule.project_id == project_id).first()
      self.db.delete(obj)
      self.db.commit()
      return ScheduleDetail.model_validate(obj, from_attributes=True)
    except Exception as e:
      self.db.rollback()
      raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))
  
  def is_project_manager(self, project_id: str, user_id: int) -> bool:
    """
    사용자가 해당 프로젝트의 관리자인지 확인
    """
    project = self.db.query(Project).filter(Project.id == project_id).first()
    if not project:
      return False
    
    # 프로젝트 멤버 테이블에서 관리자 권한 확인
    member = self.db.query(project_members).filter(
      project_members.c.project_id == project_id,
      project_members.c.user_id == user_id
    ).first()
    
    return member and (member.is_manager or member.is_leader)