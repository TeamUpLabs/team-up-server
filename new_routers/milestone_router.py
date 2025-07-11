from fastapi import APIRouter, Depends, HTTPException, status
from typing import List, Optional
from sqlalchemy.orm import Session

from database import get_db
from auth import get_current_user
from new_crud import milestone, project
from new_schemas.milestone import MilestoneCreate, MilestoneUpdate, MilestoneBrief, MilestoneDetail
from new_models.user import User
from new_routers.project_router import convert_project_to_project_detail
from utils.sse_manager import project_sse_manager
import json

router = APIRouter(
    prefix="/api/milestones",
    tags=["milestones"]
)

@router.post("/", response_model=MilestoneDetail, status_code=status.HTTP_201_CREATED)
async def create_milestone(
    milestone_in: MilestoneCreate, 
    current_user: User = Depends(get_current_user), 
    db: Session = Depends(get_db)
):
    """새 마일스톤 생성"""
    # 현재 사용자가 마일스톤 생성자로 설정
    if milestone_in.created_by is None:
        milestone_in.created_by = current_user.id
        
    # 프로젝트 존재 및 권한 확인
    db_project = project.get(db=db, id=milestone_in.project_id)
    if db_project is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="프로젝트를 찾을 수 없습니다.")
    
    # 프로젝트 멤버인지 확인 (소유자 또는 관리자만 가능)
    if db_project.owner_id != current_user.id:
        # TODO: 프로젝트 멤버 관리자 권한 확인 로직 추가
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="이 프로젝트에 마일스톤을 추가할 권한이 없습니다."
        )
    
    db_milestone = milestone.create(db=db, obj_in=milestone_in)
    if db_milestone:
        project_data = convert_project_to_project_detail(project.get(db, db_milestone.project_id), db)
        await project_sse_manager.send_event(
            db_milestone.project_id,
            json.dumps(project_sse_manager.convert_to_dict(project_data))
        )
    return MilestoneDetail.model_validate(db_milestone, from_attributes=True)

@router.get("/", response_model=List[MilestoneBrief])
def read_milestones(
    skip: int = 0, 
    limit: int = 100, 
    project_id: Optional[str] = None,
    status: Optional[str] = None,
    priority: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """마일스톤 목록 조회 (필터링 가능)"""
    milestones = milestone.get_multi_filtered(
        db=db, 
        skip=skip, 
        limit=limit,
        project_id=project_id,
        status=status,
        priority=priority
    )
    return [MilestoneBrief.model_validate(m, from_attributes=True) for m in milestones]

@router.get("/{milestone_id}", response_model=MilestoneDetail)
def read_milestone(milestone_id: int, db: Session = Depends(get_db)):
    """특정 마일스톤 정보 조회"""
    db_milestone = milestone.get(db=db, id=milestone_id)
    if db_milestone is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="마일스톤을 찾을 수 없습니다.")
    return MilestoneDetail.model_validate(db_milestone, from_attributes=True)

@router.put("/{milestone_id}", response_model=MilestoneDetail)
async def update_milestone(
    milestone_id: int,
    milestone_in: MilestoneUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """마일스톤 정보 업데이트"""
    db_milestone = milestone.get(db=db, id=milestone_id)
    if db_milestone is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="마일스톤을 찾을 수 없습니다.")
    
    # 프로젝트 소유자 또는 생성자만 수정 가능
    db_project = project.get(db=db, id=db_milestone.project_id)
    if db_project.owner_id != current_user.id and db_milestone.created_by != current_user.id:
        # TODO: 프로젝트 멤버 관리자 권한 확인 로직 추가
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="이 마일스톤을 수정할 권한이 없습니다."
        )
    
    db_milestone = milestone.update(db=db, db_obj=db_milestone, obj_in=milestone_in)
    if db_milestone:
        project_data = convert_project_to_project_detail(project.get(db, db_milestone.project_id), db)
        await project_sse_manager.send_event(
            db_milestone.project_id,
            json.dumps(project_sse_manager.convert_to_dict(project_data))
        )
    return MilestoneDetail.model_validate(db_milestone, from_attributes=True)

