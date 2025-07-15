from fastapi import APIRouter, HTTPException, status

from new_schemas.schedule import ScheduleResponse, ScheduleCreate, ScheduleUpdate
from new_crud import schedule, project
from database import get_db
from sqlalchemy.orm import Session
from fastapi import Depends
from typing import List
from new_routers.project_router import convert_project_to_project_detail
from utils.sse_manager import project_sse_manager
import json
from new_models.user import User
from new_routers.auth_router import get_current_user

router = APIRouter(
    prefix="/api/projects",
    tags=["schedules"]
)

@router.post("/{project_id}/schedules", response_model=ScheduleResponse)
async def create_schedule(
    project_id: str, 
    schedule_in: ScheduleCreate, 
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    # 생성자, 담당자 또는 프로젝트 관리자만 수정 가능
    if (schedule_in.created_by != current_user.id and 
        not schedule.is_project_manager(db=db, project_id=project_id, user_id=current_user.id)):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="이 일정을 생성할 권한이 없습니다."
        )
        
    db_schedule = schedule.create(db, project_id=project_id, obj_in=schedule_in)
    if db_schedule:
        project_data = convert_project_to_project_detail(project.get(db, db_schedule.project_id), db)
        await project_sse_manager.send_event(
            db_schedule.project_id,
            json.dumps(project_sse_manager.convert_to_dict(project_data))
        )
    return ScheduleResponse.model_validate(db_schedule, from_attributes=True)

@router.get("/{project_id}/schedules", response_model=List[ScheduleResponse])
def read_schedules(project_id: str, db: Session = Depends(get_db)):
    db_schedules = schedule.get_by_project(db, project_id)
    return [ScheduleResponse.model_validate(db_schedule, from_attributes=True) for db_schedule in db_schedules]

@router.get("/{project_id}/schedules/{schedule_id}", response_model=ScheduleResponse)
def read_schedule(project_id: str, schedule_id: int, db: Session = Depends(get_db)):
    db_schedule = schedule.get_by_id(db, schedule_id=schedule_id)
    if not db_schedule or db_schedule.project_id != project_id:
        raise HTTPException(status_code=404, detail="Schedule not found")
    return ScheduleResponse.model_validate(db_schedule, from_attributes=True)

@router.put("/{project_id}/schedules/{schedule_id}", response_model=ScheduleResponse)
async def update_schedule(project_id: str, schedule_id: int, schedule_in: ScheduleUpdate, db: Session = Depends(get_db)):
    db_schedule = schedule.get_by_id(db, schedule_id=schedule_id)
    if not db_schedule or db_schedule.project_id != project_id:
        raise HTTPException(status_code=404, detail="Schedule not found")
    
    db_schedule = schedule.update(db, db_obj=db_schedule, obj_in=schedule_in)
    
    # Send SSE event to update project data in real-time
    project_data = convert_project_to_project_detail(project.get(db, db_schedule.project_id), db)
    await project_sse_manager.send_event(
        db_schedule.project_id,
        json.dumps(project_sse_manager.convert_to_dict(project_data))
    )
    
    return ScheduleResponse.model_validate(db_schedule, from_attributes=True)

@router.delete("/{project_id}/schedules/{schedule_id}")
async def delete_schedule(project_id: str, schedule_id: int, db: Session = Depends(get_db)) -> dict:
    db_schedule = schedule.get_by_id(db, schedule_id=schedule_id)
    if not db_schedule or db_schedule.project_id != project_id:
        raise HTTPException(status_code=404, detail="Schedule not found")
    
    db_schedule = schedule.remove(db, schedule_id=schedule_id)
    
    # Send SSE event to update project data in real-time
    project_data = convert_project_to_project_detail(project.get(db, project_id), db)
    await project_sse_manager.send_event(
        project_id,
        json.dumps(project_sse_manager.convert_to_dict(project_data))
    )
    return {"message": "Schedule deleted successfully"}
