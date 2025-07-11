from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query, Path
from sqlalchemy.orm import Session
from new_crud import project
from database import get_db
from new_crud import participation_request as crud
from new_schemas.participation_request import (
    ParticipationRequestCreate,
    ParticipationRequestResponse,
    ParticipationRequestUpdate,
    ParticipationRequestList
)
from utils.sse_manager import project_sse_manager
from new_routers.project_router import convert_project_to_project_detail
import json


router = APIRouter(
    prefix="/api/participation-requests",
    tags=["participation requests"]
)


@router.post("/", response_model=ParticipationRequestResponse)
async def create_participation_request(
    request_data: ParticipationRequestCreate,
    db: Session = Depends(get_db)
):
    """
    Create a new participation request:
    - If request_type is 'request', a user is requesting to join a project
    - If request_type is 'invitation', a project leader/manager is inviting a user
    """
    # Check if there's already a pending request
    existing_request = crud.check_existing_request_sync(
        db, 
        request_data.project_id, 
        request_data.user_id
    )
    
    if existing_request:
        raise HTTPException(
            status_code=400,
            detail="There is already a pending request for this user and project"
        )
  
    
    result = crud.create_participation_request_sync(db, request_data)
    db_project = project.get(db=db, id=result.project_id)
    
    if db_project:
      project_detail = convert_project_to_project_detail(db_project, db)
      await project_sse_manager.send_event(
          db_project.id,
          json.dumps(project_sse_manager.convert_to_dict(project_detail))
      )
    return result


@router.get("/{request_id}", response_model=ParticipationRequestResponse)
def get_participation_request(
    request_id: int = Path(...),
    db: Session = Depends(get_db)
):
    """Get a participation request by ID"""
    result = crud.get_participation_request_sync(db, request_id)
    
    if not result:
        raise HTTPException(
            status_code=404,
            detail="Participation request not found"
        )
    
    return result


@router.get("/user/{user_id}", response_model=ParticipationRequestList)
def list_user_participation_requests(
    user_id: int = Path(...),
    request_type: Optional[str] = Query(None, description="Filter by request type (invitation/request)"),
    status: Optional[str] = Query(None, description="Filter by status (pending/accepted/rejected)"),
    db: Session = Depends(get_db)
):
    """List all participation requests for a user"""
    results = crud.get_user_participation_requests_sync(
        db, 
        user_id, 
        request_type=request_type, 
        status=status
    )
    
    return {
        "items": results,
        "total": len(results)
    }


@router.get("/project/{project_id}", response_model=ParticipationRequestList)
def list_project_participation_requests(
    project_id: str = Path(...),
    request_type: Optional[str] = Query(None, description="Filter by request type (invitation/request)"),
    status: Optional[str] = Query(None, description="Filter by status (pending/accepted/rejected)"),
    db: Session = Depends(get_db)
):
    """List all participation requests for a project"""
    results = crud.get_project_participation_requests_sync(
        db, 
        project_id, 
        request_type=request_type, 
        status=status
    )
    
    return {
        "items": results,
        "total": len(results)
    }


@router.put("/{request_id}", response_model=ParticipationRequestResponse)
async def update_participation_request_status(
    request_data: ParticipationRequestUpdate,
    request_id: int = Path(...),
    db: Session = Depends(get_db)
):
    """Update a participation request (accept/reject)"""
    existing_request = crud.get_participation_request_sync(db, request_id)
    
    if not existing_request:
        raise HTTPException(
            status_code=404,
            detail="Participation request not found"
        )
    
    result = crud.update_participation_request_sync(db, request_id, request_data)
    
    if request_data.status == "accepted":
      project.add_member(db=db, project_id=existing_request.project_id, user_id=existing_request.user_id)
      
    db_project = project.get(db=db, id=existing_request.project_id)
      
    if db_project:
        project_detail = convert_project_to_project_detail(db_project, db)
        await project_sse_manager.send_event(
            db_project.id,
            json.dumps(project_sse_manager.convert_to_dict(project_detail))
        )
    
    return result 