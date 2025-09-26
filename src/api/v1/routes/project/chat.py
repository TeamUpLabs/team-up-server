from fastapi import APIRouter, Depends, HTTPException, status, WebSocket, WebSocketDisconnect
from sqlalchemy.orm import Session
from core.database.database import get_db
from api.v1.services.project.chat_service import ChatService
from api.v1.schemas.project.chat_schema import ChatCreate, ChatUpdate, ChatDetail
from core.security.auth import get_current_user
from core.security.jwt import verify_token
from core.utils.chat_websocket import websocket_handler
from typing import List, Optional
import logging

router = APIRouter(prefix="/api/v1/projects/{project_id}/chats", tags=["chats"])

@router.post("/", response_model=ChatDetail)
def create_chat(
  project_id: str,
  channel_id: str,
  chat: ChatCreate,
  db: Session = Depends(get_db),
  current_user: dict = Depends(get_current_user)
):
  if not current_user:
    raise HTTPException(
      status_code=status.HTTP_403_FORBIDDEN,
      detail="Not authorized to perform this action"
    )
    
  try:
    service = ChatService(db)
    return service.create(project_id, channel_id, current_user.id, chat)
  except HTTPException as e:
    raise e
  except Exception as e:
    raise HTTPException(status_code=400, detail=str(e))
  
@router.get("/", response_model=List[ChatDetail])
def get_chats(
  project_id: str,
  channel_id: Optional[str] = None,
  user_id: Optional[int] = None,
  db: Session = Depends(get_db),
  current_user: dict = Depends(get_current_user)
):
  if not current_user:
    raise HTTPException(
      status_code=status.HTTP_403_FORBIDDEN,
      detail="Not authorized to perform this action"
    )
    
  try:
    service = ChatService(db)
    if channel_id:
      return service.get_by_channel_id(project_id, channel_id)
    elif user_id:
      return service.get_by_user_id(project_id, user_id)
    else:
      return service.get_by_project_id(project_id)
  except HTTPException as e:
    raise e
  except Exception as e:
    raise HTTPException(status_code=400, detail=str(e))

@router.get("/{chat_id}", response_model=ChatDetail)
def get_chat(
  project_id: str,
  channel_id: str,
  chat_id: int,
  db: Session = Depends(get_db),
  current_user: dict = Depends(get_current_user)
):
  if not current_user:
    raise HTTPException(
      status_code=status.HTTP_403_FORBIDDEN,
      detail="Not authorized to perform this action"
    )
    
  try:
    service = ChatService(db)
    return service.get(project_id, channel_id, current_user.id, chat_id)
  except HTTPException as e:
    raise e
  except Exception as e:
    raise HTTPException(status_code=400, detail=str(e))
  
@router.put("/{chat_id}", response_model=ChatDetail)
def update_chat(
  project_id: str,
  channel_id: str,
  chat_id: int,
  chat: ChatUpdate,
  db: Session = Depends(get_db),
  current_user: dict = Depends(get_current_user)
):
  if not current_user:
    raise HTTPException(
      status_code=status.HTTP_403_FORBIDDEN,
      detail="Not authorized to perform this action"
    )
    
  try:
    service = ChatService(db)
    return service.update(project_id, channel_id, current_user.id, chat_id, chat)
  except HTTPException as e:
    raise e
  except Exception as e:
    raise HTTPException(status_code=400, detail=str(e))
  
@router.delete("/{chat_id}", response_model=ChatDetail)
def delete_chat(
  project_id: str,
  channel_id: str,
  chat_id: int,
  db: Session = Depends(get_db),
  current_user: dict = Depends(get_current_user)
):
  if not current_user:
    raise HTTPException(
      status_code=status.HTTP_403_FORBIDDEN,
      detail="Not authorized to perform this action"
    )
    
  try:
    service = ChatService(db)
    return service.delete(project_id, channel_id, current_user.id, chat_id)
  except HTTPException as e:
    raise e
  except Exception as e:
    raise HTTPException(status_code=400, detail=str(e))
  
@router.websocket("/ws")
async def chat_endpoint(
    websocket: WebSocket,
    project_id: str,
    channel_id: str,
    user_id: int,
    access_token: str,
    db: Session = Depends(get_db)
):
  try:
    verify_token(access_token)
  except Exception as e:
    raise HTTPException(status_code=401, detail="Invalid authentication token")
  try:
    await websocket_handler(websocket, channel_id, project_id, user_id, db)
          
  except WebSocketDisconnect:
      logging.info(f"WebSocket disconnected for project: {project_id}, channel: {channel_id}")
  except Exception as e:
      logging.error(f"WebSocket error in project {project_id}, channel {channel_id}: {str(e)}")
      try:
          await websocket.close(code=status.WS_1011_INTERNAL_ERROR, reason="Internal server error")
      except Exception:
          pass
    