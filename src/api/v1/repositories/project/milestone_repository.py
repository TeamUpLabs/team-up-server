from sqlalchemy.orm import Session
from api.v1.schemas.project.milestone_schema import MilestoneCreate, MilestoneUpdate, MilestoneDetail
from api.v1.schemas.project.task_schema import TaskDetail
from api.v1.schemas.brief import UserBrief
from api.v1.models.project.milestone import Milestone
from api.v1.models.project.project import Project
from api.v1.models.user.user import User
from fastapi import HTTPException
from datetime import datetime
from typing import List

class MilestoneRepository:
  def __init__(self, db: Session):
    self.db = db
    
  def create(self, project_id: str, milestone: MilestoneCreate) -> Milestone:
    """
    새 마일스톤 생성
    """
    
    data = milestone.model_dump(exclude={"assignee_ids"})
    
    project = self.db.query(Project).filter(Project.id == project_id).first()
    if not project:
      raise HTTPException(status_code=404, detail="프로젝트를 찾을 수 없습니다.")
    
    db_obj = Milestone(**data)
    
    if milestone.assignee_ids:
      assignees = self.db.query(User).filter(User.id.in_(milestone.assignee_ids)).all()
      if len(assignees) != len(set(milestone.assignee_ids)):
        raise HTTPException(status_code=404, detail="일부 담당자를 찾을 수 없습니다.")
      db_obj.assignees = assignees
    
    self.db.add(db_obj)
    self.db.commit()
    self.db.refresh(db_obj)
    return db_obj
  
  def update(self, project_id: str, milestone_id: int, obj_in: MilestoneUpdate) -> Milestone:
    """
    마일스톤 정보 업데이트
    관계 검증 및 처리
    """
    milestone = self.db.query(Milestone).filter(Milestone.project_id == project_id, Milestone.id == milestone_id).first()
    if not milestone:
      raise HTTPException(status_code=404, detail="마일스톤을 찾을 수 없습니다.")
    
    update_data = obj_in.model_dump(exclude_unset=True)

    if "assignee_ids" in update_data:
      assignee_ids = update_data.pop("assignee_ids")
      if assignee_ids is not None:
        assignees = self.db.query(User).filter(User.id.in_(assignee_ids)).all()
        if len(assignees) != len(set(assignee_ids)):
          raise HTTPException(status_code=404, detail="일부 담당자를 찾을 수 없습니다.")
        milestone.assignees = assignees
        
    if "status" in update_data:
      if update_data["status"] == "completed" and milestone.status != "completed":
        update_data["completed_at"] = datetime.utcnow()
      elif update_data["status"] != "completed" and milestone.status == "completed":
        update_data["completed_at"] = None

    self.db.query(Milestone).filter(Milestone.project_id == project_id, Milestone.id == milestone_id).update(update_data)
    self.db.commit()
    self.db.refresh(milestone)
    return milestone
  
  def delete(self, project_id: str, id: int) -> Milestone:
    """
    마일스톤 삭제
    관련 업무 검증
    """
    project = self.db.query(Project).filter(Project.id == project_id).first()
    if not project:
      raise HTTPException(status_code=404, detail="프로젝트를 찾을 수 없습니다.")
    
    milestone = self.db.query(Milestone).filter(Milestone.project_id == project_id, Milestone.id == id).first()
    if not milestone:
      raise HTTPException(status_code=404, detail="마일스톤을 찾을 수 없습니다.")
    
    # 연결된 업무가 있는 경우 삭제 방지
    if milestone.tasks:
      raise HTTPException(status_code=400, detail="마일스톤에 연결된 업무가 있어 삭제할 수 없습니다. 먼저 업무의 마일스톤 연결을 해제해주세요.")
    
    self.db.delete(milestone)
    self.db.commit()
    return milestone
  
  def get(self, project_id: str, id: int) -> MilestoneDetail:
    """
    마일스톤 조회
    """
    project = self.db.query(Project).filter(Project.id == project_id).first()
    if not project:
      raise HTTPException(status_code=404, detail="프로젝트를 찾을 수 없습니다.")
    
    milestone = self.db.query(Milestone).filter(Milestone.id == id).first()
    if not milestone:
      raise HTTPException(status_code=404, detail="마일스톤을 찾을 수 없습니다.")
    return MilestoneDetail.model_validate(milestone, from_attributes=True)
  
  def get_by_project(self, project_id: str, skip: int = 0, limit: int = 100) -> List[MilestoneDetail]:
    """
    프로젝트별 마일스톤 목록 조회
    """
    milestones = self.db.query(Milestone).filter(Milestone.project_id == project_id).offset(skip).limit(limit).all()
    return [MilestoneDetail.model_validate(milestone, from_attributes=True) for milestone in milestones]
  
  def get_by_assignee(self, project_id: str, user_id: int, skip: int = 0, limit: int = 100) -> List[MilestoneDetail]:
    """
    마일스톤 담당자 목록 조회
    """
    project = self.db.query(Project).filter(Project.id == project_id).first()
    if not project:
      raise HTTPException(status_code=404, detail="프로젝트를 찾을 수 없습니다.")
    
    user = self.db.query(User).filter(User.id == user_id).first()
    if not user:
      raise HTTPException(status_code=404, detail="사용자를 찾을 수 없습니다.")
    
    return [MilestoneDetail.model_validate(milestone, from_attributes=True) for milestone in user.assigned_milestones[skip:skip+limit]]
  
  def get_tasks(self, project_id: str, milestone_id: int) -> List[TaskDetail]:
    """
    마일스톤에 속한 업무 목록 조회
    """
    project = self.db.query(Project).filter(Project.id == project_id).first()
    if not project:
      raise HTTPException(status_code=404, detail="프로젝트를 찾을 수 없습니다.")
    
    milestone = self.db.query(Milestone).filter(Milestone.id == milestone_id).first()
    if not milestone:
      raise HTTPException(status_code=404, detail="마일스톤을 찾을 수 없습니다.")
    return [TaskDetail.model_validate(task, from_attributes=True) for task in milestone.tasks]
  
  def get_assignees(self, project_id: str, milestone_id: int) -> List[UserBrief]:
    """
    마일스톤 담당자 목록 조회
    """
    project = self.db.query(Project).filter(Project.id == project_id).first()
    if not project:
      raise HTTPException(status_code=404, detail="프로젝트를 찾을 수 없습니다.")
    
    milestone = self.db.query(Milestone).filter(Milestone.id == milestone_id).first()
    if not milestone:
      raise HTTPException(status_code=404, detail="마일스톤을 찾을 수 없습니다.")
    return [UserBrief.model_validate(user, from_attributes=True) for user in milestone.assignees]
  
  def add_assignee(self, project_id: str, milestone_id: int, user_id: int) -> Milestone:
    """
    마일스톤에 담당자 추가
    """
    project = self.db.query(Project).filter(Project.id == project_id).first()
    if not project:
      raise HTTPException(status_code=404, detail="프로젝트를 찾을 수 없습니다.")
    
    milestone = self.db.query(Milestone).filter(Milestone.id == milestone_id).first()
    if not milestone:
      raise HTTPException(status_code=404, detail="마일스톤을 찾을 수 없습니다.")
    
    user = self.db.query(User).filter(User.id == user_id).first()
    if not user:
      raise HTTPException(status_code=404, detail="사용자를 찾을 수 없습니다.")
    
    if user not in milestone.assignees:
      milestone.assignees.append(user)
      self.db.commit()
      self.db.refresh(milestone)
    
    return milestone
  
  def remove_assignee(self, project_id: str, milestone_id: int, user_id: int) -> Milestone:
    """
    마일스톤에서 담당자 제거
    """
    project = self.db.query(Project).filter(Project.id == project_id).first()
    if not project:
      raise HTTPException(status_code=404, detail="프로젝트를 찾을 수 없습니다.")
    
    milestone = self.db.query(Milestone).filter(Milestone.id == milestone_id).first()
    if not milestone:
      raise HTTPException(status_code=404, detail="마일스톤을 찾을 수 없습니다.")
    
    user = self.db.query(User).filter(User.id == user_id).first()
    if not user:
      raise HTTPException(status_code=404, detail="사용자를 찾을 수 없습니다.")
    
    if user in milestone.assignees:
      milestone.assignees.remove(user)
      self.db.commit()
      self.db.refresh(milestone)
    
    return milestone
  
  def is_project_manager(self, project_id: str, milestone_id: int, user_id: int) -> bool:
    """
    사용자가 마일스톤의 프로젝트 관리자인지 확인
    """
    project = self.db.query(Project).filter(Project.id == project_id).first()
    if not project:
      return False
    
    milestone = self.db.query(Milestone).filter(Milestone.id == milestone_id).first()
    if not milestone:
      return False

    if milestone.project.owner_id == user_id:
      return True
    return False
    