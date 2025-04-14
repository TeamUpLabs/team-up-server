from schemas.project import ProjectCreate
from sqlalchemy.orm import Session
import logging
import json
from models.project import Project as ProjectModel
from models.member import Member as MemberModel
from models.task import Task as TaskModel
from crud.task import get_tasks_by_project_id
from crud.member import get_member_by_project_id

def create_project(db: Session, project: ProjectCreate):
    try:
        logging.info("Creating new project")
        project_data = project.dict()

        # Parse JSON fields if needed
        json_fields = ['roles', 'techStack']
        for field in json_fields:
            if field in project_data and isinstance(project_data[field], str):
                project_data[field] = json.loads(project_data[field])

        db_project = ProjectModel(**project_data)
        db.add(db_project)
        db.commit()
        db.refresh(db_project)
        return db_project
    except Exception as e:
        logging.error(f"Error in create_project: {str(e)}")
        db.rollback()
        raise

def get_all_projects(db: Session, skip: int = 0, limit: int = 100):
    projects = db.query(ProjectModel).offset(skip).limit(limit).all()
    for project in projects:
        members = get_member_by_project_id(db, project.id)
        project.members = members
        
        tasks = get_tasks_by_project_id(db, project.id)
        project.tasks = tasks
    return projects

def get_project(db: Session, project_id: str):
    project = db.query(ProjectModel).filter(ProjectModel.id == project_id).first()
    members = db.query(MemberModel).filter(
        MemberModel.projects.contains([project_id])
    ).all()
    
    tasks = db.query(TaskModel).filter(
      TaskModel.project_id == project_id
    ).all()
    
    for task in tasks:
      assignee = []
      for assignee_id in task.assignee_id:
        member = db.query(MemberModel).filter(
          MemberModel.id == assignee_id
        ).first()
        assignee.append(member)
      task.assignee = assignee
    
    project.members = members
    project.tasks = tasks
    return project
  
  
def get_all_projects_excluding_my(db: Session, member_id: int):
  Member = db.query(MemberModel).filter(MemberModel.id == member_id).first()
  other_projects = db.query(ProjectModel).filter(ProjectModel.id.not_in(Member.projects)).all()
  
  for other_project in other_projects:
    members = db.query(MemberModel).filter(
        MemberModel.projects.contains([other_project.id])
    ).all()
    
    other_project.members = members
    
    tasks = db.query(TaskModel).filter(
      TaskModel.project_id == other_project.id
    ).all()
    
    other_project.tasks = tasks
  
  return other_projects
  