from fastapi import FastAPI, WebSocket, Depends, WebSocketDisconnect, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import logging
from database import SessionLocal, engine, Base
from websocket.chat import websocket_handler
from typing import List, Dict, Any
from auth import create_access_token, verify_password, get_current_user
import schemas.login
from schemas.chat import ChatCreate
from schemas.login import LoginForm
# Import models and schemas in the correct order to avoid circular reference issues
from schemas.member import MemberCreate, Member, MemberCheck, MemberUpdate
from schemas.task import TaskCreate, Task, TaskStatusUpdate, TaskUpdate, Comment, UpdateSubTaskState
from schemas.project import Project, ProjectCreate, ProjectMemberAdd, ProjectInfoUpdate, ProjectMemberPermission
from schemas.milestone import MileStone, MileStoneCreate, MileStoneUpdate
import json
# Then import the CRUD modules
from crud.chat import *
from crud.project import *
from crud.member import *
from crud.task import *
from crud.milestone import *

# Add this for WebRTC signaling
active_connections: Dict[str, Dict[str, Dict[str, WebSocket]]] = {}


Base.metadata.create_all(bind=engine)
app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*", "Authorization"],
)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@app.websocket("/ws/chat/{projectId}/{channelId}")
async def chat_endpoint(websocket: WebSocket, projectId: str, channelId: str):
    try:
        logging.info(f"WebSocket connection established for project: {projectId}, channel: {channelId}")
        await websocket_handler(websocket, channelId, projectId)
    except WebSocketDisconnect:
        logging.info(f"WebSocket disconnected for project: {projectId}, channel: {channelId}")
    except Exception as e:
        logging.error(f"WebSocket error in project {projectId}, channel {channelId}: {str(e)}")
        try:
            await websocket.close()
        except:
            pass

@app.post("/chat")
def post_message(chat: ChatCreate, db: SessionLocal = Depends(get_db)): # type: ignore
    return save_chat_message(db, chat)


@app.get("/chat/{projectId}/{channelId}")
def get_messages(projectId: str, channelId: str, db: SessionLocal = Depends(get_db)): # type: ignore
    return get_chat_history(db, projectId, channelId)
  
@app.post("/member", response_model=Member)
def handle_create_member(member: MemberCreate, db: SessionLocal = Depends(get_db)): # type: ignore
    try:
        logging.info(f"Creating new member with email: {member.email}")
        existing_member = get_member_by_email(db, member.email)
        if existing_member:
            logging.warning(f"Email already exists: {member.email}")
            raise HTTPException(status_code=400, detail="Email already registered")
        
        db_member = create_member(db, member)
        logging.info(f"Successfully created member with id: {db_member.id}")
        return db_member
    except HTTPException as he:
        logging.error(f"HTTP Exception during member creation: {str(he)}")
        raise
    except Exception as e:
        logging.error(f"Unexpected error during member creation: {str(e)}")
        db.rollback()  # 트랜잭션 롤백
        raise HTTPException(
            status_code=500,
            detail="Internal server error occurred while creating member"
        )
        
@app.post("/member/check")
def check_member(member_check: MemberCheck, db: SessionLocal = Depends(get_db)): # type: ignore
    try:
        member = get_member_by_email(db, member_check.email)
        if member:
            return {"status": "exists", "message": "Member already exists"}
        else:
            return {"status": "not_exists", "message": "Member does not exist"}
    except Exception as e:
        logging.error(f"Unexpected error during member check: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/member", response_model=List[Member])
def read_members(skip: int = 0, limit: int = 100, db: SessionLocal = Depends(get_db)): # type: ignore
    try:
        members = get_members(db, skip=skip, limit=limit)
        return members
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/member/{member_id}", response_model=Member)
def read_member(member_id: int, db: SessionLocal = Depends(get_db)): # type: ignore
    try:
        member = get_member(db, member_id)
        if member is None:
            raise HTTPException(status_code=404, detail=f"Member {member_id} not found")
        return member
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
      
@app.get("/member/{member_id}/project", response_model=List[Project])
def read_member_projects(member_id: int, db: SessionLocal = Depends(get_db)): # type: ignore
    try:
        return get_member_projects(db, member_id)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
      
@app.put("/member/{member_id}")
def update_member(member_id: int, member_update: MemberUpdate, db: SessionLocal = Depends(get_db)): # type: ignore
  try:
    updated_member = update_member_by_id(db, member_id, member_update)
    return updated_member
  except Exception as e:
    raise HTTPException(status_code=500, detail=str(e))
      
      
