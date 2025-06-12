from schemas.project import ProjectCreate
from sqlalchemy.orm import Session, attributes
import logging
from datetime import datetime
import json
from models.project import Project as ProjectModel
from crud.task import get_tasks_by_project_id, delete_task_by_id
from crud.member import get_member_by_project_id, get_member_by_id
from crud.milestone import get_milestones_by_project_id, delete_milestone_by_id
from crud.schedule import get_schedules, delete_schedule_by_id
from crud.chat import get_chat_by_project_id, delete_chat_by_id
from models.member import Member as MemberModel
from schemas.member import NotificationInfo
from schemas.task import Task as TaskSchema
from schemas.milestone import MileStone as MileStoneSchema
from schemas.project import ProjectInfoUpdate, ProjectMemberPermission, ProjectMemberScout
from models.task import Task as TaskModel
from models.milestone import Milestone as MilestoneModel
from utils.sse_manager import notification_sse_manager, project_sse_manager
import json
from utils.send_notification import send_notification


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
          if project.manager_id and member.id in project.manager_id:
            managers.append(member)
        project.manager = managers
        project.members = members
        
        # Process tasks
        tasks = get_tasks_by_project_id(db, project.id)
        processed_tasks = []
        
        for task in tasks:
            assignee = []
            if task.assignee_id and isinstance(task.assignee_id, list):
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
    
    if project is None:
        return None
    
    # Process members
    members = get_member_by_project_id(db, project_id) or []
    managers = []
    if hasattr(project, 'manager_id') and project.manager_id:
      for manager_id in project.manager_id:
        manager = get_member_by_id(db, manager_id)
        if manager:
          managers.append(manager)
    project.manager = managers
    project.members = members
    
    # Process tasks
    tasks = get_tasks_by_project_id(db, project_id)
    processed_tasks = []
    
    for task in tasks:
      assignee = []
      if task.assignee_id and isinstance(task.assignee_id, list):
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
    try:
      project.leader = leader
    except Exception as e:
      logging.error(e)
      project.leader = None
    
    participationRequestMembers = []
    for member_id in project.participationRequest if project.participationRequest else []:
      member = get_member_by_id(db, member_id)
      if member:
        participationRequestMembers.append(member)
    project.participationRequestMembers = participationRequestMembers
    
    # Process schedules
    schedules = get_schedules(db, project_id)
    project.schedules = schedules
    
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

async def scout_member(db: Session, project_id: str, member_id: int, member_data: ProjectMemberScout):
  project = db.query(ProjectModel).filter(ProjectModel.id == project_id).first()
  if not project:
    return None
  
  sender_member = db.query(MemberModel).filter(MemberModel.id == member_data.sender_id).first()
  if not sender_member:
    return None
  
  receiver_member = db.query(MemberModel).filter(MemberModel.id == member_id).first()
  if not receiver_member and member_data.sender_id != member_id:
    return None
  
  if project.participationRequest is not None and member_id in project.participationRequest:
    return None
  
  await send_notification(
    db=db,
    id=int(datetime.now().timestamp()),
    title="스카우트 요청",
    message=f'"{sender_member.name}" 님이 "{project.title}" 프로젝트에 참여 요청을 보냈습니다.',
    type="scout",
    isRead=False,
    sender_id=sender_member.id,
    receiver_id=receiver_member.id,
    project_id=project_id
  )
  
  return receiver_member
  
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
        "createdAt": project.createdAt,
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
  
