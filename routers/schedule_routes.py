from fastapi import APIRouter, Depends, HTTPException
from database import SessionLocal
from crud.schedule import (
    get_schedules,
    create_schedule
)
from schemas.schedule import ScheduleCreate, ScheduleUpdate, Schedule
from typing import List
import logging

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
def read_schedules(project_id: str, db: SessionLocal = Depends(get_db)):
    try:
        schedules = get_schedules(db, project_id)
        return schedules
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    
@router.post("/{project_id}/schedule", response_model=ScheduleCreate)
def create_schedule_route(schedule: ScheduleCreate, db: SessionLocal = Depends(get_db)):
    try:
        db_schedule = create_schedule(db, schedule)
        logging.info(f"Successfully created schedule with id: {db_schedule.id}")
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