@app.post('/login', response_model=schemas.login.Token)
def login(login: LoginForm, db: SessionLocal = Depends(get_db)): # type: ignore
    member = get_member_by_email(db, login.userEmail)
    if not member:
        raise HTTPException(
            status_code=401,
            detail="이메일이나 비밀번호가 올바르지 않습니다"
        )
    
    if not verify_password(login.password, member.password):
        raise HTTPException(
            status_code=401,
            detail="이메일이나 비밀번호가 올바르지 않습니다"
        )

    # Convert SQLAlchemy model to dict for JWT token
    member_data = {
        "id": member.id,
        "name": member.name,
        "email": member.email,
        "role": member.role,
        "status": member.status,
        "lastLogin": member.lastLogin,
        "createdAt": member.createdAt,
        "skills": member.skills,
        "projects": member.projects,
        "profileImage": member.profileImage,
        "contactNumber": member.contactNumber,
        "birthDate": member.birthDate,
        "introduction": member.introduction,
        "workingHours": member.workingHours,
        "languages": member.languages,
        "socialLinks": member.socialLinks
    }
    
    access_token = create_access_token(
        data={
            "sub": member.email,
            "user_info": member_data
        }
    )
    
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user_id": member.id,
        "user_name": member.name,
        "user_email": member.email
    }
    
@app.get("/me", response_model=Member)
def get_me(current_user: dict = Depends(get_current_user)):
    return current_user
  
  
@app.post("/project")
def create_project_route(project: ProjectCreate, db: SessionLocal = Depends(get_db)): # type: ignore
    return create_project(db, project)
  
  
@app.get("/project", response_model=List[Project])
def read_projects(skip: int = 0, limit: int = 100, db: SessionLocal = Depends(get_db)): # type: ignore
    try:
        projects = get_all_projects(db, skip=skip, limit=limit)
        return projects
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
      
@app.get("/project/id", response_model=List[str])
def read_all_projects_ids(db: SessionLocal = Depends(get_db)): # type: ignore
  try:
    project_ids = get_all_project_ids(db)
    return project_ids
  except Exception as e:
    raise HTTPException(status_code=500, detail=str(e))
      
  
@app.get("/project/{project_id}", response_model=Project)
def read_project_endpoint(project_id: str, db: SessionLocal = Depends(get_db)): # type: ignore
    try:
        project = get_project(db, project_id)
        if project is None:
            raise HTTPException(status_code=404, detail=f"Project {project_id} not found")
        return project
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
      

@app.get("/project/{project_id}/member", response_model=List[Member])
def read_member_by_project_id(project_id: str, db: SessionLocal = Depends(get_db)): # type: ignore
  try:
    members = get_member_by_project_id(db, project_id)
    return members
  except Exception as e:
    logging.error(e)
    return []
      

@app.get("/project/exclude/{member_id}", response_model=List[Project])
def get_projects_excluding_my_project(member_id: int, db: SessionLocal = Depends(get_db)): # type: ignore
  try:
    other_projects = get_all_projects_excluding_my(db, member_id)
    if other_projects is None:
      raise HTTPException(status_code=404, detail=f"Projects not found")
    return other_projects
  except HTTPException:
    raise
  except Exception as e:
    raise HTTPException(status_code=500, detail=str(e))
  
@app.delete("/project/{project_id}")
def delete_project(project_id: str, db: SessionLocal = Depends(get_db)): # type: ignore
  try:
    delete_project_by_id(db, project_id)
    return {"status": "success", "message": "Project deleted successfully"}
  except Exception as e:
    raise HTTPException(status_code=500, detail=str(e))
  
@app.put("/project/{project_id}")
def update_project(project_id: str, project: ProjectInfoUpdate, db: SessionLocal = Depends(get_db)): # type: ignore
  try:
    updated_project = update_project_by_id(db, project_id, project)
    return updated_project
  except Exception as e:
    raise HTTPException(status_code=500, detail=str(e))
  
@app.put("/project/{project_id}/member/{member_id}/permission")
def update_project_member_permission_endpoint(project_id: str, member_id: int, permission: ProjectMemberPermission, db: SessionLocal = Depends(get_db)): # type: ignore
  try:
    updated_project = update_project_member_permission(db, project_id, member_id, permission)
    return updated_project
  except Exception as e:
    raise HTTPException(status_code=500, detail=str(e))
  
@app.put("/project/{project_id}/member/{member_id}/kick")
def kick_out_member_from_project_endpoint(project_id: str, member_id: int, db: SessionLocal = Depends(get_db)): # type: ignore
  try:
    return kick_out_member_from_project(db, project_id, member_id)
  except Exception as e:
    raise HTTPException(status_code=500, detail=str(e))
  
