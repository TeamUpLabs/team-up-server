from api.v1.models.project.channel import Channel
from api.v1.models.user import User
from api.v1.schemas.project.channel_schema import ChannelCreate, ChannelUpdate, ChannelDetail, ChannelMemberResponse
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
  
  def _to_detail(self, db_obj: Channel) -> ChannelDetail:
    """ORM Channel -> ChannelDetail 스키마로 안전하게 변환
    관계 필드(예: members)는 스키마 형태와 달라 ValidationError가 발생할 수 있으므로
    필요한 원시 컬럼만 매핑하여 반환한다.
    """
    # 채널 멤버 로드 (User + role, joined_at 포함)
    member_rows = (
      self.db.query(
        User,
        channel_members.c.role,
        channel_members.c.joined_at,
      )
      .join(channel_members, User.id == channel_members.c.user_id)
      .filter(channel_members.c.channel_id == db_obj.channel_id)
      .all()
    )

    members = [
      ChannelMemberResponse(
        user=UserBrief.model_validate(user, from_attributes=True),
        role=role,
        joined_at=joined_at,
      )
      for (user, role, joined_at) in member_rows
    ]

    return ChannelDetail(
      project_id=db_obj.project_id,
      channel_id=db_obj.channel_id,
      name=db_obj.name,
      description=db_obj.description,
      is_public=db_obj.is_public,
      created_at=db_obj.created_at,
      updated_at=db_obj.updated_at,
      created_by=db_obj.created_by,
      updated_by=db_obj.updated_by,
      member_count=len(members),
      members=members,
      chats_count=0,
    )
    
  def create(self, project_id: str, channel: ChannelCreate) -> ChannelDetail:
    """
    새 채널 생성
    """
    try:
      # 채널 레코드 생성
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
      self.db.flush()  # 채널 PK가 있는 경우 확보, 여기선 channel_id를 직접 지정함

      # 멤버 연결 추가 (중복 없이 입력 가정: 새 채널)
      if getattr(channel, "member_ids", None):
        values = [
          {
            "channel_id": channel.channel_id,
            "user_id": user_id,
            "role": "member",
            "joined_at": datetime.utcnow(),
          }
          for user_id in channel.member_ids
        ]
        if values:
          self.db.execute(channel_members.insert(), values)

      self.db.commit()
      self.db.refresh(db_obj)

      return self._to_detail(db_obj)
    except Exception as e:
      self.db.rollback()
      raise e
  
  def get(self, project_id: str, channel_id: str) -> ChannelDetail:
    """
    채널 조회
    """
    channel = self.db.query(Channel).filter(Channel.project_id == project_id, Channel.channel_id == channel_id).first()
    if not channel:
      raise HTTPException(status_code=404, detail="채널을 찾을 수 없습니다.")
    return self._to_detail(channel)
  
  def get_by_project_id(self, project_id: str, skip: int = 0, limit: int = 100) -> List[ChannelDetail]:
    """
    프로젝트별 채널 조회
    """
    channels = self.db.query(Channel).filter(Channel.project_id == project_id).offset(skip).limit(limit).all()
    return [self._to_detail(channel) for channel in channels]
  
  def get_public_channels_by_project(self, project_id: str, skip: int = 0, limit: int = 100) -> List[ChannelDetail]:
    """
    프로젝트별 공개 채널 조회
    """
    channels = self.db.query(Channel).filter(Channel.project_id == project_id, Channel.is_public == True).offset(skip).limit(limit).all()
    return [self._to_detail(channel) for channel in channels]
  
  def get_user_channels(self, user_id: int, skip: int = 0, limit: int = 100) -> List[ChannelDetail]:
    """
    사용자별 채널 조회
    """
    channels = self.db.query(Channel).filter(Channel.created_by == user_id).offset(skip).limit(limit).all()
    return [self._to_detail(channel) for channel in channels]
    
  def get_user_channels_in_project(self, user_id: int, project_id: str, skip: int = 0, limit: int = 100) -> List[ChannelDetail]:
    """
    사용자별 프로젝트 채널 조회
    """
    channels = self.db.query(Channel).filter(Channel.created_by == user_id, Channel.project_id == project_id).offset(skip).limit(limit).all()
    return [self._to_detail(channel) for channel in channels]
    
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