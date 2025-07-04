from fastapi import APIRouter, Depends, HTTPException, status
from typing import List, Optional
from sqlalchemy.orm import Session
from datetime import datetime

from database import get_db
from auth import get_current_user
from new_crud import task, project
from new_schemas.task import TaskCreate, TaskUpdate, TaskBrief, TaskDetail, SubTaskCreate, SubTaskUpdate, SubTaskDetail, CommentCreate, CommentUpdate, CommentDetail
from new_models.user import User
from new_models.task import SubTask, Comment
from new_routers.project_router import convert_project_to_project_detail
from utils.sse_manager import project_sse_manager
import json

router = APIRouter(
    prefix="/api/tasks",
    tags=["tasks"]
)

@router.post("/", response_model=TaskDetail, status_code=status.HTTP_201_CREATED)
async def create_task(task_in: TaskCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """새 업무 생성"""
    # 생성자 ID 설정
    task_in.created_by = current_user.id
    db_task = task.create(db=db, obj_in=task_in)
    if db_task:
        project_data = convert_project_to_project_detail(project.get(db, db_task.project_id), db)
        await project_sse_manager.send_event(
            db_task.project_id,
            json.dumps(project_sse_manager.convert_to_dict(project_data))
        )
    return TaskDetail.model_validate(db_task, from_attributes=True)

@router.get("/", response_model=List[TaskBrief])
def read_tasks(
    skip: int = 0, 
    limit: int = 100, 
    project_id: Optional[str] = None,
    milestone_id: Optional[int] = None,
    status: Optional[str] = None,
    priority: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """업무 목록 조회 (필터링 가능)"""
    tasks = task.get_multi_filtered(
        db=db, 
        skip=skip, 
        limit=limit,
        project_id=project_id,
        milestone_id=milestone_id,
        status=status,
        priority=priority
    )
    return [TaskBrief.model_validate(t, from_attributes=True) for t in tasks]

@router.get("/{task_id}", response_model=TaskDetail)
def read_task(task_id: int, db: Session = Depends(get_db)):
    """특정 업무 정보 조회"""
    db_task = task.get(db=db, id=task_id)
    if db_task is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="업무를 찾을 수 없습니다.")
    return TaskDetail.model_validate(db_task, from_attributes=True)

@router.put("/{task_id}", response_model=TaskDetail)
async def update_task(
    task_id: int, 
    task_in: TaskUpdate, 
    db: Session = Depends(get_db), 
    current_user: User = Depends(get_current_user)
):
    """업무 정보 수정"""
    db_task = task.get(db=db, id=task_id)
    if db_task is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="업무를 찾을 수 없습니다.")
    
    # 생성자, 담당자 또는 프로젝트 관리자만 수정 가능
    if (db_task.created_by != current_user.id and 
        current_user.id not in [a.id for a in db_task.assignees] and 
        not task.is_project_manager(db=db, task_id=task_id, user_id=current_user.id)):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="이 업무를 수정할 권한이 없습니다."
        )
    
    db_task = task.update(db=db, db_obj=db_task, obj_in=task_in)
    if db_task:
        project_data = convert_project_to_project_detail(project.get(db, db_task.project_id), db)
        await project_sse_manager.send_event(
            db_task.project_id,
            json.dumps(project_sse_manager.convert_to_dict(project_data))
        )
    return TaskDetail.model_validate(db_task, from_attributes=True)