@app.post("/task", response_model=Task)
def handle_create_task(task: TaskCreate, db: SessionLocal = Depends(get_db)): # type: ignore
    try:
        db_task = create_task(db, task)
        logging.info(f"Successfully created task with id: {db_task}")
        return db_task
    except HTTPException as he:
        logging.error(f"HTTP Exception during task creation: {str(he)}")
        raise
    except Exception as e:
        logging.error(f"Unexpected error during task creation: {str(e)}")
        db.rollback()  # 트랜잭션 롤백
        raise HTTPException(
            status_code=500,
            detail="Internal server error occurred while creating task"
        )
        
@app.get('/task', response_model=List[Task])
def get_all_tasks(skip: int = 0, limit: int = 100, db: SessionLocal = Depends(get_db)): # type: ignore
  try:
    tasks = get_tasks(db, skip=skip, limit=limit)
    return tasks
  except Exception as e:
    raise HTTPException(status_code=500, detail=str(e))
  
  
@app.get('/member/{member_id}/task', response_model=List[Task])
def get_all_tasks_by_member_id(member_id: int, db: SessionLocal = Depends(get_db)): # type: ignore
  tasks = get_tasks_by_member_id(db, member_id)
  return tasks
  
@app.get('/project/{project_id}/task', response_model=List[Task])
def get_all_tasks_by_project_id(project_id: str, db: SessionLocal = Depends(get_db)): # type: ignore
  tasks = get_tasks_by_project_id(db, project_id)
  return tasks

@app.put('/project/{project_id}/participationRequest/{member_id}/send')
def send_project_participation_request_endpoint(project_id: str, member_id: int, db: SessionLocal = Depends(get_db)): # type: ignore
  try:
    return send_project_participation_request(db, project_id, member_id)
  except Exception as e:
    raise HTTPException(status_code=500, detail=str(e))

@app.put('/project/{project_id}/participationRequest/{member_id}/allow')
def allow_project_participation_request_endpoint(project_id: str, member_id: int, db: SessionLocal = Depends(get_db)): # type: ignore
  try:
    return allow_project_participation_request(db, project_id, member_id)
  except Exception as e:
    raise HTTPException(status_code=500, detail=str(e))

@app.put('/project/{project_id}/participationRequest/{member_id}/reject')
def reject_project_participation_request_endpoint(project_id: str, member_id: int, db: SessionLocal = Depends(get_db)): # type: ignore
  try:
    return reject_project_participation_request(db, project_id, member_id)
  except Exception as e:
    raise HTTPException(status_code=500, detail=str(e))


@app.delete('/task/{task_id}')
def delete_task(task_id: int, db: SessionLocal = Depends(get_db)): # type: ignore
  try:
    delete_task_by_id(db, task_id)
    return {"status": "success", "message": "Task deleted successfully"}
  except Exception as e:
    raise HTTPException(status_code=500, detail=str(e))
  
@app.put('/project/{project_id}/task/{task_id}/status')
def update_task_status_endpoint(project_id: str, task_id: int, status: TaskStatusUpdate, db: SessionLocal = Depends(get_db)): # type: ignore
  try:
    update_task_status(db, project_id, task_id, status)
    return {"status": "success", "message": "Task status updated successfully"}
  except Exception as e:
    raise HTTPException(status_code=500, detail=str(e))
  
@app.put('/project/{project_id}/task/{task_id}')
def update_task_endpoint(project_id: str, task_id: int, task: TaskUpdate, db: SessionLocal = Depends(get_db)): # type: ignore
  try:
    updated_task = update_task_by_id(db, project_id, task_id, task)
    return updated_task
  except Exception as e:
    raise HTTPException(status_code=500, detail=str(e))
  
@app.post('/project/{project_id}/task/{task_id}/comment')
def upload_task_comment_endpoint(project_id: str, task_id: int, comment: Comment, db: SessionLocal = Depends(get_db)): # type: ignore
  try:
    updated_task = upload_task_comment(db, project_id, task_id, comment)
    return updated_task
  except Exception as e:
    raise HTTPException(status_code=500, detail=str(e))

@app.put('/project/{project_id}/task/{task_id}/subtask/{subtask_id}/state')
def update_subtask_state_endpoint(project_id: str, task_id: int, subtask_id: int, subtask_update: UpdateSubTaskState, db: SessionLocal = Depends(get_db)): # type: ignore
  try:
    updated_task = update_subtask_state_by_id(db, project_id, task_id, subtask_id, subtask_update)
    return updated_task
  except Exception as e:
    raise HTTPException(status_code=500, detail=str(e))