import traceback
def delete_project_by_id(db: Session, project_id: str):
    logger = logging.getLogger(__name__)
    logger.info(f"[delete_project_by_id] 함수 진입: project_id={project_id}")
    try:
        project = db.query(ProjectModel).filter(ProjectModel.id == project_id).first()
        logger.debug(f"프로젝트 조회 결과: {project}")
        tasks = get_tasks_by_project_id(db, project_id)
        logger.debug(f"프로젝트의 tasks: {tasks}")
        milestones = get_milestones_by_project_id(db, project_id)
        logger.debug(f"프로젝트의 milestones: {milestones}")
        members = get_member_by_project_id(db, project_id)
        logger.debug(f"프로젝트의 members: {members}")
        schedules = get_schedules(db, project_id)
        logger.debug(f"프로젝트의 schedules: {schedules}")
        chat = get_chat_by_project_id(db, project_id)
        logger.debug(f"프로젝트의 chat: {chat}")

        if project:
            if tasks:
                logger.info(f"tasks 삭제 시작 (개수: {len(tasks)})")
                for task in tasks:
                    logger.debug(f"delete_task_by_id 호출: task_id={task.id}")
                    delete_task_by_id(db, task.id)
            if milestones:
                logger.info(f"milestones 삭제 시작 (개수: {len(milestones)})")
                for milestone in milestones:
                    logger.debug(f"delete_milestone_by_id 호출: milestone_id={milestone.id}")
                    delete_milestone_by_id(db, milestone.id)
            if members:
                logger.info(f"members 업데이트 시작 (개수: {len(members)})")
                for member in members:
                    logger.debug(f"member {member.id}의 projects에서 {project_id} 제거 전: {member.projects}")
                    member.projects = [p_id for p_id in member.projects if p_id != project_id]
                    db.query(MemberModel).filter(MemberModel.id == member.id).update(
                        {"projects": member.projects},
                        synchronize_session="fetch"
                    )
                    logger.debug(f"member {member.id}의 projects 업데이트 후: {member.projects}")
            if schedules:
                logger.info(f"schedules 삭제 시작 (개수: {len(schedules)})")
                for schedule in schedules:
                    logger.debug(f"delete_schedule_by_id 호출: schedule_id={schedule.id}")
                    delete_schedule_by_id(db, schedule.id)
            if chat:
                logger.info(f"chat 메시지 삭제 시작 (개수: {len(chat)})")
                for message in chat:
                    logger.debug(f"delete_chat_by_id 호출: message_id={message.id}")
                    delete_chat_by_id(db, message.id)
            logger.info(f"프로젝트 삭제: {project}")
            db.delete(project)
            db.commit()
            logger.info("프로젝트 및 관련 데이터 삭제 완료")
            return True
        logger.warning(f"project_id={project_id}에 해당하는 프로젝트가 없음")
        return False
    except Exception as e:
        logger.error(f"delete_project_by_id에서 예외 발생: {e}", exc_info=True)
        print(traceback.format_exc())
        db.rollback()
        raise



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


async def send_project_participation_request(db: Session, project_id: str, member_id: int):
  try:
    project = db.query(ProjectModel).filter(ProjectModel.id == project_id).first()
    if not project:
      logging.error(f"Project not found: {project_id} in send_project_participation_request")
      return None
    
    if project.participationRequest is None:
      project.participationRequest = []
    
    if member_id not in project.participationRequest:
      project.participationRequest.append(member_id)
    
    member = db.query(MemberModel).filter(MemberModel.id == member_id).first()
    if not member:
      logging.error(f"Member not found: {member_id} in send_project_participation_request")
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
    
    # Add notification to project leader
    leader = get_member_by_id(db, project.leader_id)
    if leader:
      if not hasattr(leader, 'notification') or leader.notification is None:
        leader.notification = []
      
      # Ensure all existing notifications are dictionaries
      for i, note in enumerate(leader.notification):
        if hasattr(note, 'model_dump'):  # Check if it's a Pydantic model
          leader.notification[i] = note.model_dump()
          
      await send_notification(
        db=db,
        id=int(datetime.now().timestamp()),
        title="참여 요청",
        message=f'"{member.name}" 님이 "{project.title}" 프로젝트에 참여 요청을 보냈습니다.',
        type="project",
        isRead=False,
        sender_id=member_id,
        receiver_id=project.leader_id,
        project_id=project_id
      )
    else:
      logging.error(f"Leader not found for project: {project_id} in send_project_participation_request")
    
    
    # Add notification to managers
    if project.manager_id:
      for manager_id in project.manager_id:
        manager = get_member_by_id(db, manager_id)
        if not manager:
          logging.warning(f"Manager with ID {manager_id} not found in send_project_participation_request")
          continue
        
        if not hasattr(manager, 'notification') or manager.notification is None:
          manager.notification = []
          
        # Ensure all existing notifications are dictionaries
        for i, note in enumerate(manager.notification):
          if hasattr(note, 'model_dump'):  # Check if it's a Pydantic model
            manager.notification[i] = note.model_dump()
          
        await send_notification(
          db=db,
          id=int(datetime.now().timestamp()),
          title="참여 요청",
          message=f'"{member.name}" 님이 "{project.title}" 프로젝트에 참여 요청을 보냈습니다.',
          type="project",
          isRead=False,
          sender_id=member_id,
          receiver_id=manager_id,
          project_id=project_id
        )
        
    project_data = get_project(db, project_id)
    if not project_data:
        logging.error(f"Failed to get project data for project {project_id} after updates in send_project_participation_request")
    else:
        await project_sse_manager.send_event(
          project_id,
          json.dumps(project_sse_manager.convert_to_dict(project_data))
        )
    
    # Serialize subtasks for any dirty MilestoneModel instances before committing
    for instance in db.dirty:
        if isinstance(instance, MilestoneModel):
            history = attributes.get_history(instance, 'subtasks')
            if history.has_changes() and instance.subtasks is not None:
                serializable_subtasks = []
                for subtask_item in instance.subtasks:
                    try:
                        if isinstance(subtask_item, TaskModel):
                            task_schema_instance = TaskSchema.model_validate(subtask_item)
                            serializable_subtasks.append(task_schema_instance.model_dump())
                        elif hasattr(subtask_item, 'model_dump'): # Pydantic model
                            serializable_subtasks.append(subtask_item.model_dump())
                        elif isinstance(subtask_item, dict):
                            serializable_subtasks.append(subtask_item)
                        else:
                            logging.warning(f"Subtask in milestone {instance.id} during pre-commit (send_request) is of unhandled type: {type(subtask_item)}. Attempting str conversion.")
                            serializable_subtasks.append(str(subtask_item))
                    except Exception as e_serialize:
                        logging.error(f"Could not serialize subtask in milestone {instance.id} (send_request). Subtask: {subtask_item}. Error: {e_serialize}", exc_info=True)
                        serializable_subtasks.append(f"Error serializing subtask: {str(subtask_item)[:100]}") # Truncate subtask_item string representation
                instance.subtasks = serializable_subtasks

    db.commit()
    db.refresh(project)
    db.refresh(member)
    return project, member
  except Exception as e:
    logging.error(f"Error in send_project_participation_request for project_id {project_id} and member_id {member_id}: {str(e)}", exc_info=True)
    db.rollback()
    raise
  
