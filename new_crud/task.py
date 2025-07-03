from typing import List, Optional, Dict, Any
from datetime import datetime
from sqlalchemy.orm import Session
from fastapi import HTTPException, status
from new_models.task import Task
from new_models.project import Project
from new_models.milestone import Milestone
from new_models.user import User
from new_schemas.task import TaskCreate, TaskUpdate
from new_crud.base import CRUDBase

class CRUDTask(CRUDBase[Task, TaskCreate, TaskUpdate]):
    """업무 모델에 대한 CRUD 작업"""
    
    def create(self, db: Session, *, obj_in: TaskCreate) -> Task:
        """
        새 업무 생성
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
        
        # 마일스톤 검증
        if obj_in.milestone_id:
            milestone = db.query(Milestone).filter(Milestone.id == obj_in.milestone_id).first()
            if not milestone:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"마일스톤 ID {obj_in.milestone_id}를 찾을 수 없습니다."
                )
            # 마일스톤이 동일한 프로젝트에 속하는지 확인
            if milestone.project_id != obj_in.project_id:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="마일스톤이 지정된 프로젝트에 속하지 않습니다."
                )
        
        # 부모 업무 검증
        if obj_in.parent_task_id:
            parent_task = db.query(Task).filter(Task.id == obj_in.parent_task_id).first()
            if not parent_task:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"부모 업무 ID {obj_in.parent_task_id}를 찾을 수 없습니다."
                )
            # 부모 업무가 동일한 프로젝트에 속하는지 확인
            if parent_task.project_id != obj_in.project_id:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="부모 업무가 지정된 프로젝트에 속하지 않습니다."
                )
        
        # 업무 생성
        db_obj = Task(**obj_in_data)
        
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
        
        # 마일스톤의 진행도 업데이트
        if db_obj.milestone_id:
            self._update_milestone_progress(db, milestone_id=db_obj.milestone_id)
        
        return db_obj
    
    def update(self, db: Session, *, db_obj: Task, obj_in: TaskUpdate) -> Task:
        """
        업무 정보 업데이트
        관계 검증 및 처리
        """
        update_data = obj_in.model_dump(exclude_unset=True)
        old_milestone_id = db_obj.milestone_id
        
        # 마일스톤 검증
        if "milestone_id" in update_data and update_data["milestone_id"] is not None:
            milestone = db.query(Milestone).filter(Milestone.id == update_data["milestone_id"]).first()
            if not milestone:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"마일스톤 ID {update_data['milestone_id']}를 찾을 수 없습니다."
                )
            # 마일스톤이 동일한 프로젝트에 속하는지 확인
            if milestone.project_id != db_obj.project_id:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="마일스톤이 업무의 프로젝트에 속하지 않습니다."
                )
        
        # 부모 업무 검증
        if "parent_task_id" in update_data and update_data["parent_task_id"] is not None:
            if update_data["parent_task_id"] == db_obj.id:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="업무는 자기 자신을 부모로 가질 수 없습니다."
                )
                
            parent_task = db.query(Task).filter(Task.id == update_data["parent_task_id"]).first()
            if not parent_task:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"부모 업무 ID {update_data['parent_task_id']}를 찾을 수 없습니다."
                )
            # 부모 업무가 동일한 프로젝트에 속하는지 확인
            if parent_task.project_id != db_obj.project_id:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="부모 업무가 업무의 프로젝트에 속하지 않습니다."
                )
        
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
        
        # 마일스톤 진행도 업데이트
        if old_milestone_id:
            self._update_milestone_progress(db, milestone_id=old_milestone_id)
        if updated_obj.milestone_id and updated_obj.milestone_id != old_milestone_id:
            self._update_milestone_progress(db, milestone_id=updated_obj.milestone_id)
        
        return updated_obj
    
    def _update_milestone_progress(self, db: Session, *, milestone_id: int) -> None:
        """마일스톤의 진행도를 업데이트"""
        milestone = db.query(Milestone).filter(Milestone.id == milestone_id).first()
        if not milestone or not milestone.tasks:
            return
            
        total_tasks = len(milestone.tasks)
        completed_tasks = sum(1 for task in milestone.tasks if task.status == "completed")
        
        milestone.progress = int((completed_tasks / total_tasks) * 100) if total_tasks > 0 else 0
        db.add(milestone)
        db.commit()
    
    def get_by_project(self, db: Session, *, project_id: str, skip: int = 0, limit: int = 100) -> List[Task]:
        """프로젝트별 업무 목록 조회"""
        return db.query(Task).filter(Task.project_id == project_id).offset(skip).limit(limit).all()
    
    def get_by_milestone(self, db: Session, *, milestone_id: int, skip: int = 0, limit: int = 100) -> List[Task]:
        """마일스톤별 업무 목록 조회"""
        return db.query(Task).filter(Task.milestone_id == milestone_id).offset(skip).limit(limit).all()
    
    def get_by_assignee(self, db: Session, *, user_id: int, skip: int = 0, limit: int = 100) -> List[Task]:
        """담당자별 업무 목록 조회"""
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"사용자 ID {user_id}를 찾을 수 없습니다."
            )
        return user.assigned_tasks[skip:skip+limit]

# CRUDTask 클래스 인스턴스 생성
task = CRUDTask(Task) 