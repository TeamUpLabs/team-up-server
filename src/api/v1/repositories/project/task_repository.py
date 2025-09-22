from sqlalchemy.orm import Session
from fastapi import HTTPException
from api.v1.models.project.task import Task, SubTask, Comment
from api.v1.models.user.user import User
from api.v1.models.project.project import Project
from api.v1.models.project.milestone import Milestone
from api.v1.schemas.project.task_schema import CommentCreate, CommentUpdate, TaskDetail, TaskCreate, TaskUpdate
from typing import List
from datetime import datetime

class TaskRepository:
  def __init__(self, db: Session):
    self.db = db
    
  def get(self, project_id: str, task_id: int) -> TaskDetail:
    """
    프로젝트별 업무 조회
    """
    task = self.db.query(Task).filter(Task.project_id == project_id, Task.id == task_id).first()
    if not task:
      raise HTTPException(status_code=404, detail="할 일을 찾을 수 없습니다.")
    return TaskDetail.model_validate(task, from_attributes=True)
  
  def get_all_tasks_by_project_id(self, project_id: str) -> List[TaskDetail]:
    """
    프로젝트별 업무 목록 조회
    """
    tasks = self.db.query(Task).filter(Task.project_id == project_id).all()
    return [TaskDetail.model_validate(task, from_attributes=True) for task in tasks]
  
  def get_all_tasks_by_milestone_id(self, project_id: str, milestone_id: int) -> List[TaskDetail]:
    """
    마일스톤별 업무 목록 조회
    """
    tasks = self.db.query(Task).filter(Task.project_id == project_id, Task.milestone_id == milestone_id).all()
    return [TaskDetail.model_validate(task, from_attributes=True) for task in tasks]
  
  def get_all_tasks_by_assignee_id(self, project_id: str, assignee_id: int) -> List[TaskDetail]:
    """
    담당자별 업무 목록 조회
    """
    tasks = (
        self.db.query(Task)
        .join(Task.assignees)
        .filter(Task.project_id == project_id, User.id == assignee_id)
        .all()
    )
    return [TaskDetail.model_validate(task, from_attributes=True) for task in tasks]
    
  def create(self, project_id: str, task: TaskCreate) -> Task:
    """
    새 업무 생성
    관계 검증 및 처리
    """
    data = task.model_dump(exclude={"assignee_ids", "subtasks"})
    
    project = self.db.query(Project).filter(Project.id == project_id).first()
    if not project:
      raise HTTPException(status_code=404, detail="프로젝트를 찾을 수 없습니다.")
    
    if task.milestone_id:
      milestone = self.db.query(Milestone).filter(Milestone.id == task.milestone_id).first()
      if not milestone:
        raise HTTPException(status_code=404, detail="마일스톤을 찾을 수 없습니다.")
      if milestone.project_id != project_id:
        raise HTTPException(status_code=400, detail="마일스톤이 지정된 프로젝트에 속하지 않습니다.")
    
    db_obj = Task(**data)
    
    if task.assignee_ids:
      assignees = self.db.query(User).filter(User.id.in_(task.assignee_ids)).all()
      if len(assignees) != len(set(task.assignee_ids)):
        raise HTTPException(status_code=404, detail="일부 담당자를 찾을 수 없습니다.")
      db_obj.assignees = assignees
    
    self.db.add(db_obj)
    self.db.flush()
    
    if task.subtasks:
      for subtask_data in task.subtasks:
        subtask = SubTask(
          title=subtask_data.title,
          is_completed=subtask_data.is_completed,
          task_id=db_obj.id,
          created_at=datetime.utcnow(),
          updated_at=datetime.utcnow()
        )
        self.db.add(subtask)
    
    self.db.commit()
    self.db.refresh(db_obj)
    
    # 마일스톤의 진행도 업데이트
    if db_obj.milestone_id:
      self._update_milestone_progress(self.db, milestone_id=db_obj.milestone_id)
    
    return db_obj
    
  
  def update(self, project_id: str, task_id: int, task: TaskUpdate) -> Task:
    """
    업무 정보 업데이트
    관계 검증 및 처리
    """
    update_data = task.model_dump(exclude_unset=True)
    
    # Get the current task first to check the old milestone
    db_task = self.db.query(Task).filter(Task.project_id == project_id, Task.id == task_id).first()
    if not db_task:
      raise HTTPException(status_code=404, detail="할 일을 찾을 수 없습니다.")
      
    old_milestone_id = db_task.milestone_id
    
    if "milestone_id" in update_data and update_data["milestone_id"] is not None:
      milestone = self.db.query(Milestone).filter(Milestone.id == update_data["milestone_id"]).first()
      if not milestone:
        raise HTTPException(status_code=404, detail="마일스톤을 찾을 수 없습니다.")
      if milestone.project_id != project_id:
        raise HTTPException(status_code=400, detail="마일스톤이 업무의 프로젝트에 속하지 않습니다.")
      
    # 담당자 업데이트
    if "assignee_ids" in update_data:
      assignee_ids = update_data.pop("assignee_ids")
      if assignee_ids is not None:
        assignees = self.db.query(User).filter(User.id.in_(assignee_ids)).all()
        if len(assignees) != len(set(assignee_ids)):
          raise HTTPException(status_code=404, detail="일부 담당자를 찾을 수 없습니다.")
        # Clear existing assignees and add new ones
        db_task.assignees.clear()
        db_task.assignees.extend(assignees)
        
    if "status" in update_data:
      if update_data["status"] == "completed" and db_task.status != "completed":
        update_data["completed_at"] = datetime.utcnow()
      elif update_data["status"] != "completed" and db_task.status == "completed":
        update_data["completed_at"] = None
    
    for key, value in update_data.items():
      setattr(db_task, key, value)
    
    self.db.add(db_task)
    self.db.commit()
    self.db.refresh(db_task)
    
    # Update milestone progress
    if old_milestone_id:
        self._update_milestone_progress(self.db, milestone_id=old_milestone_id)
    if db_task.milestone_id and db_task.milestone_id != old_milestone_id:
        self._update_milestone_progress(self.db, milestone_id=db_task.milestone_id)
    
    return db_task
  
  def delete(self, project_id: str, task_id: int) -> Task:
    """
    업무 삭제
    """
    task = self.db.query(Task).filter(Task.project_id == project_id, Task.id == task_id).first()
    if not task:
      raise HTTPException(status_code=404, detail="할 일을 찾을 수 없습니다.")
    self.db.delete(task)
    self.db.commit()
    return task
  
  def _update_milestone_progress(self, db: Session, *, milestone_id: int) -> None:
    """
    마일스톤의 진행도를 업데이트
    """
    milestone = db.query(Milestone).filter(Milestone.id == milestone_id).first()
    if not milestone:
      return
    
    # Get all tasks for this milestone
    tasks = db.query(Task).filter(Task.milestone_id == milestone_id).all()
    if not tasks:
      milestone.progress = 0
      db.add(milestone)
      db.commit()
      return
    
    total_tasks = len(tasks)
    completed_tasks = sum(1 for task in tasks if task.status == "completed")
    
    milestone.progress = int((completed_tasks / total_tasks) * 100) if total_tasks > 0 else 0
    db.add(milestone)
    db.commit()
    
  
  def add_assignee(self, project_id: str, task_id: int, user_id: int) -> Task:
    """
    업무에 담당자 추가
    """
    task = self.db.query(Task).filter(Task.project_id == project_id, Task.id == task_id).first()
    if not task:
      raise HTTPException(status_code=404, detail="할 일을 찾을 수 없습니다.")
    user = self.db.query(User).filter(User.id == user_id).first()
    if not user:
      raise HTTPException(status_code=404, detail="사용자를 찾을 수 없습니다.")
    
    if user not in task.assignees:
      task.assignees.append(user)
      self.db.add(task)
      self.db.commit()
      self.db.refresh(task)
    return task
  
  def remove_assignee(self, project_id: str, task_id: int, user_id: int) -> Task:
    """
    업무에서 담당자 제거
    """
    task = self.db.query(Task).filter(Task.project_id == project_id, Task.id == task_id).first()
    if not task:
      raise HTTPException(status_code=404, detail="할 일을 찾을 수 없습니다.")
    user = self.db.query(User).filter(User.id == user_id).first()
    if not user:
      raise HTTPException(status_code=404, detail="사용자를 찾을 수 없습니다.")
    
    if user in task.assignees:
      task.assignees.remove(user)
      self.db.add(task)
      self.db.commit()
      self.db.refresh(task)
    return task
    
  def is_manager(self, project_id: str, task_id: int, user_id: int) -> bool:
    """
    업무의 프로젝트 관리자인지 확인
    """
    task = self.db.query(Task).filter(Task.project_id == project_id, Task.id == task_id).first()
    if not task:
      raise HTTPException(status_code=404, detail="할 일을 찾을 수 없습니다.")
    return self.is_project_manager(self.db, task_id=task_id, user_id=user_id)
  
  def get_comments(self, project_id: str, task_id: int, skip: int = 0, limit: int = 100) -> List[Comment]:
    """업무의 댓글 목록 조회"""
    task = self.db.query(Task).filter(Task.project_id == project_id, Task.id == task_id).first()
    if not task:
      raise HTTPException(status_code=404, detail="할 일을 찾을 수 없습니다.")
    
    return self.db.query(Comment).filter(Comment.task_id == task_id).offset(skip).limit(limit).all()
  
  def create_comment(self, project_id: str, task_id: int, comment: CommentCreate) -> Comment:
    """댓글 생성"""
    task = self.db.query(Task).filter(Task.project_id == project_id, Task.id == task_id).first()
    if not task:
      raise HTTPException(status_code=404, detail="할 일을 찾을 수 없습니다.")
    
    comment = Comment(
      content=comment.content,
      task_id=task_id,
      created_by=comment.created_by,
      created_at=datetime.utcnow(),
      updated_at=datetime.utcnow()
    )
    self.db.add(comment)
    self.db.commit()
    self.db.refresh(comment)
    return comment
  
  def update_comment(self, project_id: str, task_id: int, comment_id: int, comment: CommentUpdate) -> Comment:
    """댓글 수정"""
    task = self.db.query(Task).filter(Task.project_id == project_id, Task.id == task_id).first()
    if not task:
      raise HTTPException(status_code=404, detail="할 일을 찾을 수 없습니다.")
    
    comment = self.db.query(Comment).filter(Comment.task_id == task_id, Comment.id == comment_id).first()
    if not comment:
      raise HTTPException(status_code=404, detail="댓글을 찾을 수 없습니다.")
    comment.content = comment.content
    self.db.add(comment)
    self.db.commit()
    self.db.refresh(comment)
    return comment
  
  def delete_comment(self, project_id: str, task_id: int, comment_id: int) -> bool:
    """댓글 삭제"""
    task = self.db.query(Task).filter(Task.project_id == project_id, Task.id == task_id).first()
    if not task:
      raise HTTPException(status_code=404, detail="할 일을 찾을 수 없습니다.")
    
    comment = self.db.query(Comment).filter(Comment.task_id == task_id, Comment.id == comment_id).first()
    if not comment:
      raise HTTPException(status_code=404, detail="댓글을 찾을 수 없습니다.")
    
    self.db.delete(comment)
    self.db.commit()
    return True