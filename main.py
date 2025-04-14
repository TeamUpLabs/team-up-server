from fastapi import FastAPI, WebSocket, Depends, WebSocketDisconnect, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import logging
from database import SessionLocal, engine, Base
from websocket.chat import websocket_handler
from typing import List
from auth import create_access_token, verify_password, get_current_user
import schemas.login
from schemas.chat import ChatCreate
from schemas.member import MemberCreate, Member
from schemas.login import LoginForm
from schemas.task import TaskCreate, Task
from schemas.project import Project, ProjectCreate
from schemas.milestone import MileStone, MileStoneCreate
from crud.chat import *
from crud.project import *
from crud.member import *
from crud.task import *
from crud.milestone import *


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


@app.websocket("/ws/chat/{channelId}")
async def chat_endpoint(websocket: WebSocket, channelId: str):
    try:
        await websocket.accept()
        logging.info(f"WebSocket connection established for channel: {channelId}")
        await websocket_handler(websocket, channelId)
    except WebSocketDisconnect:
        logging.info(f"WebSocket disconnected for channel: {channelId}")
    except Exception as e:
        logging.error(f"WebSocket error in channel {channelId}: {str(e)}")
        try:
            await websocket.close()
        except:
            pass

@app.post("/chat")
def post_message(chat: ChatCreate, db: SessionLocal = Depends(get_db)): # type: ignore
    return save_chat_message(db, chat)


@app.get("/chat/{channelId}")
def get_messages(channelId: str, db: SessionLocal = Depends(get_db)): # type: ignore
    return get_chat_history(db, channelId)
  
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
        "department": member.department,
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
      
  
@app.get("/project/{project_id}", response_model=Project)
def read_project(project_id: str, db: SessionLocal = Depends(get_db)): # type: ignore
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
  return get_member_by_project_id(db, project_id)
      

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
  
@app.get('/project/{project_id}/task', response_model=List[Task])
def get_all_tasks_by_project_id(project_id: str, db: SessionLocal = Depends(get_db)): # type: ignore
  tasks = get_tasks_by_project_id(db, project_id)
  return tasks


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
    