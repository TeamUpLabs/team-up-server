from fastapi import APIRouter, Depends, HTTPException
from database import SessionLocal
from typing import List
import logging
from schemas.task import TaskCreate, Task, TaskStatusUpdate, TaskUpdate, Comment, UpdateSubTaskState
from crud.task import (
    create_task, get_tasks, get_tasks_by_member_id, get_tasks_by_project_id,
    delete_task_by_id, update_task_status, update_task_by_id,
    upload_task_comment, update_subtask_state_by_id
)

router = APIRouter(
    tags=["task"]
)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.post("/project/{project_id}/task", response_model=Task)
def handle_create_task(project_id: str, task: TaskCreate, db: SessionLocal = Depends(get_db)):
    try:
        db_task = create_task(db, project_id, task)
        logging.info(f"Successfully created task with id: {db_task}")
        return db_task
    except HTTPException as he:
        logging.error(f"HTTP Exception during task creation: {str(he)}")
        raise
    except Exception as e:
        logging.error(f"Unexpected error during task creation: {str(e)}")
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail="Internal server error occurred while creating task"
        )
        
@router.get('/task', response_model=List[Task])
def get_all_tasks(skip: int = 0, limit: int = 100, db: SessionLocal = Depends(get_db)):
    try:
        tasks = get_tasks(db, skip=skip, limit=limit)
        return tasks
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
  
@router.get('/member/{member_id}/task', response_model=List[Task])
def get_all_tasks_by_member_id(member_id: int, db: SessionLocal = Depends(get_db)):
    tasks = get_tasks_by_member_id(db, member_id)
    return tasks
  
@router.get('/project/{project_id}/task', response_model=List[Task])
def get_all_tasks_by_project_id(project_id: str, db: SessionLocal = Depends(get_db)):
    tasks = get_tasks_by_project_id(db, project_id)
    return tasks

@router.delete('/project/{project_id}/task/{task_id}')
def delete_task(project_id: str, task_id: int, db: SessionLocal = Depends(get_db)):
    try:
        delete_task_by_id(db, project_id, task_id)
        return {"status": "success", "message": "Task deleted successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
  
@router.put('/project/{project_id}/task/{task_id}/status')
def update_task_status_endpoint(project_id: str, task_id: int, status: TaskStatusUpdate, db: SessionLocal = Depends(get_db)):
    try:
        update_task_status(db, project_id, task_id, status)
        return {"status": "success", "message": "Task status updated successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
  
@router.put('/project/{project_id}/task/{task_id}')
def update_task_endpoint(project_id: str, task_id: int, task: TaskUpdate, db: SessionLocal = Depends(get_db)):
    try:
        updated_task = update_task_by_id(db, project_id, task_id, task)
        return updated_task
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
  
@router.post('/project/{project_id}/task/{task_id}/comment')
def upload_task_comment_endpoint(project_id: str, task_id: int, comment: Comment, db: SessionLocal = Depends(get_db)):
    try:
        updated_task = upload_task_comment(db, project_id, task_id, comment)
        return updated_task
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.put('/project/{project_id}/task/{task_id}/subtask/{subtask_id}/state')
def update_subtask_state_endpoint(project_id: str, task_id: int, subtask_id: int, subtask_update: UpdateSubTaskState, db: SessionLocal = Depends(get_db)):
    try:
        updated_task = update_subtask_state_by_id(db, project_id, task_id, subtask_id, subtask_update)
        return updated_task
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) 