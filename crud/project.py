from schemas.project import ProjectCreate
from sqlalchemy.orm import Session
import logging
import json
from models.project import Project as ProjectModel
from crud.task import get_tasks_by_project_id
from crud.member import get_member_by_project_id, get_member_by_id
from crud.milestone import get_milestones_by_project_id
from models.member import Member as MemberModel

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
        
        milestones = get_milestones_by_project_id(db, project.id)
        project.milestones = milestones
    return projects

def get_project(db: Session, project_id: str):
    project = db.query(ProjectModel).filter(ProjectModel.id == project_id).first()
    
    members = get_member_by_project_id(db, project_id)
    project.members = members
    
    tasks = get_tasks_by_project_id(db, project_id)
    
    for task in tasks:
      assignee = []
      for assignee_id in task.assignee_id:
        member = get_member_by_id(db, assignee_id)
        assignee.append(member)
      task.assignee = assignee
    project.tasks = tasks
    
    milestones = get_milestones_by_project_id(db, project_id)
    project.milestones = milestones
    return project
  
  
def get_all_projects_excluding_my(db: Session, member_id: int):
  member = get_member_by_id(db, member_id)
  other_projects = db.query(ProjectModel).filter(ProjectModel.id.not_in(member.projects)).all()
  
  for other_project in other_projects:
    members = get_member_by_project_id(db, other_project.id)
    other_project.members = members
    
    tasks = get_tasks_by_project_id(db, other_project.id)
    other_project.tasks = tasks

    milestones = get_milestones_by_project_id(db, other_project.id)
    other_project.milestones = milestones
  return other_projects
  
def add_member_to_project(db: Session, project_id: str, member_id: int):
  try:
    # Get the member
    member = db.query(MemberModel).filter(MemberModel.id == member_id).first()
    if not member:
      return {"status": "error", "message": "Member not found"}
      
    # Get the project
    project = db.query(ProjectModel).filter(ProjectModel.id == project_id).first()
    if not project:
      return {"status": "error", "message": "Project not found"}
    
    # Initialize projects list if it's None
    if member.projects is None:
      member.projects = []
    
    # Check if project_id already exists in member's projects
    if project_id in member.projects:
      return {"status": "error", "message": "Member already in project"}
    
    # Add project_id to member's projects list and ensure it's a proper JSON array
    if isinstance(member.projects, list):
      member.projects.append(project_id)
    else:
      # Convert to list if it's not already a list
      member.projects = [project_id]
    
    # Explicitly update the member object
    db.query(MemberModel).filter(MemberModel.id == member_id).update(
      {"projects": member.projects},
      synchronize_session="fetch"
    )
    
    db.commit()
    db.refresh(member)
    
    return {"status": "success", "message": "Member added to project"}
  except Exception as e:
    logging.error(f"Error in add_member_to_project: {str(e)}")
    db.rollback()
    raise
  