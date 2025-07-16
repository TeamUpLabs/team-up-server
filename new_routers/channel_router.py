from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from database import get_db
from new_crud.channel import ChannelCRUD
from new_crud.chat import ChatCRUD
from new_schemas.channel import (
    ChannelCreate, ChannelUpdate, ChannelResponse,
    ChannelMemberCreate, ChannelMemberResponse
)
from new_crud import user, project
from new_routers.project_router import convert_project_to_project_detail
from utils.sse_manager import project_sse_manager
import json
from sqlalchemy.exc import SQLAlchemyError
from new_models.association_tables import channel_members

router = APIRouter(prefix="/api/channels", tags=["channels"])

@router.post("/", response_model=ChannelResponse)
async def create_channel(
    channel_data: ChannelCreate,
    db: Session = Depends(get_db)
):
    """새로운 채널 생성 (로직 전체 리뉴얼)"""
    # 1. 프로젝트 존재 확인
    db_project = project.get(db=db, id=channel_data.project_id)
    if not db_project:
        raise HTTPException(status_code=404, detail="Project not found")

    # 2. 채널 ID 중복 확인
    existing_channel = ChannelCRUD.get_channel_by_channel_id(db, channel_data.channel_id)
    if existing_channel:
        raise HTTPException(status_code=400, detail="Channel ID already exists")

    try:
        # 3. 채널 생성
        channel = ChannelCRUD.create_channel(
            db=db,
            project_id=channel_data.project_id,
            channel_id=channel_data.channel_id,
            name=channel_data.name,
            description=channel_data.description,
            is_public=channel_data.is_public,
            created_by=channel_data.created_by,
            updated_by=channel_data.updated_by
        )

        # 4. 멤버 추가 (중복은 무시, 예외 발생 X)
        added_members = []
        for member_id in channel_data.member_ids:
            member = user.get(db=db, id=member_id)
            if not member:
                db.rollback()
                raise HTTPException(status_code=404, detail=f"User not found: {member_id}")
            # 이미 멤버인지 확인
            member_info = db.query(channel_members).filter(
                channel_members.c.channel_id == channel.channel_id,
                channel_members.c.user_id == member_id
            ).first()
            if member_info:
                continue  # 이미 멤버면 무시
            success = ChannelCRUD.add_member_to_channel(
                db=db,
                channel_id=channel.channel_id,
                user_id=member_id,
                role=member.role
            )
            if success:
                added_members.append(member)
        db.commit()
    except SQLAlchemyError as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"DB Error: {str(e)}")

    # 5. SSE 전송 (최종 한 번만)
    project_data = convert_project_to_project_detail(project.get(db, channel_data.project_id), db)
    await project_sse_manager.send_event(
        channel_data.project_id,
        json.dumps(project_sse_manager.convert_to_dict(project_data))
    )

    # 6. 멤버 정보 변환
    member_responses = []
    for member_id in channel.member_ids:
        member_info = db.query(channel_members).filter(
            channel_members.c.channel_id == channel.channel_id,
            channel_members.c.user_id == member_id
        ).first()
        if not member_info or not member_info.joined_at:
            continue
        db_user = user.get_user_by_id(db, user_id=member_id)
        if not db_user:
            continue
        member_responses.append(ChannelMemberResponse(
            id=member_id,
            name=db_user.name,
            email=db_user.email,
            profile_image=getattr(db_user, 'profile_image', None),
            role=member_info.role,
            joined_at=member_info.joined_at
        ))
    channel_dict = channel.__dict__.copy()
    channel_dict['members'] = member_responses
    return channel_dict

