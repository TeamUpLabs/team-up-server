from datetime import datetime
from typing import List, Optional
from sqlalchemy import select, update, and_, or_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Session
from sqlalchemy.sql import func

from new_models.participation_request import ParticipationRequest
from new_schemas.participation_request import ParticipationRequestCreate, ParticipationRequestUpdate


async def create_participation_request(
    db: AsyncSession, 
    request_data: ParticipationRequestCreate
) -> ParticipationRequest:
    """Create a new participation request or invitation"""
    db_request = ParticipationRequest(
        project_id=request_data.project_id,
        user_id=request_data.user_id,
        request_type=request_data.request_type,
        message=request_data.message,
        status="pending"
    )
    
    db.add(db_request)
    await db.commit()
    await db.refresh(db_request)
    return db_request


async def get_participation_request(
    db: AsyncSession, 
    request_id: int
) -> Optional[ParticipationRequest]:
    """Get a participation request by ID"""
    return await db.get(ParticipationRequest, request_id)


async def get_user_participation_requests(
    db: AsyncSession, 
    user_id: int, 
    request_type: Optional[str] = None,
    status: Optional[str] = None
) -> List[ParticipationRequest]:
    """Get all participation requests for a specific user"""
    query = select(ParticipationRequest).where(
        ParticipationRequest.user_id == user_id
    )
    
    if request_type:
        query = query.where(ParticipationRequest.request_type == request_type)
    
    if status:
        query = query.where(ParticipationRequest.status == status)
        
    result = await db.execute(query)
    return result.scalars().all()


async def get_project_participation_requests(
    db: AsyncSession, 
    project_id: str, 
    request_type: Optional[str] = None,
    status: Optional[str] = None
) -> List[ParticipationRequest]:
    """Get all participation requests for a specific project"""
    query = select(ParticipationRequest).where(
        ParticipationRequest.project_id == project_id
    )
    
    if request_type:
        query = query.where(ParticipationRequest.request_type == request_type)
    
    if status:
        query = query.where(ParticipationRequest.status == status)
        
    result = await db.execute(query)
    return result.scalars().all()


async def update_participation_request(
    db: AsyncSession, 
    request_id: int, 
    request_data: ParticipationRequestUpdate
) -> Optional[ParticipationRequest]:
    """Update a participation request status (accept/reject)"""
    db_request = await get_participation_request(db, request_id)
    if not db_request:
        return None
        
    db_request.status = request_data.status
    db_request.processed_at = datetime.now()
    
    await db.commit()
    await db.refresh(db_request)
    return db_request


async def check_existing_request(
    db: AsyncSession, 
    project_id: str, 
    user_id: int,
    request_type: Optional[str] = None
) -> Optional[ParticipationRequest]:
    """Check if there's already a pending request for the same project and user"""
    query = select(ParticipationRequest).where(
        and_(
            ParticipationRequest.project_id == project_id,
            ParticipationRequest.user_id == user_id,
            ParticipationRequest.status == "pending"
        )
    )
    
    if request_type:
        query = query.where(ParticipationRequest.request_type == request_type)
        
    result = await db.execute(query)
    return result.scalars().first()


def create_participation_request_sync(
    db: Session, 
    request_data: ParticipationRequestCreate
) -> ParticipationRequest:
    """Create a new participation request or invitation (synchronous version)"""
    db_request = ParticipationRequest(
        project_id=request_data.project_id,
        user_id=request_data.user_id,
        request_type=request_data.request_type,
        message=request_data.message,
        status="pending"
    )
    
    db.add(db_request)
    db.commit()
    db.refresh(db_request)
    return db_request


def get_participation_request_sync(
    db: Session, 
    request_id: int
) -> Optional[ParticipationRequest]:
    """Get a participation request by ID (synchronous version)"""
    return db.query(ParticipationRequest).filter(ParticipationRequest.id == request_id).first()


def get_user_participation_requests_sync(
    db: Session, 
    user_id: int, 
    request_type: Optional[str] = None,
    status: Optional[str] = None
) -> List[ParticipationRequest]:
    """Get all participation requests for a specific user (synchronous version)"""
    query = db.query(ParticipationRequest).filter(ParticipationRequest.user_id == user_id)
    
    if request_type:
        query = query.filter(ParticipationRequest.request_type == request_type)
    
    if status:
        query = query.filter(ParticipationRequest.status == status)
        
    return query.all()


def get_project_participation_requests_sync(
    db: Session, 
    project_id: str, 
    request_type: Optional[str] = None,
    status: Optional[str] = None
) -> List[ParticipationRequest]:
    """Get all participation requests for a specific project (synchronous version)"""
    query = db.query(ParticipationRequest).filter(ParticipationRequest.project_id == project_id)
    
    if request_type:
        query = query.filter(ParticipationRequest.request_type == request_type)
    
    if status:
        query = query.filter(ParticipationRequest.status == status)
        
    return query.all()


def update_participation_request_sync(
    db: Session, 
    request_id: int, 
    request_data: ParticipationRequestUpdate
) -> Optional[ParticipationRequest]:
    """Update a participation request status (accept/reject) (synchronous version)"""
    db_request = get_participation_request_sync(db, request_id)
    if not db_request:
        return None
        
    db_request.status = request_data.status
    db_request.processed_at = datetime.now()
    
    db.commit()
    db.refresh(db_request)
    return db_request


def check_existing_request_sync(
    db: Session, 
    project_id: str, 
    user_id: int,
    request_type: Optional[str] = None
) -> Optional[ParticipationRequest]:
    """Check if there's already a pending request for the same project and user (synchronous version)"""
    query = db.query(ParticipationRequest).filter(
        ParticipationRequest.project_id == project_id,
        ParticipationRequest.user_id == user_id,
        ParticipationRequest.status == "pending"
    )
    
    if request_type:
        query = query.filter(ParticipationRequest.request_type == request_type)
        
    return query.first() 