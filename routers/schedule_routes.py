from fastapi import APIRouter, Depends, HTTPException
from database import SessionLocal
from crud.schedule import (
    get_schedules,
    create_schedule
)
from crud.project import get_project
from schemas.schedule import ScheduleCreate, ScheduleUpdate, Schedule
from typing import List
import logging
from utils.sse_manager import project_sse_manager
import json

router = APIRouter(
    prefix="/project",
    tags=["schedule"]
)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
        
@router.get("/{project_id}/schedules", response_model=List[Schedule])
def read_schedules(project_id: str, db: SessionLocal = Depends(get_db)):  # type: ignore
    try:
        schedules = get_schedules(db, project_id)
        return schedules
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    
@router.post("/{project_id}/schedule", response_model=ScheduleCreate)
async def create_schedule_route(project_id: str, schedule: ScheduleCreate, db: SessionLocal = Depends(get_db)):  # type: ignore
    try:
        db_schedule = create_schedule(db, schedule)
        if db_schedule:
            project_data = get_project(db, project_id)
            await project_sse_manager.send_event(
                project_id,
                json.dumps(project_sse_manager.convert_to_dict(project_data))
            )
            logging.info(f"[SSE] Project {project_id} updated from Schedule create.")
        else:
            raise HTTPException(status_code=404, detail="Project not found")
        return db_schedule
    except HTTPException as he:
        logging.error(f"HTTP Exception during schedule creation: {str(he)}")
        raise
    except Exception as e:
        logging.error(f"Unexpected error during schedule creation: {str(e)}")
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail="Internal server error occurred while creating schedule"
        )