@app.post('/milestone', response_model=MileStone)
def handle_create_milestone(milestone: MileStoneCreate, db: SessionLocal = Depends(get_db)): # type: ignore
  try:
    db_milestone = create_milestone(db, milestone)
    logging.info(f"Successfully created milestone with id: {db_milestone}")
    return db_milestone
  except HTTPException as he:
    logging.error(f"HTTP Exception during milestone creation: {str(he)}")
    raise
  except Exception as e:
    logging.error(f"Unexpected error during milestone creation: {str(e)}")
    db.rollback()  # 트랜잭션 롤백
    raise HTTPException(
        status_code=500,
        detail="Internal server error occurred while creating milestone"
    )
    
@app.get('/milestone', response_model=List[MileStone])
def get_all_milestones(skip: int = 0, limit: int = 100, db: SessionLocal = Depends(get_db)): # type: ignore
  try:
    milestones = get_milestones(db, skip=skip, limit=limit)
    return milestones
  except Exception as e:
    raise HTTPException(status_code=500, detail=str(e))
  
@app.get('/project/{project_id}/milestone', response_model=List[MileStone])
def get_all_milestones_by_project_id(project_id: str, db: SessionLocal = Depends(get_db)): # type: ignore
  try:
    milestones = get_milestones_by_project_id(db, project_id)
    return milestones
  except Exception as e:
    raise HTTPException(status_code=500, detail=str(e))
  
@app.delete("/milestone/{milestone_id}")
def delete_milestone(milestone_id: int, db: SessionLocal = Depends(get_db)): # type: ignore
  try:
    delete_milestone_by_id(db, milestone_id)
    return {"status": "success", "message": "Milestone deleted successfully"}
  except Exception as e:
    raise HTTPException(status_code=500, detail=str(e))
  
@app.put("/project/{project_id}/milestone/{milestone_id}")
def update_milestone_endpoint(project_id: str, milestone_id: int, milestone: MileStoneUpdate, db: SessionLocal = Depends(get_db)): # type: ignore
  try:
    updated_milestone = update_milestone_by_id(db, project_id, milestone_id, milestone)
    return updated_milestone
  except Exception as e:
    raise HTTPException(status_code=500, detail=str(e))
    
@app.post("/project/{project_id}/member")
def add_member_to_project_route(project_id: str, member_data: ProjectMemberAdd, db: SessionLocal = Depends(get_db)): # type: ignore
    try:
        result = add_member_to_project(db, project_id, member_data.member_id)
        if result.get("status") == "error":
            raise HTTPException(status_code=400, detail=result.get("message"))
        return result
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    
# WebRTC signaling endpoints
@app.websocket("/project/{project_id}/ws/call/{channelId}/{userId}")
async def video_call_signaling(websocket: WebSocket, project_id: str, channelId: str, userId: str):
    await websocket.accept()
    
    # Store connection with project_id separation
    if project_id not in active_connections:
        active_connections[project_id] = {}
    if channelId not in active_connections[project_id]:
        active_connections[project_id][channelId] = {}
    active_connections[project_id][channelId][userId] = websocket
    
    try:
        # Notify others about new user joining
        join_message = {
            "type": "user-joined",
            "userId": userId
        }
        
        for user_id, conn in active_connections[project_id][channelId].items():
            if user_id != userId:
                await conn.send_text(json.dumps(join_message))
        
        # Listen for messages
        while True:
            message = await websocket.receive_text()
            data = json.loads(message)
            
            # Handle different signal types
            if data["type"] == "offer" or data["type"] == "answer" or data["type"] == "ice-candidate":
                # Forward to the specific recipient
                target_id = data.get("target")
                if target_id and target_id in active_connections[project_id][channelId]:
                    await active_connections[project_id][channelId][target_id].send_text(message)
            
            elif data["type"] == "disconnect":
                # Notify others about user disconnecting
                break
    
    except WebSocketDisconnect:
        logging.info(f"WebSocket disconnected for project: {project_id}, channel: {channelId}, user: {userId}")
    except Exception as e:
        logging.error(f"WebSocket error in video call: {str(e)}")
    finally:
        # Remove connection on disconnect
        if project_id in active_connections and channelId in active_connections[project_id] and userId in active_connections[project_id][channelId]:
            del active_connections[project_id][channelId][userId]
            
            # Notify others about user leaving
            leave_message = {
                "type": "user-left",
                "userId": userId
            }
            
            if project_id in active_connections and channelId in active_connections[project_id]:
                for user_id, conn in active_connections[project_id][channelId].items():
                    try:
                        await conn.send_text(json.dumps(leave_message))
                    except:
                        pass
                    
                # Clean up empty channels
                if not active_connections[project_id][channelId]:
                    del active_connections[project_id][channelId]
                    # Clean up empty projects
                    if not active_connections[project_id]:
                        del active_connections[project_id]
    