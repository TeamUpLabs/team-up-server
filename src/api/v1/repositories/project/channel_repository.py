from api.v1.models.project.channel import Channel
from api.v1.models.user import User
from api.v1.schemas.project.channel_schema import ChannelCreate, ChannelUpdate, ChannelDetail
from api.v1.schemas.brief import UserBrief
from sqlalchemy.orm import Session
from datetime import datetime
from fastapi import HTTPException
from typing import List
from sqlalchemy import and_
from api.v1.models.association_tables import channel_members

class ChannelRepository:
  def __init__(self, db: Session):
    self.db = db
    
  def create(self, project_id: str, channel: ChannelCreate) -> Channel:
    """
    새 채널 생성
    """
    db_obj = Channel(
      project_id=project_id,
      channel_id=channel.channel_id,
      name=channel.name,
      description=channel.description,
      is_public=channel.is_public,
      created_by=channel.created_by,
      updated_by=channel.updated_by,
      created_at=datetime.now(),
      updated_at=datetime.now()
    )
    self.db.add(db_obj)
    self.db.commit()
    self.db.refresh(db_obj)
    return db_obj
  
  def get(self, project_id: str, channel_id: str) -> ChannelDetail:
    """
    채널 조회
    """
    channel = self.db.query(Channel).filter(Channel.project_id == project_id, Channel.channel_id == channel_id).first()
    if not channel:
      raise HTTPException(status_code=404, detail="채널을 찾을 수 없습니다.")
    return ChannelDetail.model_validate(channel, from_attributes=True)
  
  def get_by_project_id(self, project_id: str, skip: int = 0, limit: int = 100) -> List[ChannelDetail]:
    """
    프로젝트별 채널 조회
    """
    channels = self.db.query(Channel).filter(Channel.project_id == project_id).offset(skip).limit(limit).all()
    return [ChannelDetail.model_validate(channel, from_attributes=True) for channel in channels]
  
  def get_public_channels_by_project(self, project_id: str, skip: int = 0, limit: int = 100) -> List[ChannelDetail]:
    """
    프로젝트별 공개 채널 조회
    """
    channels = self.db.query(Channel).filter(Channel.project_id == project_id, Channel.is_public == True).offset(skip).limit(limit).all()
    return [ChannelDetail.model_validate(channel, from_attributes=True) for channel in channels]
  
  def get_user_channels(self, user_id: int, skip: int = 0, limit: int = 100) -> List[ChannelDetail]:
    """
    사용자별 채널 조회
    """
    channels = self.db.query(Channel).filter(Channel.created_by == user_id).offset(skip).limit(limit).all()
    return [ChannelDetail.model_validate(channel, from_attributes=True) for channel in channels]
    
  def get_user_channels_in_project(self, user_id: int, project_id: str, skip: int = 0, limit: int = 100) -> List[ChannelDetail]:
    """
    사용자별 프로젝트 채널 조회
    """
    channels = self.db.query(Channel).filter(Channel.created_by == user_id, Channel.project_id == project_id).offset(skip).limit(limit).all()
    return [ChannelDetail.model_validate(channel, from_attributes=True) for channel in channels]
    
  def update(self, project_id: str, channel_id: str, channel: ChannelUpdate) -> ChannelDetail:
    """
    채널 업데이트
    """
    db_obj = self.db.query(Channel).filter(Channel.project_id == project_id, Channel.channel_id == channel_id).first()
    if not db_obj:
      raise HTTPException(status_code=404, detail="채널을 찾을 수 없습니다.")
    db_obj.name = channel.name if channel.name is not None else db_obj.name
    db_obj.description = channel.description if channel.description is not None else db_obj.description
    db_obj.is_public = channel.is_public if channel.is_public is not None else db_obj.is_public
    db_obj.updated_by = channel.updated_by if channel.updated_by is not None else db_obj.updated_by
    db_obj.updated_at = datetime.now()
    self.db.commit()
    self.db.refresh(db_obj)
    return ChannelDetail.model_validate(db_obj, from_attributes=True)
  
  def delete(self, project_id: str, channel_id: str) -> bool:
    """
    채널 삭제
    """
    db_obj = self.db.query(Channel).filter(Channel.project_id == project_id, Channel.channel_id == channel_id).first()
    if not db_obj:
      raise HTTPException(status_code=404, detail="채널을 찾을 수 없습니다.")
    self.db.delete(db_obj)
    self.db.commit()
    return True
    
  def add_member_to_channel(self, project_id: str, channel_id: str, user_id: int, role: str = "member") -> bool:
    """
    채널에 멤버 추가
    """
    try:
      channel = self.db.query(Channel).filter(Channel.project_id == project_id, Channel.channel_id == channel_id).first()
      if not channel:
        raise HTTPException(status_code=404, detail="채널을 찾을 수 없습니다.")
      
      # 이미 멤버인지 확인
      existing_member = self.db.query(channel_members).filter(
          and_(
              channel_members.c.channel_id == channel_id,
              channel_members.c.user_id == user_id
          )
      ).first()
      
      if existing_member:
          return False  # 이미 멤버임
      
      # 새 멤버 추가
      self.db.execute(
          channel_members.insert().values(
              channel_id=channel_id,
              user_id=user_id,
              role=role,
              joined_at=datetime.utcnow()
          )
      )
      self.db.commit()
      return True
    except Exception:
      self.db.rollback()
      return False
    
  def remove_member_from_channel(self, project_id: str, channel_id: str, user_id: int) -> bool:
    """
    채널에서 멤버 제거
    """
    try:
      channel = self.db.query(Channel).filter(Channel.project_id == project_id, Channel.channel_id == channel_id).first()
      if not channel:
        raise HTTPException(status_code=404, detail="채널을 찾을 수 없습니다.")
      
      result = self.db.execute(
          channel_members.delete().where(
              and_(
                  channel_members.c.channel_id == channel_id,
                  channel_members.c.user_id == user_id
              )
          )
      )
      self.db.commit()
      return result.rowcount > 0
    except Exception:
      self.db.rollback()
      return False
    
  def get_channel_members(self, project_id: str, channel_id: str) -> List[UserBrief]:
    """
    채널의 모든 멤버 조회
    """
    channel = self.db.query(Channel).filter(Channel.project_id == project_id, Channel.channel_id == channel_id).first()
    if not channel:
      raise HTTPException(status_code=404, detail="채널을 찾을 수 없습니다.")
    
    users = self.db.query(User).join(channel_members).filter(
        and_(
          channel_members.c.channel_id == channel_id,
        )
    ).all()
    
    return [UserBrief.model_validate(user, from_attributes=True) for user in users]
    
  def is_user_member_of_channel(self, project_id: str, channel_id: str, user_id: int) -> bool:
    """
    사용자가 채널의 멤버인지 확인
    """
    channel = self.db.query(Channel).filter(Channel.project_id == project_id, Channel.channel_id == channel_id).first()
    if not channel:
      raise HTTPException(status_code=404, detail="채널을 찾을 수 없습니다.")
    
    member = self.db.query(channel_members).filter(
        and_(
            channel_members.c.channel_id == channel_id,
            channel_members.c.user_id == user_id
        )
    ).first()
    return member is not None