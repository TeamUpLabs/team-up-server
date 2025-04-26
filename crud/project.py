from schemas.project import ProjectCreate, Project
from sqlalchemy.orm import Session
import logging
import json
from models.project import Project as ProjectModel
from crud.task import get_tasks_by_project_id, delete_task_by_id
from crud.member import get_member_by_project_id, get_member_by_id
from crud.milestone import get_milestones_by_project_id, delete_milestone_by_id
from models.member import Member as MemberModel
from schemas.member import Member as MemberSchema
from schemas.task import Task as TaskSchema
from schemas.milestone import MileStone as MileStoneSchema
from schemas.project import ProjectInfoUpdate, ProjectMemberPermission

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
        # Process members
        members = get_member_by_project_id(db, project.id)
        managers = []
        for member in members:
          if member.id in project.manager_id:
            managers.append(member)
        project.manager = managers
        project.members = members
        
        # Process tasks
        tasks = get_tasks_by_project_id(db, project.id)
        processed_tasks = []
        
        for task in tasks:
            assignee = []
            if task.assignee_id:
                for assignee_id in task.assignee_id:
                    member = get_member_by_id(db, assignee_id)
                    if member:
                        assignee.append(member)
            task.assignee = assignee
            # Convert to Pydantic schema
            processed_tasks.append(TaskSchema.model_validate(task.__dict__))
        
        project.tasks = processed_tasks
        
        # Process milestones
        milestones = get_milestones_by_project_id(db, project.id)
        processed_milestones = []
        
        for milestone in milestones:
            # Convert to Pydantic schema
            processed_milestones.append(MileStoneSchema.model_validate(milestone.__dict__))
            
        leader = get_member_by_id(db, project.leader_id)
        project.leader = leader
        
        project.milestones = processed_milestones
    
    return projects

def get_project(db: Session, project_id: str):
    project = db.query(ProjectModel).filter(ProjectModel.id == project_id).first()
    if not project:
        return None
    
    # Process members
    members = get_member_by_project_id(db, project_id)
    managers = []
    for member in members:
      if member.id in project.manager_id:
        managers.append(member)
    project.manager = managers
    project.members = members
    
    # Process tasks
    tasks = get_tasks_by_project_id(db, project_id)
    processed_tasks = []
    
    for task in tasks:
      assignee = []
      if task.assignee_id:
        for assignee_id in task.assignee_id:
          member = get_member_by_id(db, assignee_id)
          if member:
            assignee.append(member)
      task.assignee = assignee
      # Convert to Pydantic schema
      processed_tasks.append(TaskSchema.model_validate(task.__dict__))
    
    project.tasks = processed_tasks
    
    # Process milestones
    milestones = get_milestones_by_project_id(db, project_id)
    processed_milestones = []
    
    for milestone in milestones:
      # Convert to Pydantic schema
      processed_milestones.append(MileStoneSchema.model_validate(milestone.__dict__))
    
    project.milestones = processed_milestones
    
    leader = get_member_by_id(db, project.leader_id)
    project.leader = leader
    
    participationRequestMembers = []
    for member_id in project.participationRequest:
      member = get_member_by_id(db, member_id)
      if member:
        participationRequestMembers.append(member)
    project.participationRequestMembers = participationRequestMembers
    
    return project
  
  
def get_all_projects_excluding_my(db: Session, member_id: int):
  member = get_member_by_id(db, member_id)
  
  # Handle the case where member.projects is None
  projects_to_exclude = member.projects if member.projects is not None else []
  
  other_projects = db.query(ProjectModel).filter(ProjectModel.id.not_in(projects_to_exclude)).all()
  
  for other_project in other_projects:
    # Process members
    members = get_member_by_project_id(db, other_project.id)
    managers = []
    for project_member in members:
      if project_member.id in other_project.manager_id:
        managers.append(project_member)
    other_project.manager = managers
    other_project.members = members
    
    participationRequestMembers = []
    for req_member_id in other_project.participationRequest if other_project.participationRequest else []:
      req_member = get_member_by_id(db, req_member_id)
      if req_member:
        participationRequestMembers.append(req_member)
    other_project.participationRequestMembers = participationRequestMembers
    
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
  
