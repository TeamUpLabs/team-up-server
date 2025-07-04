from typing import List, Optional, Dict, Any
from datetime import datetime
from sqlalchemy.orm import Session
from fastapi import HTTPException, status
from new_models.milestone import Milestone
from new_models.project import Project
from new_models.user import User
from new_schemas.milestone import MilestoneCreate, MilestoneUpdate
from new_crud.base import CRUDBase

class CRUDMilestone(CRUDBase[Milestone, MilestoneCreate, MilestoneUpdate]):
    """마일스톤 모델에 대한 CRUD 작업"""
    
    def create(self, db: Session, *, obj_in: MilestoneCreate) -> Milestone:
        """
        새 마일스톤 생성
        관계 검증 및 처리
        """
        # 기본 데이터 준비
        obj_in_data = obj_in.model_dump(exclude={"assignee_ids"})
        
        # 프로젝트 존재 확인
        project = db.query(Project).filter(Project.id == obj_in.project_id).first()
        if not project:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"프로젝트 ID {obj_in.project_id}를 찾을 수 없습니다."
            )
        
        # 마일스톤 생성
        db_obj = Milestone(**obj_in_data)
        
        # 담당자 추가
        if obj_in.assignee_ids:
            assignees = db.query(User).filter(User.id.in_(obj_in.assignee_ids)).all()
            if len(assignees) != len(set(obj_in.assignee_ids)):
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="일부 담당자를 찾을 수 없습니다."
                )
            db_obj.assignees = assignees
        
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj
    
    def update(self, db: Session, *, db_obj: Milestone, obj_in: MilestoneUpdate) -> Milestone:
        """
        마일스톤 정보 업데이트
        관계 검증 및 처리
        """
        update_data = obj_in.model_dump(exclude_unset=True)
        
        # 담당자 업데이트
        if "assignee_ids" in update_data:
            assignee_ids = update_data.pop("assignee_ids")
            if assignee_ids is not None:
                assignees = db.query(User).filter(User.id.in_(assignee_ids)).all()
                if len(assignees) != len(set(assignee_ids)):
                    raise HTTPException(
                        status_code=status.HTTP_404_NOT_FOUND,
                        detail="일부 담당자를 찾을 수 없습니다."
                    )
                db_obj.assignees = assignees
        
        # 상태 변경 시 완료 일자 업데이트
        if "status" in update_data:
            if update_data["status"] == "completed" and db_obj.status != "completed":
                update_data["completed_at"] = datetime.utcnow()
            elif update_data["status"] != "completed" and db_obj.status == "completed":
                update_data["completed_at"] = None
        
        # 업데이트 수행
        updated_obj = super().update(db, db_obj=db_obj, obj_in=update_data)
        return updated_obj
    
    def get_by_project(self, db: Session, *, project_id: str, skip: int = 0, limit: int = 100) -> List[Milestone]:
        """프로젝트별 마일스톤 목록 조회"""
        return db.query(Milestone).filter(Milestone.project_id == project_id).offset(skip).limit(limit).all()
    
    def get_by_assignee(self, db: Session, *, user_id: int, skip: int = 0, limit: int = 100) -> List[Milestone]:
        """담당자별 마일스톤 목록 조회"""
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"사용자 ID {user_id}를 찾을 수 없습니다."
            )
        return user.assigned_milestones[skip:skip+limit]
    
    def get_multi_filtered(self, db: Session, *, skip: int = 0, limit: int = 100, 
                          project_id: Optional[str] = None, status: Optional[str] = None, 
                          priority: Optional[str] = None) -> List[Milestone]:
        """필터링된 마일스톤 목록 조회"""
        query = db.query(Milestone)
        
        if project_id:
            query = query.filter(Milestone.project_id == project_id)
        if status:
            query = query.filter(Milestone.status == status)
        if priority:
            query = query.filter(Milestone.priority == priority)
            
        return query.offset(skip).limit(limit).all()
    
    def get_tasks(self, db: Session, *, milestone_id: int) -> List:
        """마일스톤에 속한 업무 목록 조회"""
        milestone = self.get(db, id=milestone_id)
        if not milestone:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"마일스톤 ID {milestone_id}를 찾을 수 없습니다."
            )
        return milestone.tasks
    
    def get_assignees(self, db: Session, *, milestone_id: int) -> List:
        """마일스톤 담당자 목록 조회"""
        milestone = self.get(db, id=milestone_id)
        if not milestone:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"마일스톤 ID {milestone_id}를 찾을 수 없습니다."
            )
        return milestone.assignees
    
    def add_assignee(self, db: Session, *, milestone_id: int, user_id: int) -> Milestone:
        """마일스톤에 담당자 추가"""
        milestone = self.get(db, id=milestone_id)
        if not milestone:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"마일스톤 ID {milestone_id}를 찾을 수 없습니다."
            )
        
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"사용자 ID {user_id}를 찾을 수 없습니다."
            )
        
        if user not in milestone.assignees:
            milestone.assignees.append(user)
            db.commit()
            db.refresh(milestone)
        
        return milestone
    
    def remove_assignee(self, db: Session, *, milestone_id: int, user_id: int) -> Milestone:
        """마일스톤에서 담당자 제거"""
        milestone = self.get(db, id=milestone_id)
        if not milestone:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"마일스톤 ID {milestone_id}를 찾을 수 없습니다."
            )
        
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"사용자 ID {user_id}를 찾을 수 없습니다."
            )
        
        if user in milestone.assignees:
            milestone.assignees.remove(user)
            db.commit()
            db.refresh(milestone)
        
        return milestone
    
    def is_project_manager(self, db: Session, *, milestone_id: int, user_id: int) -> bool:
        """사용자가 마일스톤의 프로젝트 관리자인지 확인"""
        milestone = self.get(db, id=milestone_id)
        if not milestone:
            return False
        
        # 프로젝트 소유자 확인
        if milestone.project.owner_id == user_id:
            return True
        
        # 프로젝트 관리자 확인 (TODO: 프로젝트 멤버 관리자 권한 확인 로직 추가)
        return False
    
    def remove(self, db: Session, *, id: int) -> Milestone:
        """
        마일스톤 삭제
        관련 업무 검증
        """
        milestone = self.get(db, id=id)
        if not milestone:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"마일스톤 ID {id}를 찾을 수 없습니다."
            )
        
        # 연결된 업무가 있는 경우 삭제 방지
        if milestone.tasks:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"마일스톤에 연결된 업무가 있어 삭제할 수 없습니다. 먼저 업무의 마일스톤 연결을 해제해주세요."
            )
        
        db.delete(milestone)
        db.commit()
        return milestone

# CRUDMilestone 클래스 인스턴스 생성
milestone = CRUDMilestone(Milestone) 