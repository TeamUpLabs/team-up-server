from fastapi import APIRouter, Depends, HTTPException
from database import SessionLocal
from typing import List
import logging
from schemas.project import Project, ProjectCreate, ProjectInfoUpdate, ProjectMemberAdd, ProjectMemberPermission, ProjectMemberScout
from schemas.member import Member
from crud.project import (
    create_project, get_all_projects, get_project, get_member_by_project_id, get_all_projects_excluding_my,
    delete_project_by_id, update_project_by_id, update_project_member_permission, kick_out_member_from_project,
    add_member_to_project, scout_member, send_project_participation_request,
    allow_project_participation_request, reject_project_participation_request, get_all_project_ids
)
import asyncio
from typing import AsyncGenerator
from fastapi.responses import StreamingResponse
from fastapi import Request
import json

router = APIRouter(
    prefix="/project",
    tags=["project"]
)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.post("")
def create_project_route(project: ProjectCreate, db: SessionLocal = Depends(get_db)):
    return create_project(db, project)
  
@router.get("", response_model=List[Project])
def read_projects(skip: int = 0, limit: int = 100, db: SessionLocal = Depends(get_db)):
    try:
        projects = get_all_projects(db, skip=skip, limit=limit)
        return projects
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
      
@router.get("/id", response_model=List[str])
def read_all_projects_ids(db: SessionLocal = Depends(get_db)):
    try:
        project_ids = get_all_project_ids(db)
        return project_ids
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
      
@router.get("/{project_id}", response_model=Project)
def read_project_endpoint(project_id: str, db: SessionLocal = Depends(get_db)):
    try:
        project = get_project(db, project_id)
        if project is None:
            raise HTTPException(status_code=404, detail=f"Project {project_id} not found")
        return project
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
      
@router.get("/{project_id}/member", response_model=List[Member])
def read_member_by_project_id(project_id: str, db: SessionLocal = Depends(get_db)):
    try:
        members = get_member_by_project_id(db, project_id)
        return members
    except Exception as e:
        logging.error(e)
        return []
      
@router.get("/exclude/{member_id}", response_model=List[Project])
def get_projects_excluding_my_project(member_id: int, db: SessionLocal = Depends(get_db)):
    try:
        other_projects = get_all_projects_excluding_my(db, member_id)
        if other_projects is None:
            raise HTTPException(status_code=404, detail=f"Projects not found")
        return other_projects
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
  
@router.delete("/{project_id}")
def delete_project(project_id: str, db: SessionLocal = Depends(get_db)):
    try:
        delete_project_by_id(db, project_id)
        return {"status": "success", "message": "Project deleted successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
  
@router.put("/{project_id}")
def update_project(project_id: str, project: ProjectInfoUpdate, db: SessionLocal = Depends(get_db)):
    try:
        updated_project = update_project_by_id(db, project_id, project)
        return updated_project
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
  
@router.put("/{project_id}/member/{member_id}/permission")
def update_project_member_permission_endpoint(project_id: str, member_id: int, permission: ProjectMemberPermission, db: SessionLocal = Depends(get_db)):
    try:
        updated_project = update_project_member_permission(db, project_id, member_id, permission)
        return updated_project
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
  
@router.put("/{project_id}/member/{member_id}/kick")
def kick_out_member_from_project_endpoint(project_id: str, member_id: int, db: SessionLocal = Depends(get_db)):
    try:
        result = kick_out_member_from_project(db, project_id, member_id)
        if result is None:
            raise HTTPException(status_code=404, detail=f"Member {member_id} or Project {project_id} not found")
        return {"status": "success", "message": f"Member {member_id} kicked from project {project_id}"}
    except Exception as e:
        logging.error(f"Error kicking member: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error kicking member: {str(e)}")

@router.put("/{project_id}/participationRequest/{member_id}/send")
def send_project_participation_request_endpoint(project_id: str, member_id: int, db: SessionLocal = Depends(get_db)):
    try:
        return send_project_participation_request(db, project_id, member_id)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.put("/{project_id}/participationRequest/{member_id}/allow")
def allow_project_participation_request_endpoint(project_id: str, member_id: int, db: SessionLocal = Depends(get_db)):
    try:
        return allow_project_participation_request(db, project_id, member_id)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.put("/{project_id}/participationRequest/{member_id}/reject")
def reject_project_participation_request_endpoint(project_id: str, member_id: int, db: SessionLocal = Depends(get_db)):
    try:
        return reject_project_participation_request(db, project_id, member_id)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
      
@router.post("/{project_id}/member")
def add_member_to_project_route(project_id: str, member_data: ProjectMemberAdd, db: SessionLocal = Depends(get_db)):
    try:
        result = add_member_to_project(db, project_id, member_data.member_id)
        if result.get("status") == "error":
            raise HTTPException(status_code=400, detail=result.get("message"))
        return result
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/{project_id}/member/{member_id}/scout")
def scout_member_endpoint(project_id: str, member_id: int, member_data: ProjectMemberScout, db: SessionLocal = Depends(get_db)):
    try:
        return scout_member(db, project_id, member_id, member_data)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) 
      
      
@router.get("/{project_id}/sse")
async def project_sse(project_id: str, request: Request):
    def convert_to_dict(obj):
        if hasattr(obj, '__dict__'):
            return {
                key: convert_to_dict(value)
                for key, value in obj.__dict__.items()
                if not key.startswith('_')
            }
        elif isinstance(obj, (list, tuple)):
            return [convert_to_dict(item) for item in obj]
        elif isinstance(obj, dict):
            return {key: convert_to_dict(value) for key, value in obj.items()}
        else:
            return obj

    async def event_generator() -> AsyncGenerator[str, None]:
        db = None
        try:
            db = SessionLocal()
            last_project = None
            
            # Send initial connection success message
            yield f"data: {json.dumps({'status': 'connected'})}\n\n"
            
            while True:
                if await request.is_disconnected():
                    logging.info(f"Client disconnected from project {project_id} SSE")
                    break

                try:
                    current_project = get_project(db, project_id)
                    if current_project is None:
                        error_message = {
                            'error': f"Project {project_id} not found",
                            'status': 'error'
                        }
                        yield f"data: {json.dumps(error_message)}\n\n"
                        await asyncio.sleep(3)
                        continue

                    project_dict = convert_to_dict(current_project)
                    if last_project != project_dict:
                        yield f"data: {json.dumps(project_dict)}\n\n"
                        last_project = project_dict
                except Exception as e:
                    logging.error(f"Error in SSE for project {project_id}: {str(e)}")
                    error_message = {
                        'error': str(e),
                        'status': 'error'
                    }
                    yield f"data: {json.dumps(error_message)}\n\n"
                    # Don't break the connection on error, just log it and continue
                    await asyncio.sleep(3)
                    continue

                await asyncio.sleep(3)
        except Exception as e:
            logging.error(f"Critical error in SSE for project {project_id}: {str(e)}")
            yield f"data: {json.dumps({'error': str(e), 'status': 'error'})}\n\n"
        finally:
            if db:
                db.close()
            logging.info(f"SSE connection closed for project {project_id}")

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
            "Access-Control-Allow-Origin": "*"  # Add CORS header
        }
    )