def get_project_basic_info(db: Session, project_id: str):
    """
    Get basic project information without loading tasks or milestones
    to avoid circular references, but including basic member information
    """
    from schemas.project import Project as ProjectSchema
    from models.member import Member as MemberModel
    from schemas.member import Member as MemberSchema
    
    project = db.query(ProjectModel).filter(ProjectModel.id == project_id).first()
    if not project:
        return None
    
    # Directly query the database for members associated with this project
    # This avoids using get_member_by_project_id which may cause circular references
    members_query = db.query(MemberModel).filter(
        MemberModel.projects.contains([project_id])
    ).all()
    
    # Build a list of member objects that satisfy the schema requirements
    member_list = []
    if members_query:
        for member in members_query:
            if member:
                # Create a complete member object with all required fields
                member_dict = {
                    "id": member.id,
                    "name": member.name,
                    "email": member.email,
                    "role": member.role,
                    "status": member.status,
                    "contactNumber": member.contactNumber,
                    "workingHours": member.workingHours,
                    # Include other required fields with defaults if needed
                    "password": None,  # Optional field
                    "skills": member.skills or [],
                    "projects": member.projects or [],
                    "profileImage": member.profileImage,
                    "birthDate": member.birthDate,
                    "introduction": member.introduction,
                    "languages": member.languages or [],
                    "socialLinks": member.socialLinks or [],
                    "lastLogin": member.lastLogin,
                    "createdAt": member.createdAt,
                    # Empty lists for related entities to prevent circular references
                    "currentTask": [],
                    "projectDetails": []
                }
                # Convert to Pydantic model to ensure it matches the schema
                member_obj = MemberSchema.model_validate(member_dict)
                member_list.append(member_obj)
    
    # Create a simple dict with just the basic project info
    basic_info = {
        "id": project.id,
        "title": project.title,
        "description": project.description,
        "status": project.status,
        "roles": project.roles or [],
        "techStack": project.techStack or [],
        "startDate": project.startDate,
        "endDate": project.endDate,
        "teamSize": project.teamSize,
        "location": project.location,
        "projectType": project.projectType,
        # Include properly formatted members
        "members": member_list,
        "tasks": [],
        "milestones": []
    }
    
    return ProjectSchema.model_validate(basic_info)
  
  
def get_all_project_ids(db: Session):
  projects = db.query(ProjectModel).all()
  
  project_ids = []
  for project in projects:
    project_ids.append(project.id)
    
  return project_ids
  
  
def delete_project_by_id(db: Session, project_id: str):
  project = db.query(ProjectModel).filter(ProjectModel.id == project_id).first()
  tasks = get_tasks_by_project_id(db, project_id)
  milestones = get_milestones_by_project_id(db, project_id)
  members = get_member_by_project_id(db, project_id)
  if project:
    for task in tasks:
      delete_task_by_id(db, task.id)
    for milestone in milestones:
      delete_milestone_by_id(db, milestone.id)
    for member in members:
      member.projects = [p_id for p_id in member.projects if p_id != project_id]
      db.query(MemberModel).filter(MemberModel.id == member.id).update(
        {"projects": member.projects},
        synchronize_session="fetch"
      )
    db.delete(project)
    db.commit()
    return True
  return False


def update_project_by_id(db: Session, project_id: str, project_update: ProjectInfoUpdate):
  project = db.query(ProjectModel).filter(ProjectModel.id == project_id).first()
  if not project:
    return None
  
  project_data = project_update.dict(exclude_unset=True, exclude_none=True)
  for field, value in project_data.items():
    setattr(project, field, value) 
  
  db.commit()
  db.refresh(project)
  return project

def update_project_member_permission(db: Session, project_id: str, member_id: int, permission: ProjectMemberPermission):
  project = db.query(ProjectModel).filter(ProjectModel.id == project_id).first()
  if not project:
    return None
  
  if permission.permission == "manager":
    # Initialize manager_id if it's None
    if project.manager_id is None:
      project.manager_id = []
    
    # Only add if not already in the list
    if member_id not in project.manager_id:
      project.manager_id.append(member_id)
      # Explicitly mark as modified for SQLAlchemy to detect change
      db.query(ProjectModel).filter(ProjectModel.id == project_id).update(
        {"manager_id": project.manager_id},
        synchronize_session="fetch"
      )
  elif permission.permission == "member":
    if project.manager_id is not None:
      project.manager_id = [m_id for m_id in project.manager_id if m_id != member_id]
      # Explicitly mark as modified
      db.query(ProjectModel).filter(ProjectModel.id == project_id).update(
        {"manager_id": project.manager_id},
        synchronize_session="fetch"
      )
  else:
    return None
  
  db.commit()
  db.refresh(project)
  return project


def send_project_participation_request(db: Session, project_id: str, member_id: int):
  project = db.query(ProjectModel).filter(ProjectModel.id == project_id).first()
  if not project:
    return None
  
  if project.participationRequest is None:
    project.participationRequest = []
  
  if member_id not in project.participationRequest:
    project.participationRequest.append(member_id)
  
  member = db.query(MemberModel).filter(MemberModel.id == member_id).first()
  if not member:
    return None
  if member.participationRequest is None:
    member.participationRequest = []
    
  if project_id not in member.participationRequest:
    member.participationRequest.append(project_id)
  db.query(MemberModel).filter(MemberModel.id == member_id).update(
    {"participationRequest": member.participationRequest},
    synchronize_session="fetch"
  )
  
  db.query(ProjectModel).filter(ProjectModel.id == project_id).update(
    {"participationRequest": project.participationRequest},
    synchronize_session="fetch"
  )
  
  db.commit()
  db.refresh(project)
  db.refresh(member)
  return project, member
  
