from fastapi import APIRouter, Depends, HTTPException
from database import SessionLocal
from typing import List
import logging
from schemas.task import TaskCreate, Task, TaskStatusUpdate, TaskUpdate, Comment, UpdateSubTaskState
from crud.task import (
    create_task, get_tasks, get_tasks_by_member_id, get_tasks_by_project_id,
    delete_task_by_id, update_task_status, update_task_by_id,
    upload_task_comment, update_subtask_state_by_id, delete_task_comment
)
from utils.sse_manager import project_sse_manager
from crud.project import get_project
import json

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
async def handle_create_task(project_id: str, task: TaskCreate, db: SessionLocal = Depends(get_db)):  # type: ignore
    try:
        db_task = create_task(db, project_id, task)
        if db_task:
            project_data = get_project(db, project_id)
            await project_sse_manager.send_event(
                project_id,
                json.dumps(project_sse_manager.convert_to_dict(project_data))
            )
            logging.info(f"[SSE] Project {project_id} updated from Task creation.")
        else:
            raise HTTPException(status_code=404, detail="Project not found")
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
def get_all_tasks(skip: int = 0, limit: int = 100, db: SessionLocal = Depends(get_db)):  # type: ignore
    try:
        tasks = get_tasks(db, skip=skip, limit=limit)
        return tasks
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
  
@router.get('/member/{member_id}/task', response_model=List[Task])
def get_all_tasks_by_member_id(member_id: int, db: SessionLocal = Depends(get_db)):  # type: ignore
    tasks = get_tasks_by_member_id(db, member_id)
    return tasks
  
@router.get('/project/{project_id}/task', response_model=List[Task])
def get_all_tasks_by_project_id(project_id: str, db: SessionLocal = Depends(get_db)):  # type: ignore
    tasks = get_tasks_by_project_id(db, project_id)
    return tasks

@router.delete('/project/{project_id}/task/{task_id}')
async def delete_task(project_id: str, task_id: int, db: SessionLocal = Depends(get_db)):  # type: ignore
    try:
        delete_task_by_id(db, project_id, task_id)
        if delete_task_by_id:
            project_data = get_project(db, project_id)
            await project_sse_manager.send_event(
                project_id,
                    json.dumps(project_sse_manager.convert_to_dict(project_data))
                )
            logging.info(f"[SSE] Project {project_id} updated from Task {task_id} deletion.")
        else:
            raise HTTPException(status_code=404, detail="Task not found")
        return {"status": "success", "message": "Task deleted successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.put('/project/{project_id}/task/{task_id}/status')
async def update_task_status_endpoint(project_id: str, task_id: int, status: TaskStatusUpdate, db: SessionLocal = Depends(get_db)):  # type: ignore
    try:
        update_task_status(db, project_id, task_id, status)
        if update_task_status:
            project_data = get_project(db, project_id)
            await project_sse_manager.send_event(
                project_id,
                json.dumps(project_sse_manager.convert_to_dict(project_data))
            )
            logging.info(f"[SSE] Project {project_id} updated from Task {task_id} status change.")
        else:
            raise HTTPException(status_code=404, detail="Task not found")
        return {"status": "success", "message": "Task status updated successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
  
@router.put('/project/{project_id}/task/{task_id}')
async def update_task_endpoint(project_id: str, task_id: int, task: TaskUpdate, db: SessionLocal = Depends(get_db)):  # type: ignore
    try:
        updated_task = update_task_by_id(db, project_id, task_id, task)
        if updated_task:    
            project_data = get_project(db, project_id)
            await project_sse_manager.send_event(
                project_id,
                json.dumps(project_sse_manager.convert_to_dict(project_data))
            )
            logging.info(f"[SSE] Project {project_id} updated from Task {task_id} update.")
        else:
            raise HTTPException(status_code=404, detail="Task not found")
        return updated_task
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
  
@router.post('/project/{project_id}/task/{task_id}/comment')
async def upload_task_comment_endpoint(project_id: str, task_id: int, comment: Comment, db: SessionLocal = Depends(get_db)):  # type: ignore
    try:
        updated_task = await upload_task_comment(db, project_id, task_id, comment)
        if updated_task:
            project_data = get_project(db, project_id)
            await project_sse_manager.send_event(
                project_id,
                json.dumps(project_sse_manager.convert_to_dict(project_data))
            )
            logging.info(f"[SSE] Project {project_id} updated from Task {task_id} comment upload.")
        else:
            raise HTTPException(status_code=404, detail="Task not found")
        return updated_task
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
      
@router.delete('/project/{project_id}/task/{task_id}/comment/{comment_id}')
async def delete_task_comment_endpoint(project_id: str, task_id: int, comment_id: int, db: SessionLocal = Depends(get_db)):  # type: ignore
    try:
        updated_task = delete_task_comment(db, project_id, task_id, comment_id)
        if updated_task:
            project_data = get_project(db, project_id)
            await project_sse_manager.send_event(
                project_id,
                json.dumps(project_sse_manager.convert_to_dict(project_data))
            )
            logging.info(f"[SSE] Project {project_id} updated from Task {task_id} comment deletion.")
        else:
            raise HTTPException(status_code=404, detail="Task or Comment not found")
        return updated_task
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.put('/project/{project_id}/task/{task_id}/subtask/{subtask_id}/state')
async def update_subtask_state_endpoint(project_id: str, task_id: int, subtask_id: int, subtask_update: UpdateSubTaskState, db: SessionLocal = Depends(get_db)):  # type: ignore
    try:
        updated_task = update_subtask_state_by_id(db, project_id, task_id, subtask_id, subtask_update)
        if updated_task:
            project_data = get_project(db, project_id)
            await project_sse_manager.send_event(
                project_id,
                json.dumps(project_sse_manager.convert_to_dict(project_data))
            )
            logging.info(f"[SSE] Project {project_id} updated from SubTask {subtask_id} state change.")
            return updated_task
        else:
            raise HTTPException(status_code=404, detail="Task or SubTask not found")
    except Exception as e:
        logging.error(f"[ERROR] Failed to update SubTask: {e}")
        raise HTTPException(status_code=500, detail=str(e))