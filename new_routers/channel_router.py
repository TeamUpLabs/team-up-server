from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from database import get_db
from new_crud.channel import ChannelCRUD
from new_schemas.channel import (
    ChannelCreate, ChannelUpdate, ChannelResponse,
    ChannelListResponse, ChannelMemberCreate, ChannelMemberResponse
)
from new_crud import user

router = APIRouter(prefix="/channels", tags=["channels"])

@router.post("/", response_model=ChannelResponse)
def create_channel(
    channel_data: ChannelCreate,
    db: Session = Depends(get_db)
):
    """새로운 채널 생성"""
    # 프로젝트 존재 확인
    project = user.get_project_by_id(db, channel_data.project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    # 채널 ID 중복 확인
    existing_channel = ChannelCRUD.get_channel_by_channel_id(db, channel_data.channel_id)
    if existing_channel:
        raise HTTPException(status_code=400, detail="Channel ID already exists")
    
    channel = ChannelCRUD.create_channel(
        db=db,
        project_id=channel_data.project_id,
        channel_id=channel_data.channel_id,
        name=channel_data.name,
        description=channel_data.description,
        is_public=channel_data.is_public
    )
    
    for member_id in channel_data.member_ids:
        member = user.get_user_by_id(db, member_id)
        if not member:
            raise HTTPException(status_code=404, detail="User not found")
        
        success = ChannelCRUD.add_member_to_channel(
            db=db,
            channel_id=channel.id,
            user_id=member_id,
            role=member.role
        )
        if not success:
            raise HTTPException(status_code=400, detail="User is already a member of this channel")
    
    return channel

@router.get("/{channel_id}", response_model=ChannelResponse)
def get_channel(channel_id: int, db: Session = Depends(get_db)):
    """채널 정보 조회"""
    channel = ChannelCRUD.get_channel_by_id(db, channel_id)
    if not channel:
        raise HTTPException(status_code=404, detail="Channel not found")
    
    return channel

@router.get("/project/{project_id}", response_model=List[ChannelResponse])
def get_project_channels(
    project_id: str,
    public_only: bool = Query(False, description="공개 채널만 조회"),
    db: Session = Depends(get_db)
):
    """프로젝트의 채널 목록 조회"""
    if public_only:
        channels = ChannelCRUD.get_public_channels_by_project(db, project_id)
    else:
        channels = ChannelCRUD.get_channels_by_project(db, project_id)
    
    return channels

@router.get("/user/{user_id}", response_model=List[ChannelResponse])
def get_user_channels(
    user_id: int,
    project_id: Optional[str] = Query(None, description="특정 프로젝트의 채널만 조회"),
    db: Session = Depends(get_db)
):
    """사용자가 참여 중인 채널 목록 조회"""
    if project_id:
        channels = ChannelCRUD.get_user_channels_in_project(db, user_id, project_id)
    else:
        channels = ChannelCRUD.get_user_channels(db, user_id)
    
    return channels

@router.put("/{channel_id}", response_model=ChannelResponse)
def update_channel(
    channel_id: int,
    channel_data: ChannelUpdate,
    db: Session = Depends(get_db)
):
    """채널 정보 업데이트"""
    channel = ChannelCRUD.update_channel(
        db=db,
        channel_id=channel_id,
        name=channel_data.name,
        description=channel_data.description,
        is_public=channel_data.is_public
    )
    
    if not channel:
        raise HTTPException(status_code=404, detail="Channel not found")
    
    return channel

@router.post("/{channel_id}/members", response_model=dict)
def add_member_to_channel(
    channel_id: int,
    member_data: ChannelMemberCreate,
    db: Session = Depends(get_db)
):
    """채널에 멤버 추가"""
    # 채널 존재 확인
    channel = ChannelCRUD.get_channel_by_id(db, channel_id)
    if not channel:
        raise HTTPException(status_code=404, detail="Channel not found")
    
    # 사용자 존재 확인
    user = user.get_user_by_id(db, member_data.user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    success = ChannelCRUD.add_member_to_channel(
        db=db,
        channel_id=channel_id,
        user_id=member_data.user_id,
        role=member_data.role
    )
    
    if not success:
        raise HTTPException(status_code=400, detail="User is already a member of this channel")
    
    return {"message": "Member added successfully"}

@router.delete("/{channel_id}/members/{user_id}")
def remove_member_from_channel(
    channel_id: int,
    user_id: int,
    db: Session = Depends(get_db)
):
    """채널에서 멤버 제거"""
    success = ChannelCRUD.remove_member_from_channel(db, channel_id, user_id)
    
    if not success:
        raise HTTPException(status_code=404, detail="Member not found in channel")
    
    return {"message": "Member removed successfully"}

@router.get("/{channel_id}/members", response_model=List[ChannelMemberResponse])
def get_channel_members(channel_id: int, db: Session = Depends(get_db)):
    """채널의 멤버 목록 조회"""
    # 채널 존재 확인
    channel = ChannelCRUD.get_channel_by_id(db, channel_id)
    if not channel:
        raise HTTPException(status_code=404, detail="Channel not found")
    
    members = ChannelCRUD.get_channel_members(db, channel_id)
    
    # 멤버 정보를 응답 형식에 맞게 변환
    member_responses = []
    for member in members:
        from new_models.association_tables import channel_members
        member_info = db.query(channel_members).filter(
            channel_members.c.channel_id == channel_id,
            channel_members.c.user_id == member.id
        ).first()
        
        member_responses.append(ChannelMemberResponse(
            user_id=member.id,
            name=member.name,
            email=member.email,
            profile_image=member.profile_image,
            role=member_info.role if member_info else "member",
            joined_at=member_info.joined_at if member_info else None
        ))
    
    return member_responses

@router.delete("/{channel_id}")
def delete_channel(channel_id: int, db: Session = Depends(get_db)):
    """채널 삭제"""
    success = ChannelCRUD.delete_channel(db, channel_id)
    
    if not success:
        raise HTTPException(status_code=404, detail="Channel not found")
    
    return {"message": "Channel deleted successfully"} 