@router.get("/{channel_id}", response_model=ChannelResponse)
def get_channel(channel_id: str, db: Session = Depends(get_db)):
    """채널 정보 조회"""
    channel = ChannelCRUD.get_channel_by_channel_id(db, channel_id)
    if not channel:
        raise HTTPException(status_code=404, detail="Channel not found")
    
    # 멤버 정보 변환 (create_channel과 동일하게)
    member_responses = []
    if channel.members:
        for member in channel.members:
            # Fetch association info from channel_members table
            member_info = db.query(channel_members).filter(
                channel_members.c.channel_id == channel.channel_id,
                channel_members.c.user_id == member.id
            ).first()
            if not member_info or not member_info.joined_at:
                continue
            member_responses.append(ChannelMemberResponse(
                id=member.id,
                name=member.name,
                email=member.email,
                profile_image=getattr(member, 'profile_image', None),
                role=member_info.role,
                joined_at=member_info.joined_at
            ))
    channel_dict = channel.__dict__.copy()
    channel_dict['members'] = member_responses
    channel_dict['chats'] = ChatCRUD.get_channel_chats(db, channel.channel_id)
    channel_dict['chats_count'] = len(channel_dict['chats'])
    return channel_dict

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
async def update_channel(
    channel_id: str,
    channel_data: ChannelUpdate,
    db: Session = Depends(get_db)
):
    """채널 정보 및 멤버 동기화 업데이트 (리뉴얼)"""
    from datetime import datetime
    # 1. 채널 존재 확인
    channel = ChannelCRUD.get_channel_by_channel_id(db, channel_id)
    if not channel:
        raise HTTPException(status_code=404, detail="Channel not found")

    try:
        # 2. 채널 정보 업데이트
        if channel_data.name is not None:
            channel.name = channel_data.name
        if channel_data.description is not None:
            channel.description = channel_data.description
        if channel_data.is_public is not None:
            channel.is_public = channel_data.is_public
        channel.updated_at = datetime.now()
        db.add(channel)

        # 3. 멤버 동기화
        if channel_data.member_ids is not None:
            # 현재 멤버 set
            current_member_ids = {m.id for m in channel.members}
            # 요청 멤버 set
            new_member_ids = set(channel_data.member_ids)

            # 추가해야 할 멤버
            to_add = new_member_ids - current_member_ids
            # 제거해야 할 멤버
            to_remove = current_member_ids - new_member_ids

            # 추가
            for user_id in to_add:
                db_user = user.get_user_by_id(db, user_id=user_id)
                if not db_user:
                    db.rollback()
                    raise HTTPException(status_code=404, detail=f"User not found: {user_id}")
                ChannelCRUD.add_member_to_channel(db, channel_id, user_id, role=db_user.role)

            # 제거
            for user_id in to_remove:
                ChannelCRUD.remove_member_from_channel(db, channel_id, user_id)

        db.commit()
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"DB Error: {str(e)}")

    # 4. SSE 전송
    project_data = convert_project_to_project_detail(project.get(db, channel.project_id), db)
    await project_sse_manager.send_event(
        channel.project_id,
        json.dumps(project_sse_manager.convert_to_dict(project_data))
    )

    # 5. 멤버 정보 변환 (create와 동일)
    member_responses = []
    for member in channel.members:
        member_info = db.query(channel_members).filter(
            channel_members.c.channel_id == channel.channel_id,
            channel_members.c.user_id == member.id
        ).first()
        if not member_info or not member_info.joined_at:
            continue
        member_responses.append(ChannelMemberResponse(
            id=member.id,
            name=member.name,
            email=member.email,
            profile_image=getattr(member, 'profile_image', None),
            role=member_info.role,
            joined_at=member_info.joined_at
        ))
    channel_dict = channel.__dict__.copy()
    channel_dict['members'] = member_responses
    channel_dict['chats'] = ChatCRUD.get_channel_chats(db, channel.channel_id)
    channel_dict['chats_count'] = len(channel_dict['chats'])
    return channel_dict

