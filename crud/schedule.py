from schemas.schedule import ScheduleCreate, ScheduleUpdate
from sqlalchemy.orm import Session
from models.schedule import Schedule
from models.member import Member as MemberModel
from schemas.member import Member as MemberSchema
import logging
from utils.send_notification import send_notification
from datetime import datetime

def get_basic_member_info(db: Session, member_id: int):
    """Get basic member info without loading related data to avoid circular references"""
    member = db.query(MemberModel).filter(MemberModel.id == member_id).first()
    if not member:
        return None
    
    # Create a basic info dict with all required fields
    basic_info = {
        "id": member.id,
        "name": member.name,
        "email": member.email,
        "role": member.role,
        "status": member.status,
        "profileImage": member.profileImage,
        "contactNumber": member.contactNumber,
        "workingHours": member.workingHours,
        # Include other required fields from the Member schema
        "skills": member.skills or [],
        "projects": member.projects or [],
        "languages": member.languages or [],
        "password": None  # Include as None since it's optional
    }
    
    return MemberSchema.model_validate(basic_info)

async def create_schedule(db: Session, schedule: ScheduleCreate):
    try:
        schedule_data_for_db = schedule.model_dump()
        db_schedule = Schedule(**schedule_data_for_db)
        db.add(db_schedule)
        db.commit()
        db.refresh(db_schedule)
        
        for assignee_id in db_schedule.assignee_id:
          if assignee_id != db_schedule.created_by:
            member = get_basic_member_info(db, assignee_id)
            if member:
              await send_notification(
                db=db,
                id=int(datetime.now().timestamp()),
                title="스케줄 생성",
                message=f'"{db_schedule.title}" 스케줄에 참여되었습니다.',
                type="schedule",
                isRead=False,
                sender_id=db_schedule.created_by,
                receiver_id=member.id,
                project_id=db_schedule.project_id
              )
        return db_schedule
    except Exception as e:
        print(f"Error in create_schedule: {str(e)}")
        db.rollback()
        raise

def get_schedule(db: Session, schedule_id: int):
    schedule = db.query(Schedule).filter(Schedule.id == schedule_id).first()
    
    if schedule:
      assignee = []
      if schedule.assignee_id:
        for assignee_id in schedule.assignee_id:
          assignee.append(get_basic_member_info(db, assignee_id))
      schedule.assignee = assignee
      return schedule
    return None

def get_schedules(db: Session, project_id: str):
    schedules = db.query(Schedule).filter(Schedule.project_id == project_id).all()
    result = []
    
    for schedule in schedules:
      assignee = []
      if schedule.assignee_id:
        for assignee_id in schedule.assignee_id:
          assignee.append(get_basic_member_info(db, assignee_id))
      schedule.assignee = assignee
      result.append(schedule)
    if not schedules:
        return []
    return result
    

def update_schedule(db: Session, schedule_id: int, schedule: ScheduleUpdate):
    db_schedule = db.query(Schedule).filter(Schedule.id == schedule_id).first()
    
    if db_schedule:
      schedule_data = schedule.model_dump()
      for field, value in schedule_data.items():
        setattr(db_schedule, field, value)
      db.commit()
      db.refresh(db_schedule)
      return db_schedule
    return None

def delete_schedule_by_id(db: Session, schedule_id: int):
    schedule = db.query(Schedule).filter(Schedule.id == schedule_id).first()
    if not schedule:
        return None
    db.delete(schedule)
    db.commit()
    return schedule
