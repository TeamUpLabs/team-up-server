from fastapi import APIRouter, Depends, HTTPException
from database import SessionLocal
import logging
from schemas.channel import ChannelCreate, ChannelUpdate, Channel
from crud.channel import create_channel, get_channel_by_project_id, get_channel_by_channel_id
from utils.sse_manager import project_sse_manager
import json
from typing import List
from crud.project import get_project

router = APIRouter(
  prefix="/project",
  tags=["channel"]
)
    
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
        
@router.post("/{projectId}/channel", response_model=Channel)
async def handle_create_channel(projectId: str, payload: ChannelCreate, db: SessionLocal = Depends(get_db)):  # type: ignore
  try:
    db_channel = create_channel(db, payload)
    
    if db_channel:
      project_data = get_project(db, projectId)
      await project_sse_manager.send_event(
        projectId,
        json.dumps(project_sse_manager.convert_to_dict(project_data))
      )
      logging.info(f"[SSE] Project {projectId} updated from Channel create.")
    else:
      raise HTTPException(status_code=404, detail="Project not found")
    return db_channel
  except Exception as e:
    raise HTTPException(status_code=500, detail=str(e))

@router.get("/{projectId}/channel", response_model=List[Channel])
async def handle_get_channel_by_project_id(projectId: str, db: SessionLocal = Depends(get_db)):  # type: ignore
  try:
    channels = get_channel_by_project_id(db, projectId)
    return channels
  except Exception as e:
    raise HTTPException(status_code=500, detail=str(e))

@router.get("/{projectId}/channel/{channelId}", response_model=Channel)
async def handle_get_channel_by_channel_id(projectId: str, channelId: str, db: SessionLocal = Depends(get_db)):  # type: ignore
  try:
    channel = get_channel_by_channel_id(db, projectId, channelId)
    if channel:
      project_data = get_project(db, projectId)
      await project_sse_manager.send_event(
        projectId,
        json.dumps(project_sse_manager.convert_to_dict(project_data))
      )
      logging.info(f"[SSE] Project {projectId} updated from Channel get.")
    else:
      raise HTTPException(status_code=404, detail="Channel not found")
    return channel
  except Exception as e:
    raise HTTPException(status_code=500, detail=str(e))