@router.post("/{channel_id}/members", response_model=dict)
async def add_member_to_channel(
    channel_id: str,
    member_data: ChannelMemberCreate,
    db: Session = Depends(get_db)
):
    """채널에 멤버 추가"""
    # 채널 존재 확인
    channel = ChannelCRUD.get_channel_by_channel_id(db, channel_id)
    if not channel:
        raise HTTPException(status_code=404, detail="Channel not found")
    
    # 사용자 존재 확인
    db_user = user.get_user_by_id(db, user_id=member_data.id)
    if not db_user:
        raise HTTPException(status_code=404, detail="User not found")
    
    success = ChannelCRUD.add_member_to_channel(
        db=db,
        channel_id=channel_id,
        user_id=member_data.id,
        role=member_data.role
    )
    
    if not success:
        raise HTTPException(status_code=400, detail="User is already a member of this channel")
    
    project_data = convert_project_to_project_detail(project.get(db, channel.project_id), db)
    await project_sse_manager.send_event(
        channel.project_id,
        json.dumps(project_sse_manager.convert_to_dict(project_data))
    )
    
    return {"message": "Member added successfully"}

@router.delete("/{channel_id}/members/{user_id}")
async def remove_member_from_channel(
    channel_id: str,
    user_id: int,
    db: Session = Depends(get_db)
):
    """채널에서 멤버 제거"""
    # 채널 존재 확인
    channel = ChannelCRUD.get_channel_by_channel_id(db, channel_id)
    if not channel:
        raise HTTPException(status_code=404, detail="Channel not found")
    
    # 사용자 존재 확인
    db_user = user.get_user_by_id(db, user_id=user_id)
    if not db_user:
        raise HTTPException(status_code=404, detail="User not found")
    
    success = ChannelCRUD.remove_member_from_channel(db, channel_id, user_id)
    
    if not success:
        raise HTTPException(status_code=404, detail="Member not found in channel")
    
    project_data = convert_project_to_project_detail(project.get(db, channel.project_id), db)
    await project_sse_manager.send_event(
        channel.project_id,
        json.dumps(project_sse_manager.convert_to_dict(project_data))
    )
    
    return {"message": "Member removed successfully"}

@router.get("/{channel_id}/members", response_model=List[ChannelMemberResponse])
def get_channel_members(channel_id: str, db: Session = Depends(get_db)):
    """채널의 멤버 목록 조회"""
    # 채널 존재 확인
    channel = ChannelCRUD.get_channel_by_channel_id(db, channel_id)
    if not channel:
        raise HTTPException(status_code=404, detail="Channel not found")
    
    members = ChannelCRUD.get_channel_members(db, channel_id)
    
    # 멤버 정보를 응답 형식에 맞게 변환
    member_responses = []
    for member in members:
        member_info = db.query(channel_members).filter(
            channel_members.c.channel_id == channel_id,
            channel_members.c.user_id == member.id
        ).first()
        
        # member_info가 없거나 joined_at이 없으면 응답에서 제외
        if not member_info or not member_info.joined_at:
            continue

        member_responses.append(ChannelMemberResponse(
            id=member.id,
            name=member.name,
            email=member.email,
            profile_image=member.profile_image,
            role=member_info.role,
            joined_at=member_info.joined_at
        ))
    
    return member_responses

@router.delete("/{channel_id}")
async def delete_channel(channel_id: str, db: Session = Depends(get_db)):
    """채널 삭제"""
    # 채널 존재 확인
    channel = ChannelCRUD.get_channel_by_channel_id(db, channel_id)
    if not channel:
        raise HTTPException(status_code=404, detail="Channel not found")
    
    success = ChannelCRUD.delete_channel(db, channel_id)
    
    if not success:
        raise HTTPException(status_code=404, detail="Channel not found")
    
    project_data = convert_project_to_project_detail(project.get(db, channel.project_id), db)
    await project_sse_manager.send_event(
        channel.project_id,
        json.dumps(project_sse_manager.convert_to_dict(project_data))
    )
    
    return {"message": "Channel deleted successfully"} 