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
from utils.sse_manager import project_sse_manager

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
async def create_project_route(project: ProjectCreate, db: SessionLocal = Depends(get_db)):  # type: ignore
    result = create_project(db, project)
    if result:
        project_data = get_project(db, result.id)
        await project_sse_manager.send_event(
            result.id,
            json.dumps(project_sse_manager.convert_to_dict(project_data))
        )
        logging.info(f"[SSE] Project {result.id} created.")
    else:
        logging.error(f"Failed to create project {project.name}")
    return result

@router.get("", response_model=List[Project])
def read_projects(skip: int = 0, limit: int = 100, db: SessionLocal = Depends(get_db)):  # type: ignore
    try:
        projects = get_all_projects(db, skip=skip, limit=limit)
        return projects
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/id", response_model=List[str])
def read_all_projects_ids(db: SessionLocal = Depends(get_db)):  # type: ignore
    try:
        project_ids = get_all_project_ids(db)
        return project_ids
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{project_id}", response_model=Project)
def read_project_endpoint(project_id: str, db: SessionLocal = Depends(get_db)):  # type: ignore
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
def read_member_by_project_id(project_id: str, db: SessionLocal = Depends(get_db)):  # type: ignore
    try:
        members = get_member_by_project_id(db, project_id)
        return members
    except Exception as e:
        logging.error(e)
        return []

@router.get("/exclude/{member_id}", response_model=List[Project])
def get_projects_excluding_my_project(member_id: int, db: SessionLocal = Depends(get_db)):  # type: ignore
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
async def delete_project_endpoint(project_id: str, db: SessionLocal = Depends(get_db)):  # type: ignore
    try:
        result = delete_project_by_id(db, project_id)
        if result:
            project_data = get_project(db, project_id)
            if project_data is not None:
                await project_sse_manager.send_event(
                    project_id,
                    json.dumps(project_sse_manager.convert_to_dict(project_data))
                )
                logging.info(f"[SSE] Project {project_id} deleted.")
            else:
                logging.warning(f"Project {project_id} deleted but no project data found for SSE.")
        else:
            raise HTTPException(status_code=404, detail="Project not found")
        return {"status": "success", "message": "Project deleted successfully"}
    except Exception as e:
        import traceback
        print(traceback.format_exc())
        raise HTTPException(status_code=500, detail=str(e))

@router.put("/{project_id}")
async def update_project(project_id: str, project: ProjectInfoUpdate, db: SessionLocal = Depends(get_db)):  # type: ignore
    try:
        updated_project = update_project_by_id(db, project_id, project)
        if updated_project:
            project_data = get_project(db, project_id)
            await project_sse_manager.send_event(
                project_id,
                json.dumps(project_sse_manager.convert_to_dict(project_data))
            )
            logging.info(f"[SSE] Project {project_id} updated from Project update.")
        else:
            raise HTTPException(status_code=404, detail="Project not found")
        return updated_project
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.put("/{project_id}/member/{member_id}/permission")
async def update_project_member_permission_endpoint(project_id: str, member_id: int, permission: ProjectMemberPermission, db: SessionLocal = Depends(get_db)):  # type: ignore
    try:
        updated_project = update_project_member_permission(db, project_id, member_id, permission)
        if updated_project:
            project_data = get_project(db, project_id)
            await project_sse_manager.send_event(
                project_id,
                json.dumps(project_sse_manager.convert_to_dict(project_data))
            )
            logging.info(f"[SSE] Project {project_id} updated from Member {member_id} permission update.")
        else:
            raise HTTPException(status_code=404, detail="Project not found")
        return updated_project
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.put("/{project_id}/member/{member_id}/kick")
async def kick_out_member_from_project_endpoint(project_id: str, member_id: int, db: SessionLocal = Depends(get_db)):  # type: ignore
    try:
        result = await kick_out_member_from_project(db, project_id, member_id)
        logging.info(f"[SSE] Project {project_id} updated from Member {member_id} kick.")
        if result is None:
            raise HTTPException(status_code=404, detail=f"Member {member_id} or Project {project_id} not found")
        return {"status": "success", "message": f"Member {member_id} kicked from project {project_id}"}
    except Exception as e:
        logging.error(f"Error kicking member: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error kicking member: {str(e)}")

@router.put("/{project_id}/participationRequest/{member_id}/send")
async def send_project_participation_request_endpoint(project_id: str, member_id: int, db: SessionLocal = Depends(get_db)):  # type: ignore
    try:
        result = await send_project_participation_request(db, project_id, member_id)
        logging.info(f"[SSE] Project {project_id} updated from Member {member_id} send.")
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.put("/{project_id}/participationRequest/{member_id}/allow")
async def allow_project_participation_request_endpoint(project_id: str, member_id: int, db: SessionLocal = Depends(get_db)):  # type: ignore
    try:
        result = await allow_project_participation_request(db, project_id, member_id)
        logging.info(f"[SSE] Project {project_id} updated from Member {member_id} allow.")
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.put("/{project_id}/participationRequest/{member_id}/reject")
async def reject_project_participation_request_endpoint(project_id: str, member_id: int, db: SessionLocal = Depends(get_db)):  # type: ignore
    try:
        result = await reject_project_participation_request(db, project_id, member_id)
        logging.info(f"[SSE] Project {project_id} updated from Member {member_id} reject.")
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/{project_id}/member")
async def add_member_to_project_route(project_id: str, member_data: ProjectMemberAdd, db: SessionLocal = Depends(get_db)):  # type: ignore
    try:
        result = add_member_to_project(db, project_id, member_data.member_id)
        if result:
            project_data = get_project(db, project_id)
            await project_sse_manager.send_event(
                project_id,
                json.dumps(project_sse_manager.convert_to_dict(project_data))
            )
            logging.info(f"[SSE] Project {project_id} updated from Member {member_data.member_id} add.")
        else:
            raise HTTPException(status_code=404, detail="Project not found")
        if result.get("status") == "error":
            raise HTTPException(status_code=400, detail=result.get("message"))
        return result
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/{project_id}/member/{member_id}/scout")
async def scout_member_endpoint(project_id: str, member_id: int, member_data: ProjectMemberScout, db: SessionLocal = Depends(get_db)):  # type: ignore
    try:
        result = scout_member(db, project_id, member_id, member_data)
        logging.info(f"[SSE] Project {project_id} updated from Member {member_id} scout.")
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) 
    
@router.get("/{project_id}/sse")
async def project_sse(project_id: str, request: Request):
    queue = await project_sse_manager.connect(project_id)
    
    async def event_generator():
        db = SessionLocal()
        try:
            project = get_project(db, project_id)
            if project:
                project_dict = project_sse_manager.convert_to_dict(project)
                yield f"data: {json.dumps(project_dict)}\n\n"
        finally:
            db.close()
            
        async for event in project_sse_manager.event_generator(project_id, queue):
            if await request.is_disconnected():
                await project_sse_manager.disconnect(project_id, queue)
                break
            yield event
            
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