async def allow_project_participation_request(db: Session, project_id: str, member_id: int):
  try:
    project = db.query(ProjectModel).filter(ProjectModel.id == project_id).first()
    if not project:
      logging.error(f"Project not found: {project_id} in allow_project_participation_request")
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
    
    await send_notification(
      db=db,
      id=int(datetime.now().timestamp()),
      title="참여 승인",
      message=f'"{project.title}" 프로젝트 참여가 승인되었습니다.',
      type="project",
      isRead=False,
      sender_id=project.leader_id,
      receiver_id=member_id,
      project_id=project_id
    )
    
    project_data = get_project(db, project_id)
    await project_sse_manager.send_event(
      project_id,
      json.dumps(project_sse_manager.convert_to_dict(project_data))
    )

    # Serialize subtasks for any dirty MilestoneModel instances before committing
    for instance in db.dirty:
        if isinstance(instance, MilestoneModel):
            history = attributes.get_history(instance, 'subtasks')
            if history.has_changes() and instance.subtasks is not None:
                serializable_subtasks = []
                for subtask_item in instance.subtasks:
                    try:
                        if isinstance(subtask_item, TaskModel):
                            task_schema_instance = TaskSchema.model_validate(subtask_item)
                            serializable_subtasks.append(task_schema_instance.model_dump())
                        elif hasattr(subtask_item, 'model_dump'): # Pydantic model
                            serializable_subtasks.append(subtask_item.model_dump())
                        elif isinstance(subtask_item, dict):
                            serializable_subtasks.append(subtask_item)
                        else:
                            logging.warning(f"Subtask in milestone {instance.id} during pre-commit (allow_request) is of unhandled type: {type(subtask_item)}. Attempting str conversion.")
                            serializable_subtasks.append(str(subtask_item))
                    except Exception as e_serialize:
                        logging.error(f"Could not serialize subtask in milestone {instance.id} (allow_request). Subtask: {subtask_item}. Error: {e_serialize}", exc_info=True)
                        serializable_subtasks.append(f"Error serializing subtask: {str(subtask_item)[:100]}") # Truncate subtask_item string representation
                instance.subtasks = serializable_subtasks

    db.commit()
    db.refresh(project)
    return project
  except Exception as e:
    logging.error(f"Error in allow_project_participation_request for project_id {project_id} and member_id {member_id}: {str(e)}", exc_info=True)
    db.rollback()
    raise