@router.delete("/{milestone_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_milestone(
    milestone_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """마일스톤 삭제"""
    db_milestone = milestone.get(db=db, id=milestone_id)
    if db_milestone is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="마일스톤을 찾을 수 없습니다.")
    
    # 프로젝트 소유자 또는 생성자만 삭제 가능
    db_project = project.get(db=db, id=db_milestone.project_id)
    if db_project.owner_id != current_user.id and db_milestone.created_by != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="이 마일스톤을 삭제할 권한이 없습니다."
        )
    
    try:
        milestone.remove(db=db, id=milestone_id)
    except HTTPException as e:
        # 연결된 업무가 있는 경우 등의 예외 처리
        raise e
    
    project_data = convert_project_to_project_detail(project.get(db, db_milestone.project_id), db)
    await project_sse_manager.send_event(
        db_milestone.project_id,
        json.dumps(project_sse_manager.convert_to_dict(project_data))
    )
    return None

@router.get("/project/{project_id}", response_model=List[MilestoneDetail])
def read_milestones_by_project(
    project_id: str, 
    skip: int = 0, 
    limit: int = 100, 
    db: Session = Depends(get_db)
):
    """프로젝트별 마일스톤 목록 조회"""
    return milestone.get_by_project(db=db, project_id=project_id, skip=skip, limit=limit)

@router.get("/user/{user_id}", response_model=List[MilestoneBrief])
def read_milestones_by_user(
    user_id: int, 
    skip: int = 0, 
    limit: int = 100, 
    db: Session = Depends(get_db)
):
    """담당자별 마일스톤 목록 조회"""
    return milestone.get_by_assignee(db=db, user_id=user_id, skip=skip, limit=limit)

@router.get("/{milestone_id}/tasks", response_model=List)
def read_milestone_tasks(milestone_id: int, db: Session = Depends(get_db)):
    """마일스톤에 속한 업무 목록 조회"""
    from new_schemas.task import TaskBrief
    tasks = milestone.get_tasks(db=db, milestone_id=milestone_id)
    return [TaskBrief.model_validate(t, from_attributes=True) for t in tasks]

@router.get("/{milestone_id}/assignees", response_model=List)
def read_milestone_assignees(milestone_id: int, db: Session = Depends(get_db)):
    """마일스톤 담당자 목록 조회"""
    from new_schemas.user import UserBrief
    assignees = milestone.get_assignees(db=db, milestone_id=milestone_id)
    return [UserBrief.model_validate(a, from_attributes=True) for a in assignees]

@router.post("/{milestone_id}/assignees/{user_id}", response_model=MilestoneDetail)
async def add_milestone_assignee(
    milestone_id: int, 
    user_id: int, 
    db: Session = Depends(get_db), 
    current_user: User = Depends(get_current_user)
):
    """마일스톤에 담당자 추가"""
    db_milestone = milestone.get(db=db, id=milestone_id)
    if db_milestone is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="마일스톤을 찾을 수 없습니다.")
    
    # 생성자 또는 프로젝트 관리자만 담당자 추가 가능
    if db_milestone.created_by != current_user.id and not milestone.is_project_manager(db=db, milestone_id=milestone_id, user_id=current_user.id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="이 마일스톤에 담당자를 추가할 권한이 없습니다."
        )
    
    db_milestone = milestone.add_assignee(db=db, milestone_id=milestone_id, user_id=user_id)
    if db_milestone:
        project_data = convert_project_to_project_detail(project.get(db, db_milestone.project_id), db)
        await project_sse_manager.send_event(
            db_milestone.project_id,
            json.dumps(project_sse_manager.convert_to_dict(project_data))
        )
    return MilestoneDetail.model_validate(db_milestone, from_attributes=True)

@router.delete("/{milestone_id}/assignees/{user_id}", response_model=MilestoneDetail)
async def remove_milestone_assignee(
    milestone_id: int, 
    user_id: int, 
    db: Session = Depends(get_db), 
    current_user: User = Depends(get_current_user)
):
    """마일스톤에서 담당자 제거"""
    db_milestone = milestone.get(db=db, id=milestone_id)
    if db_milestone is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="마일스톤을 찾을 수 없습니다.")
    
    # 생성자, 본인(담당자) 또는 프로젝트 관리자만 담당자 제거 가능
    if (db_milestone.created_by != current_user.id and 
        current_user.id != user_id and 
        not milestone.is_project_manager(db=db, milestone_id=milestone_id, user_id=current_user.id)):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="이 마일스톤에서 담당자를 제거할 권한이 없습니다."
        )
    
    db_milestone = milestone.remove_assignee(db=db, milestone_id=milestone_id, user_id=user_id)
    if db_milestone:
        project_data = convert_project_to_project_detail(project.get(db, db_milestone.project_id), db)
        await project_sse_manager.send_event(
            db_milestone.project_id,
            json.dumps(project_sse_manager.convert_to_dict(project_data))
        )
    return MilestoneDetail.model_validate(db_milestone, from_attributes=True) 