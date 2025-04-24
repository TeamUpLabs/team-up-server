import logging
import json
from sqlalchemy.orm import Session
from models.member import Member as MemberModel
from schemas.member import MemberCreate, Member, MemberUpdate
from auth import get_password_hash

def create_member(db: Session, member: MemberCreate):
    try:
        logging.info("Creating new member")
        member_data = member.dict()
        member_data["password"] = get_password_hash(member.password)
        
        # Ensure JSON fields are properly handled
        json_fields = ['skills', 'projects', 'workingHours', 'languages', 'socialLinks']
        for field in json_fields:
            if field in member_data and member_data[field] is not None:
                if isinstance(member_data[field], str):
                    member_data[field] = json.loads(member_data[field])
        
        db_member = MemberModel(**member_data)
        db.add(db_member)
        db.commit()
        db.refresh(db_member)
        return Member.model_validate(db_member)
    except Exception as e:
        logging.error(f"Error in create_member: {str(e)}")
        db.rollback()
        raise

def get_member(db: Session, member_id: int):
  member = db.query(MemberModel).filter(MemberModel.id == member_id).first()
  if not member:
    return None
  from crud.task import get_tasks_by_member_id
  tasks = get_tasks_by_member_id(db, member_id)
  member.currentTask = tasks

  project_ids = db.query(MemberModel).filter(MemberModel.id == member_id).first().projects
  project_list = []
  from crud.project import get_project_basic_info
  if project_ids:
    for project_id in project_ids:
      project = get_project_basic_info(db, project_id)
      if project:
        project_list.append(project)
  member.projectDetails = project_list
  return Member.model_validate(member.__dict__)

def get_member_by_email(db: Session, email: str):
    member = db.query(MemberModel).filter(MemberModel.email == email).first()
    if member:
        from crud.task import get_tasks_by_member_id
        tasks = get_tasks_by_member_id(db, member.id)
        member.currentTask = tasks
        
        # Add project details
        project_ids = member.projects
        project_list = []
        from crud.project import get_project_basic_info
        if project_ids:
            for project_id in project_ids:
                project = get_project_basic_info(db, project_id)
                if project:
                    project_list.append(project)
        member.projectDetails = project_list
        
        return Member.model_validate(member.__dict__)
    return None

def get_members(db: Session, skip: int = 0, limit: int = 100):
    members = db.query(MemberModel).offset(skip).limit(limit).all()
    from crud.task import get_tasks_by_member_id
    from crud.project import get_project_basic_info
    result = []
    
    for member in members:
        tasks = get_tasks_by_member_id(db, member.id)
        member.currentTask = tasks
        
        # Add project details
        project_ids = member.projects
        project_list = []
        if project_ids:
            for project_id in project_ids:
                project = get_project_basic_info(db, project_id)
                if project:
                    project_list.append(project)
        member.projectDetails = project_list
        
        result.append(Member.model_validate(member.__dict__))
    
    return result
  
def get_member_projects(db: Session, member_id: int):
    try:
      from crud.project import get_project_basic_info
      member = db.query(MemberModel).filter(MemberModel.id == member_id).first()
      if member:
          projects = member.projects
          project_list = []
          if projects:
            for project_id in projects:
              project = get_project_basic_info(db, project_id)
              if project:
                project_list.append(project)
          return project_list
      else:
          return None
    except Exception as e:
        logging.error(f"Error in get_member_projects: {str(e)}")
        raise
      
def get_member_by_project_id(db: Session, project_id: str):
  try:
    members = db.query(MemberModel).filter(
      MemberModel.projects.contains([project_id])
    ).all()
    from crud.task import get_tasks_by_member_id
    from crud.project import get_project_basic_info
    result = []
    
    for member in members:
        tasks = get_tasks_by_member_id(db, member.id)
        member.currentTask = tasks
        
        # Add project details
        project_ids = member.projects
        project_list = []
        if project_ids:
            for pid in project_ids:
                project = get_project_basic_info(db, pid)
                if project:
                    project_list.append(project)
        member.projectDetails = project_list
        
        result.append(Member.model_validate(member.__dict__))
    
    return result
  except Exception as e:
    logging.error(e)
    
def get_member_by_id(db: Session, member_id: int):
    member = db.query(MemberModel).filter(MemberModel.id == member_id).first()
    if member:
        return Member.model_validate(member.__dict__)
    return None
  
  
def update_member_by_id(db: Session, member_id: int, member_update: MemberUpdate):
  member = db.query(MemberModel).filter(MemberModel.id == member_id).first()
  if not member:
    return None
  
  member_data = member_update.dict(exclude_unset=True, exclude_none=True)
  for field, value in member_data.items():
    setattr(member, field, value)
  
  db.commit()
  db.refresh(member)
  return member
  