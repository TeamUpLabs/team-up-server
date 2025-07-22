from fastapi import APIRouter, Depends, HTTPException, Query, WebSocket, WebSocketDisconnect
from sqlalchemy.orm import Session
from typing import List, Optional
from database import get_db
from crud.chat import ChatCRUD
from crud.channel import ChannelCRUD
from schemas.chat import (
    ChatCreate, ChatUpdate, ChatResponse, ChatListResponse,
    ChatSearchRequest, ChatDateRangeRequest
)
from websocket.chat import websocket_handler
import logging

router = APIRouter(prefix="/api/chats", tags=["chats"])

@router.post("/", response_model=ChatResponse)
def create_chat(
    chat_data: ChatCreate,
    user_id: int = Query(..., description="메시지 작성자 ID"),
    db: Session = Depends(get_db)
):
    """새로운 채팅 메시지 생성"""
    # 채널 존재 확인
    channel = ChannelCRUD.get_channel_by_id(db, chat_data.channel_id)
    if not channel:
        raise HTTPException(status_code=404, detail="Channel not found")
    
    # 사용자가 채널의 멤버인지 확인
    is_member = ChannelCRUD.is_user_member_of_channel(db, chat_data.channel_id, user_id)
    if not is_member:
        raise HTTPException(status_code=403, detail="User is not a member of this channel")
    
    chat = ChatCRUD.create_chat(
        db=db,
        project_id=chat_data.project_id,
        channel_id=chat_data.channel_id,
        user_id=user_id,
        message=chat_data.message
    )
    
    # 사용자 정보와 함께 응답
    chat_with_user = ChatCRUD.get_chat_with_user_info(db, chat.id)
    return chat_with_user

@router.get("/{chat_id}", response_model=ChatResponse)
def get_chat(chat_id: int, db: Session = Depends(get_db)):
    """채팅 메시지 조회"""
    chat = ChatCRUD.get_chat_with_user_info(db, chat_id)
    if not chat:
        raise HTTPException(status_code=404, detail="Chat not found")
    
    return chat

@router.get("/channel/{channel_id}", response_model=List[ChatResponse])
def get_channel_chats(
    channel_id: str,
    limit: int = Query(50, ge=1, le=100, description="조회할 메시지 수"),
    offset: int = Query(0, ge=0, description="건너뛸 메시지 수"),
    db: Session = Depends(get_db)
):
    """채널의 채팅 메시지 조회"""
    # 채널 존재 확인
    channel = ChannelCRUD.get_channel_by_channel_id(db, channel_id)
    if not channel:
        raise HTTPException(status_code=404, detail="Channel not found")
    
    chats = ChatCRUD.get_channel_chats_with_user_info(db, channel_id, limit, offset)
    return chats

@router.get("/project/{project_id}", response_model=List[ChatResponse])
def get_project_chats(
    project_id: str,
    limit: int = Query(50, ge=1, le=100, description="조회할 메시지 수"),
    offset: int = Query(0, ge=0, description="건너뛸 메시지 수"),
    db: Session = Depends(get_db)
):
    """프로젝트의 모든 채팅 메시지 조회"""
    chats = ChatCRUD.get_project_chats(db, project_id, limit, offset)
    
    # 사용자 정보와 함께 응답
    chats_with_user = []
    for chat in chats:
        chat_with_user = ChatCRUD.get_chat_with_user_info(db, chat.id)
        if chat_with_user:
            chats_with_user.append(chat_with_user)
    
    return chats_with_user

@router.get("/user/{user_id}", response_model=List[ChatResponse])
def get_user_chats(
    user_id: int,
    limit: int = Query(50, ge=1, le=100, description="조회할 메시지 수"),
    offset: int = Query(0, ge=0, description="건너뛸 메시지 수"),
    db: Session = Depends(get_db)
):
    """사용자가 작성한 채팅 메시지 조회"""
    chats = ChatCRUD.get_user_chats(db, user_id, limit, offset)
    
    # 사용자 정보와 함께 응답
    chats_with_user = []
    for chat in chats:
        chat_with_user = ChatCRUD.get_chat_with_user_info(db, chat.id)
        if chat_with_user:
            chats_with_user.append(chat_with_user)
    
    return chats_with_user

