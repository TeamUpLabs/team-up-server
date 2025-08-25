from fastapi import APIRouter, Depends, HTTPException
from crud.whiteboard import whiteboard
from crud.project import project
from database import get_db
from schemas.whiteboard import WhiteBoardCreate, WhiteBoardDetail, WhiteBoardBrief, WhiteBoardUpdate, CommentCreate, CommentUpdate, Comment
from sqlalchemy.orm import Session
from typing import List
from utils.sse_manager import project_sse_manager
from utils.auth import get_current_user
import json
from routers.project_router import convert_project_to_project_detail
from models.user import User

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
async def update_whiteboard(
    whiteboard_id: int, 
    whiteboard_in: WhiteBoardUpdate, 
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    # Add the current user's ID to the update data
    update_data = whiteboard_in.model_dump()
    update_data['updated_by'] = current_user.id
    
    db_whiteboard = whiteboard.update(
        db=db, 
        whiteboard_id=whiteboard_id, 
        obj_in=WhiteBoardUpdate(**update_data)
    )
    
    if db_whiteboard:
        project_data = convert_project_to_project_detail(project.get(db, db_whiteboard.project_id), db)
        await project_sse_manager.send_event(
            db_whiteboard.project_id,
            json.dumps(project_sse_manager.convert_to_dict(project_data))
        )
    return db_whiteboard

@router.delete("/{whiteboard_id}", response_model=WhiteBoardDetail)
async def delete_whiteboard(whiteboard_id: int, db: Session = Depends(get_db)):
    db_whiteboard = whiteboard.remove(db=db, whiteboard_id=whiteboard_id)
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
    comment, project_id = whiteboard.create_comment(db=db, whiteboard_id=whiteboard_id, content=comment_in.content, creator_id=comment_in.creator.id)
    
    project_data = convert_project_to_project_detail(project.get(db, project_id), db)
    await project_sse_manager.send_event(
        project_id,
        json.dumps(project_sse_manager.convert_to_dict(project_data))
    )
    return Comment.model_validate(comment, from_attributes=True)

@router.put("/{whiteboard_id}/comments/{comment_id}", response_model=Comment)
async def update_comment(whiteboard_id: int, comment_id: int, comment_in: CommentUpdate, db: Session = Depends(get_db)):
    comment, project_id = whiteboard.update_comment(db=db, whiteboard_id=whiteboard_id, comment_id=comment_id, content=comment_in.content)
    
    project_data = convert_project_to_project_detail(project.get(db, project_id), db)
    await project_sse_manager.send_event(
        project_id,
        json.dumps(project_sse_manager.convert_to_dict(project_data))
    )
    return Comment.model_validate(comment, from_attributes=True)

@router.delete("/{whiteboard_id}/comments/{comment_id}", response_model=dict)
async def delete_comment(whiteboard_id: int, comment_id: int, db: Session = Depends(get_db)):
    success, project_id = whiteboard.delete_comment(db=db, whiteboard_id=whiteboard_id, comment_id=comment_id)
    if not success:
        raise HTTPException(status_code=404, detail="Comment not found")
    
    project_data = convert_project_to_project_detail(project.get(db, project_id), db)
    await project_sse_manager.send_event(
        project_id,
        json.dumps(project_sse_manager.convert_to_dict(project_data))
    )
    return {"status": "success", "message": "Comment deleted successfully"}
  
@router.put("/{whiteboard_id}/like", response_model=WhiteBoardDetail)
async def toggle_whiteboard_like(
    whiteboard_id: int, 
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    WhiteBoard 좋아요/좋아요 취소 토글
    이미 좋아요를 누른 상태라면 좋아요 취소, 아니면 좋아요 추가
    """
    db_whiteboard = whiteboard.update_like(db=db, whiteboard_id=whiteboard_id, user_id=current_user.id)
    
    # SSE로 좋아요 상태 변경 알림 전송
    if db_whiteboard:
        project_data = convert_project_to_project_detail(project.get(db, db_whiteboard.project_id), db)
        await project_sse_manager.send_event(
            db_whiteboard.project_id,
            json.dumps(project_sse_manager.convert_to_dict(project_data))
        )
    
    return db_whiteboard
  
@router.put("/{whiteboard_id}/view", response_model=WhiteBoardDetail)
async def update_whiteboard_view(whiteboard_id: int, db: Session = Depends(get_db)):
    db_whiteboard = whiteboard.update_view(db=db, whiteboard_id=whiteboard_id)
    
    # SSE로 조회수 변경 알림 전송
    if db_whiteboard:
        project_data = convert_project_to_project_detail(project.get(db, db_whiteboard.project_id), db)
        await project_sse_manager.send_event(
            db_whiteboard.project_id,
            json.dumps(project_sse_manager.convert_to_dict(project_data))
        )
    
    return db_whiteboard
    