from fastapi import APIRouter, Depends
from crud.whiteboard import whiteboard
from crud.project import project
from database import get_db
from schemas.whiteboard import WhiteBoardCreate, WhiteBoardDetail, WhiteBoardBrief, WhiteBoardUpdate, CommentCreate, CommentUpdate, Comment
from sqlalchemy.orm import Session
from typing import List
from utils.sse_manager import project_sse_manager
import json
from routers.project_router import convert_project_to_project_detail

router = APIRouter(
    prefix="/api/whiteboards",
    tags=["whiteboards"]
)

@router.post("/", response_model=WhiteBoardBrief)
async def create_whiteboard(whiteboard_in: WhiteBoardCreate, db: Session = Depends(get_db)):
    db_whiteboard = whiteboard.create(db=db, obj_in=whiteboard_in)
    if db_whiteboard:
        project_data = convert_project_to_project_detail(project.get(db, db_whiteboard.project_id), db)
        await project_sse_manager.send_event(
            db_whiteboard.project_id,
            json.dumps(project_sse_manager.convert_to_dict(project_data))
        )
    return db_whiteboard
  
@router.get("/{whiteboard_id}", response_model=WhiteBoardDetail)
def read_whiteboard(whiteboard_id: int, db: Session = Depends(get_db)):
    return whiteboard.get(db=db, id=whiteboard_id)
  
@router.get("/project/{project_id}", response_model=List[WhiteBoardDetail])
def read_whiteboards_by_project(project_id: str, skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    return whiteboard.get_by_project(db=db, project_id=project_id, skip=skip, limit=limit)

@router.put("/{whiteboard_id}", response_model=WhiteBoardDetail)
async def update_whiteboard(whiteboard_id: int, whiteboard_in: WhiteBoardUpdate, db: Session = Depends(get_db)):
  db_whiteboard = whiteboard.update(db=db, id=whiteboard_id, obj_in=whiteboard_in)
  if db_whiteboard:
        project_data = convert_project_to_project_detail(project.get(db, db_whiteboard.project_id), db)
        await project_sse_manager.send_event(
            db_whiteboard.project_id,
            json.dumps(project_sse_manager.convert_to_dict(project_data))
        )

@router.delete("/{whiteboard_id}", response_model=WhiteBoardDetail)
async def delete_whiteboard(whiteboard_id: int, db: Session = Depends(get_db)):
    db_whiteboard = whiteboard.remove(db=db, id=whiteboard_id)
    if db_whiteboard:
        project_data = convert_project_to_project_detail(project.get(db, db_whiteboard.project_id), db)
        await project_sse_manager.send_event(
            db_whiteboard.project_id,
            json.dumps(project_sse_manager.convert_to_dict(project_data))
        )
    return db_whiteboard
  
@router.get("/{whiteboard_id}/comments", response_model=List[Comment])
def read_comments(whiteboard_id: int, skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    return whiteboard.get_comments(db=db, whiteboard_id=whiteboard_id, skip=skip, limit=limit)
  
@router.post("/{whiteboard_id}/comments", response_model=Comment)
async def create_comment(whiteboard_id: int, comment_in: CommentCreate, db: Session = Depends(get_db)):
    db_comment = whiteboard.create_comment(db=db, whiteboard_id=whiteboard_id, content=comment_in.content, creator_id=comment_in.creator.id)
    return db_comment

@router.put("/{whiteboard_id}/comments/{comment_id}", response_model=Comment)
async def update_comment(whiteboard_id: int, comment_id: int, comment_in: CommentUpdate, db: Session = Depends(get_db)):
    db_comment = whiteboard.update_comment(db=db, whiteboard_id=whiteboard_id, comment_id=comment_id, content=comment_in.content)
    return db_comment

@router.delete("/{whiteboard_id}/comments/{comment_id}", response_model=dict)
async def delete_comment(whiteboard_id: int, comment_id: int, db: Session = Depends(get_db)):
    success = whiteboard.delete_comment(db=db, whiteboard_id=whiteboard_id, comment_id=comment_id)
    if not success:
        raise HTTPException(status_code=404, detail="Comment not found")
    return {"status": "success", "message": "Comment deleted successfully"}