from fastapi import HTTPException
from sqlalchemy.orm import Session
from typing import List, Dict, Any, Optional
from api.v1.models.project.project import Project
from api.v1.schemas.project.project_schema import ProjectDetail, ProjectCreate, ProjectUpdate
from api.v1.repositories.user.user_repository import UserRepository
from api.v1.models.association_tables import project_members
from api.v1.models.user.user import User
from core.utils.format_project_members import format_member_details
from core.utils.calculate_project_stat import calculate_project_stat
from fastapi import status

class ProjectRepository:
  def __init__(self, db: Session):
    self.db = db
    
  def get(self, project_id: str) -> ProjectDetail:
    """
    프로젝트 ID로 프로젝트 조회
    """
    project = self.db.get(Project, project_id)
    
    if not project:
      raise HTTPException(status_code=404, detail="프로젝트를 찾을 수 없습니다.")
    project_dict = project.__dict__.copy()
    
    project_dict["owner"] = UserRepository(self.db).get(project.owner_id)
    
    formatted_members = [
        format_member_details(self.db, project.id, member) 
        for member in project.members
    ]
    project_dict["members"] = formatted_members
    
    project_dict["stats"] = calculate_project_stat(project)
    
    return ProjectDetail.model_validate(project_dict, from_attributes=True)
  
  def get_all_projects(self) -> List[ProjectDetail]:
    """
    모든 프로젝트 조회
    """
    projects = self.db.query(Project).all()
    if not projects:
      raise HTTPException(status_code=404, detail="프로젝트를 찾을 수 없습니다.")
    
    result = []
    for project in projects:
      project_dict = project.__dict__.copy()
      project_dict["owner"] = UserRepository(self.db).get(project.owner_id)
      formatted_members = [
          format_member_details(self.db, project.id, member)
          for member in project.members
      ]
      
      project_dict["members"] = formatted_members
      
      project_dict["stats"] = calculate_project_stat(project)
      
      result.append(ProjectDetail.model_validate(project_dict, from_attributes=True))
    
    return result
  
  def get_by_user_id(self, user_id: int) -> List[ProjectDetail]:
    """
    사용자 ID로 프로젝트 조회
    """
    user = UserRepository(self.db).get(user_id)
    if not user:
      raise HTTPException(status_code=404, detail="사용자를 찾을 수 없습니다.")
    
    projects = self.db.query(Project).filter(Project.members.any(User.id == user_id)).all()
    
    result = []
    for project in projects:
      project_dict = project.__dict__.copy()
      project_dict["owner"] = UserRepository(self.db).get(project.owner_id)
      formatted_members = [
          format_member_details(self.db, project.id, member)
          for member in project.members
      ]
      
      project_dict["members"] = formatted_members
      
      project_dict["stats"] = calculate_project_stat(project)
      
      result.append(ProjectDetail.model_validate(project_dict, from_attributes=True))
    
    return result
  
  def get_all_projects_excluding_my(self, user_id: int) -> List[ProjectDetail]:
    """
    사용자가 속한 프로젝트를 제외한 모든 프로젝트 조회
    """
    user = UserRepository(self.db).get(user_id)
    if not user:
      raise HTTPException(status_code=404, detail="사용자를 찾을 수 없습니다.")
    
    # Get all projects that the user is NOT a member of
    projects = self.db.query(Project).filter(
        Project.members.any(User.id != user_id)
    ).all()
    
    result = []
    for project in projects:
      project_dict = project.__dict__.copy()
      project_dict["owner"] = UserRepository(self.db).get(project.owner_id)
      formatted_members = [
          format_member_details(self.db, project.id, member)
          for member in project.members
      ]
      
      project_dict["members"] = formatted_members
      
      project_dict["stats"] = calculate_project_stat(project)
      
      result.append(ProjectDetail.model_validate(project_dict, from_attributes=True))
    
    return result
  
  def get_all_project_ids(self) -> List[str]:
    """
    모든 프로젝트 ID 조회
    """
    rows = self.db.query(Project.id).all()
    return [str(row[0]) for row in rows]
  
  def create(self, project: ProjectCreate) -> Project:
    """
    새 프로젝트 생성
    사용자, 기술 스택 및 멤버 관계 처리
    """
    # 기본 데이터 준비
    obj_in_data = project.model_dump(exclude={"tech_stack_ids", "member_ids"})
    
    # 소유자 확인
    owner = self.db.query(User).filter(User.id == project.owner_id).first()
    if not owner:
      raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail=f"소유자 ID {project.owner_id}를 찾을 수 없습니다."
      )
    
    # 프로젝트 생성
    db_obj = Project(**obj_in_data)
    
    # 멤버 추가
    if project.member_ids:
      member_ids = set(project.member_ids)
      member_ids.add(project.owner_id)
      
      members = self.db.query(User).filter(User.id.in_(member_ids)).all()
      if len(members) != len(member_ids):
        raise HTTPException(
          status_code=status.HTTP_404_NOT_FOUND,
          detail="일부 사용자를 찾을 수 없습니다."
        )
      db_obj.members = members
    else:
      # 소유자만 멤버로 추가
      db_obj.members = [owner]
    
    self.db.add(db_obj)
    self.db.commit()
    self.db.refresh(db_obj)
    
    # 소유자를 리더로 설정
    self.db.query(project_members).filter(
      project_members.c.project_id == db_obj.id,
      project_members.c.user_id == project.owner_id
    ).update({
      "role": "leader",
      "is_leader": 1,
      "is_manager": 0
    })
    
    self.db.commit()
    self.db.refresh(db_obj)
    # 생성된 프로젝트를 상세 스키마로 반환
    return self.get(db_obj.id)
    
  def update(self, project_id: str, project: ProjectUpdate) -> Project:
    """
    프로젝트 정보 업데이트
    기술 스택 관계 처리
    """
    try:
      db_project = self.db.query(Project).filter(Project.id == project_id).first()
      if not db_project:
        error_msg = f"프로젝트를 찾을 수 없습니다. ID: {project_id}"
        raise HTTPException(status_code=404, detail=error_msg)
      
      update_data = project.model_dump(exclude_unset=True)
      
      try:
        for key, value in update_data.items():
          try:
            setattr(db_project, key, value)
          except Exception as attr_error:
            error_msg = f"Failed to set attribute {key}: {str(attr_error)}"
            raise ValueError(error_msg) from attr_error
        
        self.db.add(db_project)
        self.db.commit()
        self.db.refresh(db_project)
        
        return self.get(project_id)
        
      except HTTPException:
        raise
        
      except Exception as e:
        self.db.rollback()
        error_msg = f"프로젝트 업데이트 중 오류가 발생했습니다: {str(e)}"
        raise HTTPException(
          status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
          detail=error_msg
        )
        
    except HTTPException:
      raise
      
    except Exception as e:
      self.db.rollback()
      error_msg = f"프로젝트 업데이트 처리 중 예상치 못한 오류가 발생했습니다: {str(e)}"
      raise HTTPException(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        detail=error_msg
      )
  
  def delete(self, project_id: str) -> Project:
    """
    프로젝트 삭제
    """
    db_obj = self.db.query(Project).filter(Project.id == project_id).first()
    if not db_obj:
      raise HTTPException(status_code=404, detail="프로젝트를 찾을 수 없습니다.")
    self.db.delete(db_obj)
    self.db.commit()
    return db_obj
  
  def get_project_members(self, project_id: str) -> List[Dict[str, Any]]:
    """
    프로젝트 멤버 정보 조회 (역할, 리더 여부, 관리자 여부, 가입일 포함)
    """
    project = self.db.query(Project).filter(Project.id == project_id).first()
    
    if not project:
      raise HTTPException(status_code=404, detail="프로젝트를 찾을 수 없습니다.")
    
    formatted_members = [
      format_member_details(self.db, project.id, member)
      for member in project.members
    ]
    
    return formatted_members
  
  def add_member(self, project_id: str, user_id: int) -> Project:
    """
    프로젝트에 멤버 추가
    """
    orm_project = self.db.query(Project).filter(Project.id == project_id).first()
    if not orm_project:
      raise HTTPException(status_code=404, detail="프로젝트를 찾을 수 없습니다.")
    
    orm_user = self.db.query(User).filter(User.id == user_id).first()
    if not orm_user:
      raise HTTPException(status_code=404, detail="사용자를 찾을 수 없습니다.")
    
    if orm_user in orm_project.members:
      raise HTTPException(status_code=400, detail="이미 프로젝트의 멤버입니다.")
    
    orm_project.members.append(orm_user)
    self.db.commit()
    self.db.refresh(orm_project)
    return orm_project
  
  def remove_member(self, project_id: str, user_id: int) -> Project:
    """
    프로젝트에서 멤버 제거 및 관련 리소스에서 사용자 제거
    """
    from api.v1.models.project.task import Task
    from api.v1.models.project.milestone import Milestone
    from api.v1.models.project.schedule import Schedule
    from api.v1.models.project.channel import Channel
    
    project = self.get(project_id)
    if not project:
      raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail="프로젝트를 찾을 수 없습니다."
      )
        
    user = UserRepository(self.db).get(user_id)
    if not user:
      raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail="사용자를 찾을 수 없습니다."
      )
        
    if user not in project.members:
      raise HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST,
        detail="프로젝트의 멤버가 아닙니다."
      )
        
    if project.owner_id == user_id:
      raise HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST,
        detail="프로젝트 소유자는 제거할 수 없습니다."
      )
    
    # 1. 프로젝트의 모든 태스크 처리
    tasks = self.db.query(Task).filter(Task.project_id == project_id).all()
    for task in tasks:
      if task.created_by == user_id:
        # 태스크의 소유자인 경우 태스크 삭제
        self.db.delete(task)
      elif user in task.assignees:
        # 담당자에서만 제거
        task.assignees.remove(user)
    
    # 2. 프로젝트의 모든 마일스톤 처리
    milestones = self.db.query(Milestone).filter(Milestone.project_id == project_id).all()
    for milestone in milestones:
      if milestone.created_by == user_id:
        # 마일스톤의 소유자인 경우 마일스톤 삭제
        self.db.delete(milestone)
      elif user in milestone.assignees:
        # 담당자에서만 제거
        milestone.assignees.remove(user)
    
    # 3. 프로젝트의 모든 일정 처리
    schedules = self.db.query(Schedule).filter(Schedule.project_id == project_id).all()
    for schedule in schedules:
      if schedule.created_by == user_id:
        # 일정의 생성자인 경우 일정 삭제
        self.db.delete(schedule)
      else:
        if user in schedule.assignees:
          schedule.assignees.remove(user)
        if schedule.updated_by == user_id:
          schedule.updated_by = None
    
    # 4. 프로젝트의 모든 채널 처리
    channels = self.db.query(Channel).filter(Channel.project_id == project_id).all()
    for channel in channels:
      if channel.created_by == user_id:
        # 채널의 생성자인 경우 채널 삭제
        self.db.delete(channel)
      else:
        if user in channel.members:
          channel.members.remove(user)
        if channel.updated_by == user_id:
          channel.updated_by = None
    
    # 5. 프로젝트 멤버에서 사용자 제거
    project.members.remove(user)
    
    self.db.commit()
    self.db.refresh(project)
    return project
  
  def is_manager(self, project_id: str, user_id: int) -> bool:
    """
    사용자가 프로젝트 관리자인지 확인
    """
    stmt = self.db.query(project_members).filter(
      project_members.c.project_id == project_id,
      project_members.c.user_id == user_id,
      project_members.c.is_leader == 1
    ).first()
    
    return stmt is not None
  
  def update_project_member_permission(self, project_id: str, user_id: int, permission: str) -> Project:
    """
    프로젝트 멤버 권한 수정
    """
    project = self.get(project_id)
    if not project:
      raise HTTPException(status_code=404, detail="프로젝트를 찾을 수 없습니다.")
    member = UserRepository(self.db).get(user_id)
    if not member:
      raise HTTPException(status_code=404, detail="사용자를 찾을 수 없습니다.")
        
    # 사용자가 프로젝트에 속해 있는지 확인
    if member not in project.members:
      raise HTTPException(status_code=400, detail="이 사용자는 프로젝트의 멤버가 아닙니다.")
        
    # 권한 설정에 따른 값 변경
    role = "member"
    is_leader = 0
    is_manager = 0
    
    if permission == "leader":
      role = "leader"
      is_leader = 1
    elif permission == "manager":
      role = "manager"
      is_manager = 1
    # "member"인 경우 둘 다 0으로 유지
    
    # 프로젝트-멤버 관계 테이블 업데이트
    self.db.query(project_members).filter(
      project_members.c.project_id == project_id,
      project_members.c.user_id == user_id
    ).update({
      "role": role,
      "is_leader": is_leader,
      "is_manager": is_manager
    })
        
    self.db.commit()
    self.db.refresh(project)
    return project