from sqlalchemy.orm import Session
from api.v1.models.project.channel import Channel
from api.v1.repositories.project.channel_repository import ChannelRepository
from api.v1.schemas.project.channel_schema import ChannelCreate, ChannelUpdate, ChannelDetail
from api.v1.schemas.brief import UserBrief
from typing import List

class ChannelService:
  def __init__(self, db: Session):
    self.channel_repository = ChannelRepository(db)
    
  def create(self, project_id: str, channel: ChannelCreate) -> Channel:
    return self.channel_repository.create(project_id, channel)
    
  def get(self, project_id: str, channel_id: str) -> ChannelDetail:
    return self.channel_repository.get(project_id, channel_id)
  
  def get_by_project_id(self, project_id: str, skip: int = 0, limit: int = 100) -> List[ChannelDetail]:
    return self.channel_repository.get_by_project_id(project_id, skip, limit)
    
  def get_public_channels_by_project(self, project_id: str, skip: int = 0, limit: int = 100) -> List[ChannelDetail]:
    return self.channel_repository.get_public_channels_by_project(project_id, skip, limit)
    
  def get_user_channels(self, user_id: int, skip: int = 0, limit: int = 100) -> List[ChannelDetail]:
    return self.channel_repository.get_user_channels(user_id, skip, limit)
    
  def get_user_channels_in_project(self, user_id: int, project_id: str, skip: int = 0, limit: int = 100) -> List[ChannelDetail]:
    return self.channel_repository.get_user_channels_in_project(user_id, project_id, skip, limit)
    
  def update(self, project_id: str, channel_id: str, channel: ChannelUpdate) -> ChannelDetail:
    return self.channel_repository.update(project_id, channel_id, channel)
    
  def delete(self, project_id: str, channel_id: str) -> bool:
    return self.channel_repository.delete(project_id, channel_id)
    
  def add_member_to_channel(self, project_id: str, channel_id: str, user_id: int, role: str = "member") -> bool:
    return self.channel_repository.add_member_to_channel(project_id, channel_id, user_id, role)
    
  def remove_member_from_channel(self, project_id: str, channel_id: str, user_id: int) -> bool:
    return self.channel_repository.remove_member_from_channel(project_id, channel_id, user_id)
    
  def get_channel_members(self, project_id: str, channel_id: str) -> List[UserBrief]:
    return self.channel_repository.get_channel_members(project_id, channel_id)
    
  def is_user_member_of_channel(self, project_id: str, channel_id: str, user_id: int) -> bool:
    return self.channel_repository.is_user_member_of_channel(project_id, channel_id, user_id)