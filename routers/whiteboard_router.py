from fastapi import APIRouter, Depends
from crud.whiteboard import whiteboard
from database import get_db
from schemas.whiteboard import WhiteBoardCreate, WhiteBoardDetail, WhiteBoardBrief, WhiteBoardUpdate
from sqlalchemy.orm import Session
from models.whiteboard import WhiteBoard
from typing import List

router = APIRouter(
    prefix="/api/whiteboards",
    tags=["whiteboards"]
)

@router.post("/", response_model=WhiteBoardBrief)
def create_whiteboard(whiteboard_in: WhiteBoardCreate, db: Session = Depends(get_db)):
    return whiteboard.create(db=db, obj_in=whiteboard_in)
  
@router.get("/{whiteboard_id}", response_model=WhiteBoardDetail)
def read_whiteboard(whiteboard_id: int, db: Session = Depends(get_db)):
    return whiteboard.get(db=db, id=whiteboard_id)
  
@router.get("/project/{project_id}", response_model=List[WhiteBoardDetail])
def read_whiteboards_by_project(project_id: str, skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    return whiteboard.get_by_project(db=db, project_id=project_id, skip=skip, limit=limit)

@router.put("/{whiteboard_id}", response_model=WhiteBoardDetail)
def update_whiteboard(whiteboard_id: int, whiteboard_in: WhiteBoardUpdate, db: Session = Depends(get_db)):
    return whiteboard.update(db=db, id=whiteboard_id, obj_in=whiteboard_in)

@router.delete("/{whiteboard_id}", response_model=WhiteBoardDetail)
def delete_whiteboard(whiteboard_id: int, db: Session = Depends(get_db)):
    return whiteboard.remove(db=db, id=whiteboard_id)
