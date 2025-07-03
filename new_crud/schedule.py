from new_models.schedule import Schedule
from new_schemas.schedule import ScheduleCreate, ScheduleUpdate
from new_crud.base import CRUDBase
from sqlalchemy.orm import Session
from typing import List
from new_models.association_tables import schedule_assignees

class CRUDSchedule(CRUDBase[Schedule, ScheduleCreate, ScheduleUpdate]):
    """스케줄 모델에 대한 CRUD 작업"""
    def create(self, db: Session, *, project_id: str, obj_in: ScheduleCreate) -> Schedule:
        schedule_data_for_db = obj_in.model_dump(exclude={"assignee_ids"})
        schedule_data_for_db["project_id"] = project_id
        db_schedule = Schedule(**schedule_data_for_db)
        db.add(db_schedule)
        db.flush()  # Get the ID without committing
        
        # Handle assignees
        if obj_in.assignee_ids:
            from new_models.user import User
            for user_id in obj_in.assignee_ids:
                user = db.query(User).filter(User.id == user_id).first()
                if user:
                    db_schedule.assignees.append(user)
        
        db.commit()
        db.refresh(db_schedule)
        return db_schedule
    
    def get_by_project(self, db: Session, *, project_id: str) -> List[Schedule]:
        return db.query(Schedule).filter(Schedule.project_id == project_id).all()
    
    def get_by_assignee(self, db: Session, *, user_id: int) -> List[Schedule]:
        return db.query(Schedule).join(schedule_assignees).filter(
            schedule_assignees.c.user_id == user_id
        ).all()
    
    def get_by_id(self, db: Session, *, schedule_id: int) -> Schedule:
        return db.query(Schedule).filter(Schedule.id == schedule_id).first()
        
    def get_multi(self, db: Session, *, skip: int = 0, limit: int = 100) -> List[Schedule]:
        return db.query(Schedule).offset(skip).limit(limit).all()
        
    def update(self, db: Session, *, db_obj: Schedule, obj_in: ScheduleUpdate) -> Schedule:
        obj_data = db_obj.__dict__
        update_data = obj_in.model_dump(exclude_unset=True, exclude={"assignee_ids"})
        
        for field in obj_data:
            if field in update_data:
                setattr(db_obj, field, update_data[field])
        
        # Handle assignees update if provided
        if hasattr(obj_in, "assignee_ids") and obj_in.assignee_ids is not None:
            from new_models.user import User
            # Clear existing assignees
            db_obj.assignees = []
            # Add new assignees
            for user_id in obj_in.assignee_ids:
                user = db.query(User).filter(User.id == user_id).first()
                if user:
                    db_obj.assignees.append(user)
        
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj
        
    def remove(self, db: Session, *, schedule_id: int) -> Schedule:
        obj = db.query(Schedule).get(schedule_id)
        db.delete(obj)
        db.commit()
        return obj

schedule = CRUDSchedule(Schedule)