@router.delete("/{task_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_task(task_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """업무 삭제"""
    db_task = task.get(db=db, id=task_id)
    if db_task is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="업무를 찾을 수 없습니다.")
    
    # 생성자 또는 프로젝트 관리자만 삭제 가능
    if db_task.created_by != current_user.id and not task.is_project_manager(db=db, task_id=task_id, user_id=current_user.id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="이 업무를 삭제할 권한이 없습니다."
        )
    
    task.remove(db=db, id=task_id)
    project_data = convert_project_to_project_detail(project.get(db, db_task.project_id), db)
    await project_sse_manager.send_event(
        db_task.project_id,
        json.dumps(project_sse_manager.convert_to_dict(project_data))
    )
    return None

# 하위 업무 관련 엔드포인트
@router.post("/{task_id}/subtasks", response_model=SubTaskDetail, status_code=status.HTTP_201_CREATED)
async def create_subtask(
    task_id: int,
    subtask_in: SubTaskCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """하위 업무 생성"""
    db_task = task.get(db=db, id=task_id)
    if db_task is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="업무를 찾을 수 없습니다.")
    
    # 생성자, 담당자 또는 프로젝트 관리자만 하위 업무 생성 가능
    if (db_task.created_by != current_user.id and 
        current_user.id not in [a.id for a in db_task.assignees] and 
        not task.is_project_manager(db=db, task_id=task_id, user_id=current_user.id)):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="이 업무에 하위 업무를 추가할 권한이 없습니다."
        )
    
    subtask = SubTask(
        title=subtask_in.title,
        task_id=task_id,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )
    db.add(subtask)
    db.commit()
    db.refresh(subtask)
    
    return SubTaskDetail.model_validate(subtask, from_attributes=True)

@router.put("/{task_id}/subtasks/{subtask_id}", response_model=SubTaskDetail)
async def update_subtask(
    task_id: int,
    subtask_id: int,
    subtask_in: SubTaskUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """하위 업무 수정"""
    db_task = task.get(db=db, id=task_id)
    if db_task is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="업무를 찾을 수 없습니다.")
    
    subtask = db.query(SubTask).filter(SubTask.id == subtask_id, SubTask.task_id == task_id).first()
    if subtask is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="하위 업무를 찾을 수 없습니다.")
    
    # 생성자, 담당자 또는 프로젝트 관리자만 수정 가능
    if (db_task.created_by != current_user.id and 
        current_user.id not in [a.id for a in db_task.assignees] and 
        not task.is_project_manager(db=db, task_id=task_id, user_id=current_user.id)):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="이 하위 업무를 수정할 권한이 없습니다."
        )
    
    update_data = subtask_in.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(subtask, field, value)
    
    # updated_at 필드를 현재 시간으로 업데이트
    subtask.updated_at = datetime.utcnow()
    
    db.add(subtask)
    db.commit()
    db.refresh(subtask)
    
    return SubTaskDetail.model_validate(subtask, from_attributes=True)

@router.delete("/{task_id}/subtasks/{subtask_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_subtask(
    task_id: int,
    subtask_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """하위 업무 삭제"""
    db_task = task.get(db=db, id=task_id)
    if db_task is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="업무를 찾을 수 없습니다.")
    
    subtask = db.query(SubTask).filter(SubTask.id == subtask_id, SubTask.task_id == task_id).first()
    if subtask is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="하위 업무를 찾을 수 없습니다.")
    
    # 생성자, 담당자 또는 프로젝트 관리자만 삭제 가능
    if (db_task.created_by != current_user.id and 
        current_user.id not in [a.id for a in db_task.assignees] and 
        not task.is_project_manager(db=db, task_id=task_id, user_id=current_user.id)):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="이 하위 업무를 삭제할 권한이 없습니다."
        )
    
    db.delete(subtask)
    db.commit()
    return None

@router.get("/{task_id}/assignees", response_model=List)
def read_task_assignees(task_id: int, db: Session = Depends(get_db)):
    """업무 담당자 목록 조회"""
    from new_schemas.user import UserBrief
    assignees = task.get_assignees(db=db, task_id=task_id)
    return [UserBrief.model_validate(a, from_attributes=True) for a in assignees]

@router.post("/{task_id}/assignees/{user_id}", response_model=TaskDetail)
async def add_task_assignee(
    task_id: int, 
    user_id: int, 
    db: Session = Depends(get_db), 
    current_user: User = Depends(get_current_user)
):
    """업무에 담당자 추가"""
    db_task = task.get(db=db, id=task_id)
    if db_task is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="업무를 찾을 수 없습니다.")
    
    # 생성자 또는 프로젝트 관리자만 담당자 추가 가능
    if db_task.created_by != current_user.id and not task.is_project_manager(db=db, task_id=task_id, user_id=current_user.id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="이 업무에 담당자를 추가할 권한이 없습니다."
        )
    
    db_task = task.add_assignee(db=db, task_id=task_id, user_id=user_id)
    if db_task:
        project_data = convert_project_to_project_detail(project.get(db, db_task.project_id), db)
        await project_sse_manager.send_event(
            db_task.project_id,
            json.dumps(project_sse_manager.convert_to_dict(project_data))
        )
    return TaskDetail.model_validate(db_task, from_attributes=True)

@router.delete("/{task_id}/assignees/{user_id}", response_model=TaskDetail)
async def remove_task_assignee(
    task_id: int, 
    user_id: int, 
    db: Session = Depends(get_db), 
    current_user: User = Depends(get_current_user)
):
    """업무에서 담당자 제거"""
    db_task = task.get(db=db, id=task_id)
    if db_task is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="업무를 찾을 수 없습니다.")
    
    # 생성자, 본인(담당자) 또는 프로젝트 관리자만 담당자 제거 가능
    if (db_task.created_by != current_user.id and 
        current_user.id != user_id and 
        not task.is_project_manager(db=db, task_id=task_id, user_id=current_user.id)):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="이 업무에서 담당자를 제거할 권한이 없습니다."
        )
    
    db_task = task.remove_assignee(db=db, task_id=task_id, user_id=user_id)
    if db_task:
        project_data = convert_project_to_project_detail(project.get(db, db_task.project_id), db)
        await project_sse_manager.send_event(
            db_task.project_id,
            json.dumps(project_sse_manager.convert_to_dict(project_data))
        )
    return TaskDetail.model_validate(db_task, from_attributes=True)

@router.get("/project/{project_id}", response_model=List[TaskBrief])
def read_tasks_by_project(
    project_id: str, 
    skip: int = 0, 
    limit: int = 100, 
    db: Session = Depends(get_db)
):
    """프로젝트별 업무 목록 조회"""
    return task.get_by_project(db=db, project_id=project_id, skip=skip, limit=limit)

@router.get("/milestone/{milestone_id}", response_model=List[TaskBrief])
def read_tasks_by_milestone(
    milestone_id: int, 
    skip: int = 0, 
    limit: int = 100, 
    db: Session = Depends(get_db)
):
    """마일스톤별 업무 목록 조회"""
    return task.get_by_milestone(db=db, milestone_id=milestone_id, skip=skip, limit=limit)

@router.get("/user/{user_id}", response_model=List[TaskBrief])
def read_tasks_by_user(
    user_id: int, 
    skip: int = 0, 
    limit: int = 100, 
    db: Session = Depends(get_db)
):
    """담당자별 업무 목록 조회"""
    return task.get_by_assignee(db=db, user_id=user_id, skip=skip, limit=limit)

# 댓글 관련 엔드포인트
@router.post("/{task_id}/comments", response_model=CommentDetail, status_code=status.HTTP_201_CREATED)
async def create_comment(
    task_id: int,
    comment_in: CommentCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """댓글 생성"""
    db_task = task.get(db=db, id=task_id)
    if db_task is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="업무를 찾을 수 없습니다.")
    
    comment = task.create_comment(
        db=db, 
        task_id=task_id, 
        content=comment_in.content, 
        created_by=current_user.id
    )
    
    return CommentDetail.model_validate(comment, from_attributes=True)

@router.get("/{task_id}/comments", response_model=List[CommentDetail])
def read_task_comments(
    task_id: int,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    """업무 댓글 목록 조회"""
    db_task = task.get(db=db, id=task_id)
    if db_task is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="업무를 찾을 수 없습니다.")
    
    comments = task.get_comments(db=db, task_id=task_id, skip=skip, limit=limit)
    return [CommentDetail.model_validate(c, from_attributes=True) for c in comments]

@router.put("/{task_id}/comments/{comment_id}", response_model=CommentDetail)
async def update_comment(
    task_id: int,
    comment_id: int,
    comment_in: CommentUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """댓글 수정"""
    db_task = task.get(db=db, id=task_id)
    if db_task is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="업무를 찾을 수 없습니다.")
    
    comment = db.query(Comment).filter(Comment.id == comment_id, Comment.task_id == task_id).first()
    if comment is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="댓글을 찾을 수 없습니다.")
    
    # 작성자만 수정 가능
    if comment.created_by != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="이 댓글을 수정할 권한이 없습니다."
        )
    
    comment = task.update_comment(db=db, comment_id=comment_id, content=comment_in.content)
    
    return CommentDetail.model_validate(comment, from_attributes=True)

@router.delete("/{task_id}/comments/{comment_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_comment(
    task_id: int,
    comment_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """댓글 삭제"""
    db_task = task.get(db=db, id=task_id)
    if db_task is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="업무를 찾을 수 없습니다.")
    
    comment = db.query(Comment).filter(Comment.id == comment_id, Comment.task_id == task_id).first()
    if comment is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="댓글을 찾을 수 없습니다.")
    
    # 작성자 또는 프로젝트 관리자만 삭제 가능
    if (comment.created_by != current_user.id and 
        not task.is_project_manager(db=db, task_id=task_id, user_id=current_user.id)):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="이 댓글을 삭제할 권한이 없습니다."
        )
    
    task.delete_comment(db=db, comment_id=comment_id)
    return None 