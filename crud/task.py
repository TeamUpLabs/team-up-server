from schemas.task import TaskCreate
from models.task import Task as TaskModel
from models.member import Member as MemberModel
from sqlalchemy.orm import Session
import json

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
        return db_task
    except Exception as e:
        print(f"Error in create_task: {str(e)}")
        db.rollback()
        raise
      
def get_tasks(db: Session, skip: int = 0, limit: int = 100):
  tasks = db.query(TaskModel).offset(skip).limit(limit).all()
  
  if tasks:
    for task in tasks:
      assignee = []
      for assignee_id in task.assignee_id:
        member = db.query(MemberModel).filter(
          MemberModel.id == assignee_id
        ).first()
        assignee.append(member)
      task.assignee = assignee
      
  return tasks

def get_tasks_by_project_id(db: Session, project_id: str):
  tasks = db.query(TaskModel).filter(TaskModel.project_id == project_id).all()
  
  for task in tasks:
    assignee = []
    for assignee_id in task.assignee_id:
      member = db.query(MemberModel).filter(
        MemberModel.id == assignee_id
      ).first()
      assignee.append(member)
    task.assignee = assignee
  return tasks
        
        