@router.post("/channel/{channel_id}/search", response_model=List[ChatResponse])
def search_channel_chats(
    channel_id: str,
    search_request: ChatSearchRequest,
    db: Session = Depends(get_db)
):
    """채널에서 메시지 검색"""
    # 채널 존재 확인
    channel = ChannelCRUD.get_channel_by_channel_id(db, channel_id)
    if not channel:
        raise HTTPException(status_code=404, detail="Channel not found")
    
    chats = ChatCRUD.search_chats(
        db=db,
        channel_id=channel_id,
        search_term=search_request.search_term,
        limit=search_request.limit
    )
    
    # 사용자 정보와 함께 응답
    chats_with_user = []
    for chat in chats:
        chat_with_user = ChatCRUD.get_chat_with_user_info(db, chat.id)
        if chat_with_user:
            chats_with_user.append(chat_with_user)
    
    return chats_with_user

@router.post("/channel/{channel_id}/date-range", response_model=List[ChatResponse])
def get_chats_by_date_range(
    channel_id: str,
    date_request: ChatDateRangeRequest,
    db: Session = Depends(get_db)
):
    """특정 기간의 채팅 메시지 조회"""
    # 채널 존재 확인
    channel = ChannelCRUD.get_channel_by_channel_id(db, channel_id)
    if not channel:
        raise HTTPException(status_code=404, detail="Channel not found")
    
    chats = ChatCRUD.get_chats_by_date_range(
        db=db,
        channel_id=channel_id,
        start_date=date_request.start_date,
        end_date=date_request.end_date,
        limit=date_request.limit
    )
    
    # 사용자 정보와 함께 응답
    chats_with_user = []
    for chat in chats:
        chat_with_user = ChatCRUD.get_chat_with_user_info(db, chat.id)
        if chat_with_user:
            chats_with_user.append(chat_with_user)
    
    return chats_with_user

@router.put("/{chat_id}", response_model=ChatResponse)
def update_chat(
    chat_id: int,
    chat_data: ChatUpdate,
    user_id: int = Query(..., description="메시지 수정자 ID"),
    db: Session = Depends(get_db)
):
    """채팅 메시지 수정"""
    # 채팅 메시지 존재 확인
    chat = ChatCRUD.get_chat_by_id(db, chat_id)
    if not chat:
        raise HTTPException(status_code=404, detail="Chat not found")
    
    # 메시지 작성자만 수정 가능
    if chat.user_id != user_id:
        raise HTTPException(status_code=403, detail="Only the message author can edit the message")
    
    updated_chat = ChatCRUD.update_chat(
        db=db,
        chat_id=chat_id,
        message=chat_data.message
    )
    
    if not updated_chat:
        raise HTTPException(status_code=404, detail="Chat not found")
    
    # 사용자 정보와 함께 응답
    chat_with_user = ChatCRUD.get_chat_with_user_info(db, updated_chat.id)
    return chat_with_user

@router.delete("/{chat_id}")
def delete_chat(
    chat_id: int,
    user_id: int = Query(..., description="메시지 삭제자 ID"),
    db: Session = Depends(get_db)
):
    """채팅 메시지 삭제"""
    # 채팅 메시지 존재 확인
    chat = ChatCRUD.get_chat_by_id(db, chat_id)
    if not chat:
        raise HTTPException(status_code=404, detail="Chat not found")
    
    # 메시지 작성자만 삭제 가능
    if chat.user_id != user_id:
        raise HTTPException(status_code=403, detail="Only the message author can delete the message")
    
    success = ChatCRUD.delete_chat(db, chat_id)
    
    if not success:
        raise HTTPException(status_code=404, detail="Chat not found")
    
    return {"message": "Chat deleted successfully"} 

@router.websocket("/ws")
async def chat_endpoint(
    websocket: WebSocket,
    project_id: str = Query(..., alias="project_id"),
    channel_id: str = Query(..., alias="channel_id"),
    user_id: int = Query(..., alias="user_id"),
    db: Session = Depends(get_db)
):
    """
    WebSocket 채팅 엔드포인트
    - 쿼리 파라미터로 반드시 user_id를 전달해야 합니다.
    예: ws://.../api/chats/ws?project_id=xxx&channel_id=yyy&user_id=zzz
    """
    try:
        await websocket_handler(websocket, channel_id, project_id, user_id, db)
    except WebSocketDisconnect:
        logging.info(f"WebSocket disconnected for project: {project_id}, channel: {channel_id}")
    except Exception as e:
        logging.error(f"WebSocket error in project {project_id}, channel {channel_id}: {str(e)}")
        try:
            await websocket.close()
        except Exception:
            logging.error("WebSocket close failed")