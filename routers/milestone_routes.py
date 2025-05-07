from fastapi import APIRouter, Depends, HTTPException
from database import SessionLocal
from typing import List
import logging
from schemas.milestone import MileStone, MileStoneCreate, MileStoneUpdate
from crud.milestone import (
    create_milestone, get_milestones, get_milestones_by_project_id,
    delete_milestone_by_id, update_milestone_by_id
)

router = APIRouter(
    tags=["milestone"]
)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.post('/project/{project_id}/milestone', response_model=MileStone)
def handle_create_milestone(project_id: str, milestone: MileStoneCreate, db: SessionLocal = Depends(get_db)):
    try:
        db_milestone = create_milestone(db, project_id, milestone)
        logging.info(f"Successfully created milestone with id: {db_milestone}")
        return db_milestone
    except HTTPException as he:
        logging.error(f"HTTP Exception during milestone creation: {str(he)}")
        raise
    except Exception as e:
        logging.error(f"Unexpected error during milestone creation: {str(e)}")
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail="Internal server error occurred while creating milestone"
        )
    
@router.get('/milestone', response_model=List[MileStone])
def get_all_milestones(skip: int = 0, limit: int = 100, db: SessionLocal = Depends(get_db)):
    try:
        milestones = get_milestones(db, skip=skip, limit=limit)
        return milestones
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
  
@router.get('/project/{project_id}/milestone', response_model=List[MileStone])
def get_all_milestones_by_project_id(project_id: str, db: SessionLocal = Depends(get_db)):
    try:
        milestones = get_milestones_by_project_id(db, project_id)
        return milestones
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
  
@router.delete("/project/{project_id}/milestone/{milestone_id}")
def delete_milestone(project_id: str, milestone_id: int, db: SessionLocal = Depends(get_db)):
    try:
        delete_milestone_by_id(db, project_id, milestone_id)
        return {"status": "success", "message": "Milestone deleted successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
  
@router.put("/project/{project_id}/milestone/{milestone_id}")
def update_milestone_endpoint(project_id: str, milestone_id: int, milestone: MileStoneUpdate, db: SessionLocal = Depends(get_db)):
    try:
        updated_milestone = update_milestone_by_id(db, project_id, milestone_id, milestone)
        return updated_milestone
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) 