def allow_project_participation_request(db: Session, project_id: str, member_id: int):
  project = db.query(ProjectModel).filter(ProjectModel.id == project_id).first()
  if not project:
    return None
  
  if member_id in project.participationRequest:
    project.participationRequest = [m_id for m_id in project.participationRequest if m_id != member_id]
    
    add_member_to_project(db, project_id, member_id)
    db.query(ProjectModel).filter(ProjectModel.id == project_id).update(
      {"participationRequest": project.participationRequest},
      synchronize_session="fetch"
    )
  
  member = db.query(MemberModel).filter(MemberModel.id == member_id).first()
  if not member:
    return None
  
  if project_id in member.participationRequest:
    member.participationRequest = [m_id for m_id in member.participationRequest if m_id != project_id]
  db.query(MemberModel).filter(MemberModel.id == member_id).update(
    {"participationRequest": member.participationRequest},
    synchronize_session="fetch"
  )
  
  db.commit()
  db.refresh(project)
  db.refresh(member)
  return project, member

def reject_project_participation_request(db: Session, project_id: str, member_id: int):
  project = db.query(ProjectModel).filter(ProjectModel.id == project_id).first()
  if not project:
    return None
  
  if member_id in project.participationRequest:
    project.participationRequest = [m_id for m_id in project.participationRequest if m_id != member_id]
    db.query(ProjectModel).filter(ProjectModel.id == project_id).update(
      {"participationRequest": project.participationRequest},
      synchronize_session="fetch"
    )
  
  member = db.query(MemberModel).filter(MemberModel.id == member_id).first()
  if not member:
    return None
  
  if project_id in member.participationRequest:
    member.participationRequest = [m_id for m_id in member.participationRequest if m_id != project_id]
  db.query(MemberModel).filter(MemberModel.id == member_id).update(
    {"participationRequest": member.participationRequest},
    synchronize_session="fetch"
  )
  
  db.commit()
  db.refresh(project)
  db.refresh(member)
  return project, member

def kick_out_member_from_project(db: Session, project_id: str, member_id: int):
  member = db.query(MemberModel).filter(MemberModel.id == member_id).first()
  if not member:
    return None
  
  # Remove project from member's projects list
  member.projects = [p_id for p_id in member.projects if p_id != project_id]
  db.query(MemberModel).filter(MemberModel.id == member_id).update(
    {"projects": member.projects},
    synchronize_session="fetch" 
  )
  
  project = db.query(ProjectModel).filter(ProjectModel.id == project_id).first()
  if not project:
    return None
  
  # Remove member from manager_id list
  if project.manager_id:
    project.manager_id = [m_id for m_id in project.manager_id if m_id != member_id]
    db.query(ProjectModel).filter(ProjectModel.id == project_id).update(
      {"manager_id": project.manager_id},
      synchronize_session="fetch"
    )
  
  # Remove member from participation requests if present
  if project.participationRequest and member_id in project.participationRequest:
    project.participationRequest = [m_id for m_id in project.participationRequest if m_id != member_id]
    db.query(ProjectModel).filter(ProjectModel.id == project_id).update(
      {"participationRequest": project.participationRequest},
      synchronize_session="fetch"
    )
  
  # Remove member from leader position if they are the leader
  if project.leader_id == member_id:
    project.leader_id = None
    db.query(ProjectModel).filter(ProjectModel.id == project_id).update(
      {"leader_id": None},
      synchronize_session="fetch"
    )
  
  # Get all tasks for this project and remove member from assignee lists
  tasks = get_tasks_by_project_id(db, project_id)
  for task in tasks:
    if task.assignee_id and member_id in task.assignee_id:
      task.assignee_id = [a_id for a_id in task.assignee_id if a_id != member_id]
      db.query(task.__class__).filter(task.__class__.id == task.id).update(
        {"assignee_id": task.assignee_id},
        synchronize_session="fetch"
      )
  
  # Get all milestones for this project and remove member from assignee lists
  milestones = get_milestones_by_project_id(db, project_id)
  for milestone in milestones:
    if milestone.assignee_id and member_id in milestone.assignee_id:
      milestone.assignee_id = [a_id for a_id in milestone.assignee_id if a_id != member_id]
      db.query(milestone.__class__).filter(milestone.__class__.id == milestone.id).update(
        {"assignee_id": milestone.assignee_id},
        synchronize_session="fetch"
      )
  
  db.commit()
  db.refresh(member)
  db.refresh(project)
  return member, project
  