async def reject_project_participation_request(db: Session, project_id: str, member_id: int):
  try:
    project = db.query(ProjectModel).filter(ProjectModel.id == project_id).first()
    if not project:
      logging.error(f"Project not found: {project_id} in reject_project_participation_request")
      return None
    
    if member_id in project.participationRequest:
      project.participationRequest = [m_id for m_id in project.participationRequest if m_id != member_id]
      db.query(ProjectModel).filter(ProjectModel.id == project_id).update(
        {"participationRequest": project.participationRequest},
        synchronize_session="fetch"
      )
    else:
      logging.warning(f"Member {member_id} not in participation request for project {project_id} in reject_project_participation_request")

    member = db.query(MemberModel).filter(MemberModel.id == member_id).first()
    if not member:
      logging.error(f"Member not found: {member_id} in reject_project_participation_request")
      return None
    
    if project_id in member.participationRequest:
      member.participationRequest = [m_id for m_id in member.participationRequest if m_id != project_id]
      db.query(MemberModel).filter(MemberModel.id == member_id).update(
        {"participationRequest": member.participationRequest},
        synchronize_session="fetch"
      )
    else:
      logging.warning(f"Project {project_id} not in participation request for member {member_id} in reject_project_participation_request")

    await send_notification(
      db=db,
      id=int(datetime.now().timestamp()),
      title="참여 거절",
      message=f'"{project.title}" 프로젝트 참여가 거절되었습니다.',
      type="project",
      isRead=False,
      sender_id=project.leader_id, # Assuming leader_id is not None, add check if necessary
      receiver_id=member_id,
      project_id=project_id
    )
    
    project_data = get_project(db, project_id)
    if not project_data:
      logging.error(f"Failed to get project data for project {project_id} after updates in reject_project_participation_request")
    else:
      await project_sse_manager.send_event(
        project_id,
        json.dumps(project_sse_manager.convert_to_dict(project_data))
      )

    # Serialize subtasks for any dirty MilestoneModel instances before committing
    for instance in db.dirty:
        if isinstance(instance, MilestoneModel):
            history = attributes.get_history(instance, 'subtasks')
            if history.has_changes() and instance.subtasks is not None:
                serializable_subtasks = []
                for subtask_item in instance.subtasks:
                    try:
                        if isinstance(subtask_item, TaskModel):
                            task_schema_instance = TaskSchema.model_validate(subtask_item)
                            serializable_subtasks.append(task_schema_instance.model_dump())
                        elif hasattr(subtask_item, 'model_dump'): # Pydantic model
                            serializable_subtasks.append(subtask_item.model_dump())
                        elif isinstance(subtask_item, dict):
                            serializable_subtasks.append(subtask_item)
                        else:
                            # Ensuring the logging context is clear for kick_out_member
                            logging.warning(f"Subtask in milestone {instance.id} during pre-commit (kick_out_member) is of unhandled type: {type(subtask_item)}. Attempting str conversion.")
                            serializable_subtasks.append(str(subtask_item))
                    except Exception as e_serialize:
                        logging.error(f"Could not serialize subtask in milestone {instance.id} (kick_out_member). Subtask: {subtask_item}. Error: {e_serialize}", exc_info=True)
                        serializable_subtasks.append(f"Error serializing subtask: {str(subtask_item)[:100]}")
                instance.subtasks = serializable_subtasks
    
    db.commit()
    db.refresh(project)
    return project
  except Exception as e:
    logging.error(f"Error in reject_project_participation_request for project_id {project_id} and member_id {member_id}: {str(e)}", exc_info=True)
    db.rollback()
    raise

