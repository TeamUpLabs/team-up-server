from typing import List, Optional, Dict, Any
from datetime import datetime
from sqlalchemy.orm import Session
from fastapi import HTTPException, status
from new_models.task import Task, SubTask, Comment
from new_models.project import Project
from new_models.milestone import Milestone
from new_models.user import User
from new_schemas.task import TaskCreate, TaskUpdate, SubTaskCreate
from new_crud.base import CRUDBase

class CRUDTask(CRUDBase[Task, TaskCreate, TaskUpdate]):
    """업무 모델에 대한 CRUD 작업"""
    
    def create(self, db: Session, *, obj_in: TaskCreate) -> Task:
        """
        새 업무 생성
        관계 검증 및 처리
        """
        # 기본 데이터 준비
        obj_in_data = obj_in.model_dump(exclude={"assignee_ids", "subtasks"})
        
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
        db.flush()  # ID를 생성하기 위해 flush
        
        # 하위 업무 추가
        if obj_in.subtasks:
            for subtask_data in obj_in.subtasks:
                subtask = SubTask(
                    title=subtask_data.title,
                    is_completed=subtask_data.is_completed,
                    task_id=db_obj.id,
                    created_at=datetime.utcnow(),
                    updated_at=datetime.utcnow()
                )
                db.add(subtask)
        
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
    
    def get_assignees(self, db: Session, *, task_id: int) -> List[User]:
        """업무 담당자 목록 조회"""
        task = db.query(Task).filter(Task.id == task_id).first()
        if not task:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"업무 ID {task_id}를 찾을 수 없습니다."
            )
        return task.assignees
    
    def add_assignee(self, db: Session, *, task_id: int, user_id: int) -> Task:
        """업무에 담당자 추가"""
        task = db.query(Task).filter(Task.id == task_id).first()
        if not task:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"업무 ID {task_id}를 찾을 수 없습니다."
            )
        
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"사용자 ID {user_id}를 찾을 수 없습니다."
            )
        
        if user not in task.assignees:
            task.assignees.append(user)
            db.add(task)
            db.commit()
            db.refresh(task)
        
        return task
    
    def remove_assignee(self, db: Session, *, task_id: int, user_id: int) -> Task:
        """업무에서 담당자 제거"""
        task = db.query(Task).filter(Task.id == task_id).first()
        if not task:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"업무 ID {task_id}를 찾을 수 없습니다."
            )
        
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"사용자 ID {user_id}를 찾을 수 없습니다."
            )
        
        if user in task.assignees:
            task.assignees.remove(user)
            db.add(task)
            db.commit()
            db.refresh(task)
        
        return task
    
    def is_project_manager(self, db: Session, *, task_id: int, user_id: int) -> bool:
        """사용자가 해당 업무의 프로젝트 관리자인지 확인"""
        task = db.query(Task).filter(Task.id == task_id).first()
        if not task:
            return False
        
        # 프로젝트 멤버 테이블에서 관리자 권한 확인
        from new_models.association_tables import project_members
        member = db.query(project_members).filter(
            project_members.c.project_id == task.project_id,
            project_members.c.user_id == user_id
        ).first()
        
        return member and (member.is_manager or member.is_leader)
    
    def get_multi_filtered(self, db: Session, *, skip: int = 0, limit: int = 100, 
                          project_id: Optional[str] = None, milestone_id: Optional[int] = None,
                          status: Optional[str] = None, priority: Optional[str] = None) -> List[Task]:
        """필터링된 업무 목록 조회"""
        query = db.query(Task)
        
        if project_id:
            query = query.filter(Task.project_id == project_id)
        if milestone_id:
            query = query.filter(Task.milestone_id == milestone_id)
        if status:
            query = query.filter(Task.status == status)
        if priority:
            query = query.filter(Task.priority == priority)
        
        return query.offset(skip).limit(limit).all()
    
    def get_comments(self, db: Session, *, task_id: int, skip: int = 0, limit: int = 100) -> List[Comment]:
        """업무의 댓글 목록 조회"""
        return db.query(Comment).filter(Comment.task_id == task_id).offset(skip).limit(limit).all()
    
    def create_comment(self, db: Session, *, task_id: int, content: str, created_by: int) -> Comment:
        """댓글 생성"""
        comment = Comment(
            content=content,
            task_id=task_id,
            created_by=created_by,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        db.add(comment)
        db.commit()
        db.refresh(comment)
        return comment
    
    def update_comment(self, db: Session, *, comment_id: int, content: str) -> Comment:
        """댓글 수정"""
        comment = db.query(Comment).filter(Comment.id == comment_id).first()
        if not comment:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"댓글 ID {comment_id}를 찾을 수 없습니다."
            )
        
        comment.content = content
        comment.updated_at = datetime.utcnow()
        db.add(comment)
        db.commit()
        db.refresh(comment)
        return comment
    
    def delete_comment(self, db: Session, *, comment_id: int) -> bool:
        """댓글 삭제"""
        comment = db.query(Comment).filter(Comment.id == comment_id).first()
        if not comment:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"댓글 ID {comment_id}를 찾을 수 없습니다."
            )
        
        db.delete(comment)
        db.commit()
        return True

# CRUDTask 클래스 인스턴스 생성
task = CRUDTask(Task) 