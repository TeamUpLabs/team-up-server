from schemas.schedule import ScheduleCreate, ScheduleUpdate
from sqlalchemy.orm import Session
from models.schedule import Schedule

def create_schedule(db: Session, schedule: ScheduleCreate):
    db_schedule = Schedule(**schedule.model_dump())
    db.add(db_schedule)
    db.commit()
    db.refresh(db_schedule)
    return db_schedule

def get_schedule(db: Session, schedule_id: int):
    return db.query(Schedule).filter(Schedule.id == schedule_id).first()

def get_schedules(db: Session, project_id: str):
    schedules = db.query(Schedule).filter(Schedule.project_id == project_id).all()
    if not schedules:
        return []
    return schedules
    

def update_schedule(db: Session, schedule_id: int, schedule: ScheduleUpdate):
    db_schedule = db.query(Schedule).filter(Schedule.id == schedule_id).first()
    db_schedule.update(schedule.model_dump())