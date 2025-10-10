from src.api.v1.repositories.project.chat_repository import ChatRepository
from sqlalchemy.orm import Session
from src.api.v1.schemas.project.chat_schema import ChatCreate, ChatDetail, ChatUpdate
from typing import List
from datetime import datetime

class ChatService:
  def __init__(self, db: Session):
    self.repository = ChatRepository(db)
  
  def create(self, project_id: str, channel_id: str, user_id: int, chat: ChatCreate) -> ChatDetail:
    return self.repository.create(project_id, channel_id, user_id, chat)
  
  def get(self, project_id: str, channel_id: str, user_id: int, chat_id: int) -> ChatDetail:
    return self.repository.get(project_id, channel_id, user_id, chat_id)

  def get_by_project_id(self, project_id: str, skip: int = 0, limit: int = 100) -> List[ChatDetail]:
    return self.repository.get_by_project_id(project_id, skip, limit)

  def get_by_channel_id(self, project_id: str, channel_id: str, skip: int = 0, limit: int = 100) -> List[ChatDetail]:
    return self.repository.get_by_channel_id(project_id, channel_id, skip, limit)

  def get_by_user_id(self, user_id: int, skip: int = 0, limit: int = 100) -> List[ChatDetail]:
    return self.repository.get_by_user_id(user_id, skip, limit)

  def get_by_date_range(self, start_date: datetime, end_date: datetime, skip: int = 0, limit: int = 100) -> List[ChatDetail]:
    return self.repository.get_by_date_range(start_date, end_date, skip, limit)

  def search(self, search_term: str, skip: int = 0, limit: int = 100) -> List[ChatDetail]:
    return self.repository.search(search_term, skip, limit)

  def update(self, project_id: str, channel_id: str, user_id: int, chat_id: int, chat: ChatUpdate) -> ChatDetail:
    return self.repository.update(project_id, channel_id, user_id, chat_id, chat)

  def delete(self, project_id: str, channel_id: str, user_id: int, chat_id: int) -> bool:
    return self.repository.delete(project_id, channel_id, user_id, chat_id)