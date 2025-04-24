from schemas.task import TaskCreate, Task, TaskStatusUpdate
from models.task import Task as TaskModel
from sqlalchemy.orm import Session
import json
from models.member import Member as MemberModel
from schemas.member import Member as MemberSchema

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

def create_task(db: Session, task: TaskCreate):
    try:
        json_fields = ['assignee_id', 'tags', 'subtasks', 'comments']
        task_data = task.dict()

        for field in json_fields:
            if field in task_data and task_data[field] is not None:
                if isinstance(task_data[field], str):
                    task_data[field] = json.loads(task_data[field])

        db_task = TaskModel(**task_data)
        db.add(db_task)
        db.commit()
        db.refresh(db_task)
        return Task.model_validate(db_task)
    except Exception as e:
        print(f"Error in create_task: {str(e)}")
        db.rollback()
        raise
      
def get_tasks(db: Session, skip: int = 0, limit: int = 100):
  tasks = db.query(TaskModel).offset(skip).limit(limit).all()
  result = []
  
  if tasks:
    for task in tasks:
      assignee = []
      if task.assignee_id:
        for assignee_id in task.assignee_id:
          member = get_basic_member_info(db, assignee_id)
          if member:
            assignee.append(member)
      task.assignee = assignee
      
      # Convert SQLAlchemy model to Pydantic model
      result.append(Task.model_validate(task))
      
  return result

def get_tasks_by_milestone_id(db: Session, milestone_id: int):
  tasks = db.query(TaskModel).filter(TaskModel.milestone_id == milestone_id).all()
  result = []
  
  for task in tasks:
    assignee = []
    if task.assignee_id:
      for assignee_id in task.assignee_id:
        member = get_basic_member_info(db, assignee_id)
        if member:
          assignee.append(member)
    task.assignee = assignee
    
    # Convert SQLAlchemy model to Pydantic model
    result.append(Task.model_validate(task))
    
  return result


def get_tasks_by_project_id(db: Session, project_id: str):
  tasks = db.query(TaskModel).filter(TaskModel.project_id == project_id).all()
  result = []
  
  for task in tasks:
    assignee = []
    if task.assignee_id:
      for assignee_id in task.assignee_id:
        member = get_basic_member_info(db, assignee_id)
        if member:
          assignee.append(member)
    task.assignee = assignee
    
    # Convert SQLAlchemy model to Pydantic model
    result.append(Task.model_validate(task))
    
  return result

def get_task_by_project_id_and_milestone_id(db: Session, project_id: str, milestone_id: int):
  tasks = db.query(TaskModel).filter(TaskModel.project_id == project_id, TaskModel.milestone_id == milestone_id).all()
  result = []
  
  for task in tasks:
    assignee = [] 
    if task.assignee_id:
      for assignee_id in task.assignee_id:
        member = get_basic_member_info(db, assignee_id)
        if member:
          assignee.append(member)
    task.assignee = assignee
    
    # Convert SQLAlchemy model to Pydantic model
    result.append(Task.model_validate(task))
    
  return result
        
def get_tasks_by_member_id(db: Session, member_id: int):
  from sqlalchemy import cast
  from sqlalchemy.dialects.postgresql import JSONB

  tasks = db.query(TaskModel).filter(
      cast(TaskModel.assignee_id, JSONB).contains([member_id])
  ).all()
  
  result = []
  
  for task in tasks:
    assignee = []
    if task.assignee_id:
      for assignee_id in task.assignee_id:
        member = get_basic_member_info(db, assignee_id)
        if member:
          assignee.append(member)
    task.assignee = assignee
    
    # Convert SQLAlchemy model to Pydantic model
    result.append(Task.model_validate(task))
    
  return result

def delete_task_by_id(db: Session, task_id: int):
  task = db.query(TaskModel).filter(TaskModel.id == task_id).first()
  if task:
    db.delete(task)
    db.commit()
    return True
  return False

def update_task_status(db: Session, project_id: str, task_id: int, status: TaskStatusUpdate):
  task = db.query(TaskModel).filter(TaskModel.id == task_id, TaskModel.project_id == project_id).first()
  if task:
    task.status = status.status
    db.commit()
    db.refresh(task)
    return Task.model_validate(task)
  return None