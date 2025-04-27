from schemas.milestone import MileStoneCreate, MileStoneUpdate, MileStone
from models.milestone import Milestone as MileStoneModel
from sqlalchemy.orm import Session
import json
from crud.task import get_basic_member_info, get_task_by_project_id_and_milestone_id, delete_task_by_id

def create_milestone(db: Session, milestone: MileStoneCreate):
  try:
    json_fields = ['assignee_id', 'tags']
    milestone_data = milestone.dict()
    
    for field in json_fields:
      if field in milestone_data and milestone_data[field] is not None:
        if isinstance(milestone_data[field], str):
            milestone_data[field] = json.loads(milestone_data[field])
            
    db_milestone = MileStoneModel(**milestone_data)
    db.add(db_milestone)
    db.commit()
    db.refresh(db_milestone)
    return db_milestone
  
  except Exception as e:
    print(f"Error in create_milestone: {str(e)}")
    db.rollback()
    raise
  
  
def get_milestones(db: Session, skip: int = 0, limit: int = 100):
  from schemas.member import Member as MemberSchema
  milestones = db.query(MileStoneModel).offset(skip).limit(limit).all()
  
  if milestones:
    for milestone in milestones:
      subtasks = get_task_by_project_id_and_milestone_id(db, milestone.project_id, milestone.id)
      milestone.subtasks = subtasks
      
      # Initialize assignee as empty list if None
      milestone.assignee = []
      
      # Only try to get members if assignee_id exists and isn't empty
      if milestone.assignee_id and isinstance(milestone.assignee_id, list):
        for member_id in milestone.assignee_id:
          member = get_basic_member_info(db, member_id)
          if member:
            milestone.assignee.append(member)
      
  return milestones

def get_milestones_by_project_id(db: Session, project_id: str):
  from schemas.member import Member as MemberSchema
  milestones = db.query(MileStoneModel).filter(MileStoneModel.project_id == project_id).all()
  
  if milestones:
    for milestone in milestones:
      subtasks = get_task_by_project_id_and_milestone_id(db, project_id, milestone.id)
      milestone.subtasks = subtasks
      
      # Initialize assignee as empty list if None
      milestone.assignee = []
      
      # Only try to get members if assignee_id exists and isn't empty
      if milestone.assignee_id and isinstance(milestone.assignee_id, list):
        for member_id in milestone.assignee_id:
          member = get_basic_member_info(db, member_id)
          if member:
            milestone.assignee.append(member)
      
  return milestones

def delete_milestone_by_id(db: Session, milestone_id: int):
  milestone = db.query(MileStoneModel).filter(MileStoneModel.id == milestone_id).first()
  tasks = get_task_by_project_id_and_milestone_id(db, milestone.project_id, milestone.id)
  if milestone:
    for task in tasks:
      delete_task_by_id(db, task.id)
    db.delete(milestone)
    db.commit()
    return True
  return False

def update_milestone_by_id(db: Session, project_id: str, milestone_id: int, milestone_update: MileStoneUpdate):
  db_milestone = db.query(MileStoneModel).filter(MileStoneModel.id == milestone_id, MileStoneModel.project_id == project_id).first()
  if db_milestone:
    milestone_data = milestone_update.dict(exclude_unset=True, exclude_none=True)
    for field, value in milestone_data.items():
      setattr(db_milestone, field, value)
    db.commit()
    db.refresh(db_milestone)
    return MileStone.model_validate(db_milestone)
  return None