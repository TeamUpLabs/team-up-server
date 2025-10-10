from src.api.v1.models.project.chat import Chat
from src.api.v1.schemas.project.chat_schema import ChatCreate, ChatUpdate, ChatDetail
from sqlalchemy.orm import Session
from datetime import datetime
from fastapi import HTTPException
from typing import List

class ChatRepository:
  def __init__(self, db: Session):
      self.db = db
      
  def create(self, project_id: str, channel_id: str, user_id: int, chat: ChatCreate) -> Chat:
    """
    새 채팅 생성
    """
    db_obj = Chat(
      project_id=project_id,
      channel_id=channel_id,
      user_id=user_id,
      message=chat.message,
      timestamp=datetime.utcnow()
    )
    self.db.add(db_obj)
    self.db.commit()
    self.db.refresh(db_obj)
    return db_obj
  
  def get(self, project_id: str, channel_id: str, user_id: int, chat_id: int) -> ChatDetail:
    """
    채팅 조회
    """
    chat = self.db.query(Chat).filter(Chat.project_id == project_id, Chat.channel_id == channel_id, Chat.user_id == user_id, Chat.id == chat_id).first()
    if not chat:
      raise HTTPException(status_code=404, detail="채팅을 찾을 수 없습니다.")
    return ChatDetail.model_validate(chat, from_attributes=True)
  
  def get_by_project_id(self, project_id: str, skip: int = 0, limit: int = 100) -> List[ChatDetail]:
    """
    프로젝트별 채팅 조회
    """
    chats = self.db.query(Chat).filter(Chat.project_id == project_id).offset(skip).limit(limit).all()
    return [ChatDetail.model_validate(chat, from_attributes=True) for chat in chats]
    
  def get_by_channel_id(self, project_id: str, channel_id: str, skip: int = 0, limit: int = 100) -> List[ChatDetail]:
    """
    채널별 채팅 조회
    """
    chats = self.db.query(Chat).filter(Chat.project_id == project_id, Chat.channel_id == channel_id).offset(skip).limit(limit).all()
    return [ChatDetail.model_validate(chat, from_attributes=True) for chat in chats]
  
  def get_by_user_id(self, user_id: int, skip: int = 0, limit: int = 100) -> List[ChatDetail]:
    """
    사용자별 채팅 조회
    """
    chats = self.db.query(Chat).filter(Chat.user_id == user_id).offset(skip).limit(limit).all()
    return [ChatDetail.model_validate(chat, from_attributes=True) for chat in chats]
    
  def get_by_date_range(self, start_date: datetime, end_date: datetime, skip: int = 0, limit: int = 100) -> List[ChatDetail]:
    """
    날짜 범위별 채팅 조회
    """
    chats = self.db.query(Chat).filter(Chat.timestamp >= start_date, Chat.timestamp <= end_date).offset(skip).limit(limit).all()
    return [ChatDetail.model_validate(chat, from_attributes=True) for chat in chats]
    
  def search(self, search_term: str, skip: int = 0, limit: int = 100) -> List[ChatDetail]:
    """
    검색어로 채팅 조회
    """
    chats = self.db.query(Chat).filter(Chat.message.contains(search_term)).offset(skip).limit(limit).all()
    return [ChatDetail.model_validate(chat, from_attributes=True) for chat in chats]
    
  def update(self, project_id: str, channel_id: str, user_id: int, chat_id: int, chat: ChatUpdate) -> ChatDetail:
    """
    채팅 업데이트
    """
    chat = self.db.query(Chat).filter(Chat.project_id == project_id, Chat.channel_id == channel_id, Chat.user_id == user_id, Chat.id == chat_id).first()
    if not chat:
      raise HTTPException(status_code=404, detail="채팅을 찾을 수 없습니다.")
    chat.message = chat.message if chat.message is not None else chat.message
    self.db.commit()
    self.db.refresh(chat)
    return ChatDetail.model_validate(chat, from_attributes=True)
    
  def delete(self, project_id: str, channel_id: str, user_id: int, chat_id: int) -> bool:
    """
    채팅 삭제
    """
    chat = self.db.query(Chat).filter(Chat.project_id == project_id, Chat.channel_id == channel_id, Chat.user_id == user_id, Chat.id == chat_id).first()
    if not chat:
      raise HTTPException(status_code=404, detail="채팅을 찾을 수 없습니다.")
    self.db.delete(chat)
    self.db.commit()
    return True