async def kick_out_member_from_project(db: Session, project_id: str, member_id: int):
  try:
    member = db.query(MemberModel).filter(MemberModel.id == member_id).first()
    if not member:
      return None
    
    # Remove project from member's projects list
    if member.projects is not None:
      member.projects = [p_id for p_id in member.projects if p_id != project_id]
      db.query(MemberModel).filter(MemberModel.id == member_id).update(
        {"projects": member.projects},
        synchronize_session="fetch" 
      )
    
    project = db.query(ProjectModel).filter(ProjectModel.id == project_id).first()
    if not project:
      return None
    
    # Remove member from manager_id list
    if project.manager_id is not None:
      project.manager_id = [m_id for m_id in project.manager_id if m_id != member_id]
      db.query(ProjectModel).filter(ProjectModel.id == project_id).update(
        {"manager_id": project.manager_id},
        synchronize_session="fetch"
      )
    
    # Remove member from participation requests if present
    if project.participationRequest is not None and member_id in project.participationRequest:
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
    tasks = get_tasks_by_project_id(db, project_id) or []
    for task in tasks:
      if task.assignee_id is not None and member_id in task.assignee_id:
        task.assignee_id = [a_id for a_id in task.assignee_id if a_id != member_id]
        db.query(TaskModel).filter(TaskModel.id == task.id).update(
          {"assignee_id": task.assignee_id},
          synchronize_session="fetch"
        )
    
    # Get all milestones for this project and remove member from assignee lists
    milestones = get_milestones_by_project_id(db, project_id) or []
    for milestone in milestones:
      modified = False
      
      # Remove member from assignee list
      if milestone.assignee_id is not None and member_id in milestone.assignee_id:
        milestone.assignee_id = [a_id for a_id in milestone.assignee_id if a_id != member_id]
        modified = True
      
      # Fix serialization issue with subtasks that might contain Task objects
      if milestone.subtasks is not None:
        serializable_subtasks = []
        for subtask_item in milestone.subtasks:
          try:
            if isinstance(subtask_item, TaskModel):
              # Convert ORM TaskModel to TaskSchema Pydantic model, then to dict
              task_schema_instance = TaskSchema.model_validate(subtask_item)
              serializable_subtasks.append(task_schema_instance.model_dump())
            elif hasattr(subtask_item, 'model_dump'): # Already a Pydantic model
              serializable_subtasks.append(subtask_item.model_dump())
            elif isinstance(subtask_item, dict): # Already a dict
              serializable_subtasks.append(subtask_item) # Assume it's serializable
            else:
              logging.warning(f"Subtask in milestone {milestone.id} is of unhandled type: {type(subtask_item)}. Attempting str conversion.")
              serializable_subtasks.append(str(subtask_item))
          except Exception as e_serialize:
            logging.error(f"Could not serialize subtask in milestone {milestone.id}. Subtask: {subtask_item}. Error: {e_serialize}", exc_info=True)
            # Optionally, append a placeholder or skip
            # For now, let's try to append a string representation as a fallback to avoid breaking the whole list.
            serializable_subtasks.append(f"Error serializing subtask: {subtask_item}")

        milestone.subtasks = serializable_subtasks
        modified = True
      
      # Only update the milestone if changes were made
      if modified:
        db.query(MilestoneModel).filter(MilestoneModel.id == milestone.id).update(
          {
            "assignee_id": milestone.assignee_id,
            "subtasks": milestone.subtasks
          },
          synchronize_session="fetch"
        )
      
    await send_notification(
      db=db,
      id=int(datetime.now().timestamp()),
      title="프로젝트 탈퇴",
      message=f'"{project.title}" 프로젝트에서 탈퇴되었습니다.',
      type="project",
      isRead=False,
      sender_id=project.leader_id,
      receiver_id=member_id,
      project_id=project_id
    )
      
    project_data = get_project(db, project_id)
    await project_sse_manager.send_event(
      project_id,
      json.dumps(project_sse_manager.convert_to_dict(project_data))
    )
    
    # Serialize subtasks for any dirty MilestoneModel instances before committing
    for instance in db.dirty:
        if isinstance(instance, MilestoneModel):
            history = attributes.get_history(instance, 'subtasks')
            if history.has_changes() and instance.subtasks is not None:
                serializable_subtasks = []
                for subtask_item in instance.subtasks:
                    try:
                        if isinstance(subtask_item, TaskModel):
                            task_schema_instance = TaskSchema.model_validate(subtask_item)
                            serializable_subtasks.append(task_schema_instance.model_dump())
                        elif hasattr(subtask_item, 'model_dump'): # Pydantic model
                            serializable_subtasks.append(subtask_item.model_dump())
                        elif isinstance(subtask_item, dict):
                            serializable_subtasks.append(subtask_item)
                        else:
                            logging.warning(f"Subtask in milestone {instance.id} during pre-commit (kick_out_member) is of unhandled type: {type(subtask_item)}. Attempting str conversion.")
                            serializable_subtasks.append(str(subtask_item))
                    except Exception as e_serialize:
                        logging.error(f"Could not serialize subtask in milestone {instance.id} (kick_out_member). Subtask: {subtask_item}. Error: {e_serialize}", exc_info=True)
                        serializable_subtasks.append(f"Error serializing subtask: {str(subtask_item)[:100]}")
                instance.subtasks = serializable_subtasks
    
    db.commit()
    db.refresh(project)
    return project
  except Exception as e:
    logging.error(f"Error in kick_out_member_from_project: {str(e)}", exc_info=True)
    db.rollback()
    raise
  