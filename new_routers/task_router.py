from fastapi import APIRouter, Depends, HTTPException, status
from typing import List, Optional
from sqlalchemy.orm import Session

from database import get_db
from auth import get_current_user
from new_crud import task, project
from new_schemas.task import TaskCreate, TaskUpdate, TaskBrief, TaskDetail
from new_models.user import User
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