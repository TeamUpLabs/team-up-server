from schemas.task import TaskCreate, Task, TaskStatusUpdate, TaskUpdate, Comment, UpdateSubTaskState
from models.task import Task as TaskModel
from sqlalchemy.orm import Session
import json
from typing import List
from models.member import Member as MemberModel
from schemas.member import Member as MemberSchema
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

def create_task(db: Session, project_id: str, task: TaskCreate):
    try:
        json_fields = ['assignee_id', 'tags', 'subtasks', 'comments']
        task_data = task.dict()
        task_data['project_id'] = project_id

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

def get_tasks_by_member_id_and_project_id(db: Session, member_id: int, project_id: str):
  from sqlalchemy import cast
  from sqlalchemy.dialects.postgresql import JSONB

  tasks = db.query(TaskModel).filter(
      cast(TaskModel.assignee_id, JSONB).contains([member_id]),
      TaskModel.project_id == project_id
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

def delete_task_by_id(db: Session, project_id: str, task_id: int):
  task = db.query(TaskModel).filter(TaskModel.id == task_id, TaskModel.project_id == project_id).first()
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

def update_task_by_id(db: Session, project_id: str, task_id: int, task_update: TaskUpdate):
  task = db.query(TaskModel).filter(TaskModel.id == task_id, TaskModel.project_id == project_id).first()
  
  if task:
    task_data = task_update.dict(exclude_unset=True, exclude_none=True)
    for field, value in task_data.items():
      setattr(task, field, value)
    db.commit()
    db.refresh(task)
    
    return Task.model_validate(task)
  return None

def update_subtask_state_by_id(db: Session, project_id: str, task_id: int, subtask_id: int, subtask_update: UpdateSubTaskState):
  task = db.query(TaskModel).filter(TaskModel.id == task_id, TaskModel.project_id == project_id).first()
  if task:
    subtask = next((subtask for subtask in task.subtasks if subtask['id'] == subtask_id), None)
    if subtask:
      subtask['completed'] = subtask_update.completed
      db.query(TaskModel).filter(TaskModel.id == task_id, TaskModel.project_id == project_id).update(
        {"subtasks": task.subtasks},
        synchronize_session="fetch"
      )
      db.commit()
      db.refresh(task)
      return Task.model_validate(task)
  return None

async def upload_task_comment(db: Session, project_id: str, task_id: int, comment: Comment):
  try:
    # Get task
    task = db.query(TaskModel).filter(TaskModel.id == task_id, TaskModel.project_id == project_id).first()
    if not task:
      print("Task not found")
      return None
    
    current_comments = []
    if task.comments:
      if isinstance(task.comments, list):
        current_comments = task.comments.copy()
      elif isinstance(task.comments, str):
        current_comments = json.loads(task.comments)
    
    comment_dict = {
      "author_id": comment.author_id,
      "content": comment.content,
      "createdAt": comment.createdAt
    }
    
    current_comments.append(comment_dict)

    from sqlalchemy import update
    stmt = update(TaskModel).where(
      TaskModel.id == task_id,
      TaskModel.project_id == project_id
    ).values(
      comments=current_comments
    )
    
    for assignee_id in task.assignee_id:
      if assignee_id != comment.author_id:
        member = get_basic_member_info(db, assignee_id)
        if member:
          await send_notification(
            db=db,
            id=int(datetime.now().timestamp()),
            title=f"{task.title}에 대한 {member.name}님의 새 댓글",
            message=comment.content,
            type="task",
            isRead=False,
            sender_id=comment.author_id,
            receiver_id=assignee_id,
            project_id=project_id,
          )
    
    db.execute(stmt)
    db.commit()
    
    # Return updated task
    return Task.model_validate(task)
  except Exception as e:
    db.rollback()
    print(f"Error in upload_task_comment: {str(e)}")
    import traceback
    print(traceback.format_exc())
    raise