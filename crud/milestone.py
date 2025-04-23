from schemas.milestone import MileStoneCreate
from models.milestone import Milestone as MileStoneModel
from sqlalchemy.orm import Session
import json
from crud.task import get_tasks_by_project_id, get_basic_member_info, get_tasks_by_milestone_id

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
      subtasks = get_tasks_by_milestone_id(db, milestone.id)
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
      subtasks = get_tasks_by_milestone_id(db, milestone.id)
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
      