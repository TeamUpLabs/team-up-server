from schemas.project import ProjectCreate
from sqlalchemy.orm import Session
import logging
import json
from models.project import Project as ProjectModel
from models.member import Member  # ✅ SQLAlchemy 모델 import

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
        members = db.query(Member).filter(
            Member.projects.contains([project.id])
        ).all()
        project.members = members
    return projects

def get_project(db: Session, project_id: str):
    project = db.query(ProjectModel).filter(ProjectModel.id == project_id).first()
    members = db.query(Member).filter(
        Member.projects.contains([project_id])
    ).all()
    project.members = members
    return project
  
  
def get_all_projects_excluding_my(db: Session, member_id: int):
  member = db.query(Member).filter(Member.id == member_id).first()
  other_projects = (
    db.query(ProjectModel).filter(ProjectModel.id.not_in(member.projects))
  )
  
  return other_projects
  