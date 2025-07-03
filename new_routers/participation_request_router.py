from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query, Path
from sqlalchemy.orm import Session

from database import get_db
from new_crud import participation_request as crud
from new_schemas.participation_request import (
    ParticipationRequestCreate,
    ParticipationRequestResponse,
    ParticipationRequestUpdate,
    ParticipationRequestList
)


router = APIRouter(
    prefix="/api/participation-requests",
    tags=["participation requests"]
)


@router.post("/", response_model=ParticipationRequestResponse)
def create_participation_request(
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
    
    # TODO: Add authentication check to ensure:
    # - For 'invitation': Only project leaders/managers can create invitations
    # - For 'request': Users can only create requests for themselves
    
    result = crud.create_participation_request_sync(db, request_data)
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
def update_participation_request_status(
    request_data: ParticipationRequestUpdate,
    request_id: int = Path(...),
    db: Session = Depends(get_db)
):
    """Update a participation request (accept/reject)"""
    # First, check if the request exists
    existing_request = crud.get_participation_request_sync(db, request_id)
    
    if not existing_request:
        raise HTTPException(
            status_code=404,
            detail="Participation request not found"
        )
    
    # TODO: Add authentication checks to ensure:
    # - For 'invitation': Only the invited user can accept/reject
    # - For 'request': Only project leaders/managers can accept/reject
    
    result = crud.update_participation_request_sync(db, request_id, request_data)
    
    # If the request is accepted, add the user to the project members
    # This would be handled in a service layer in a more complex application
    if request_data.status == "accepted":
        # TODO: Add logic to insert into project_members table
        pass
    
    return result 