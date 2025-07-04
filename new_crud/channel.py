from sqlalchemy.orm import Session
from sqlalchemy import and_
from typing import List, Optional
from new_models.channel import Channel
from new_models.user import User
from new_models.association_tables import channel_members
from datetime import datetime

class ChannelCRUD:
    """채널 관련 CRUD 작업"""
    
    @staticmethod
    def create_channel(
        db: Session,
        project_id: str,
        channel_id: str,
        name: str,
        description: Optional[str] = None,
        is_public: bool = True,
        created_by: int = None
    ) -> Channel:
        """새로운 채널 생성"""
        channel = Channel(
            project_id=project_id,
            channel_id=channel_id,
            name=name,
            description=description,
            is_public=is_public,
            created_by=created_by,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        db.add(channel)
        db.commit()
        db.refresh(channel)
        return channel
    
    @staticmethod
    def get_channel_by_id(db: Session, channel_id: int) -> Optional[Channel]:
        """ID로 채널 조회"""
        return db.query(Channel).filter(Channel.id == channel_id).first()
    
    @staticmethod
    def get_channel_by_channel_id(db: Session, channel_id: str) -> Optional[Channel]:
        """채널 ID로 채널 조회"""
        return db.query(Channel).filter(Channel.channel_id == channel_id).first()
    
    @staticmethod
    def get_channels_by_project(db: Session, project_id: str) -> List[Channel]:
        """프로젝트의 모든 채널 조회"""
        return db.query(Channel).filter(Channel.project_id == project_id).all()
    
    @staticmethod
    def get_public_channels_by_project(db: Session, project_id: str) -> List[Channel]:
        """프로젝트의 공개 채널만 조회"""
        return db.query(Channel).filter(
            and_(Channel.project_id == project_id, Channel.is_public == True)
        ).all()
    
    @staticmethod
    def get_user_channels(db: Session, user_id: int) -> List[Channel]:
        """사용자가 참여 중인 모든 채널 조회"""
        return db.query(Channel).join(channel_members).filter(
            channel_members.c.user_id == user_id
        ).all()
    
    @staticmethod
    def get_user_channels_in_project(db: Session, user_id: int, project_id: str) -> List[Channel]:
        """사용자가 특정 프로젝트에서 참여 중인 채널 조회"""
        return db.query(Channel).join(channel_members).filter(
            and_(
                channel_members.c.user_id == user_id,
                Channel.project_id == project_id
            )
        ).all()
    
    @staticmethod
    def add_member_to_channel(db: Session, channel_id: int, user_id: int, role: str = "member") -> bool:
        """채널에 멤버 추가"""
        try:
            # 이미 멤버인지 확인
            existing_member = db.query(channel_members).filter(
                and_(
                    channel_members.c.channel_id == channel_id,
                    channel_members.c.user_id == user_id
                )
            ).first()
            
            if existing_member:
                return False  # 이미 멤버임
            
            # 새 멤버 추가
            db.execute(
                channel_members.insert().values(
                    channel_id=channel_id,
                    user_id=user_id,
                    role=role,
                    joined_at=datetime.utcnow()
                )
            )
            db.commit()
            return True
        except Exception:
            db.rollback()
            return False
    
    @staticmethod
    def remove_member_from_channel(db: Session, channel_id: int, user_id: int) -> bool:
        """채널에서 멤버 제거"""
        try:
            result = db.execute(
                channel_members.delete().where(
                    and_(
                        channel_members.c.channel_id == channel_id,
                        channel_members.c.user_id == user_id
                    )
                )
            )
            db.commit()
            return result.rowcount > 0
        except Exception:
            db.rollback()
            return False
    
    @staticmethod
    def get_channel_members(db: Session, channel_id: int) -> List[User]:
        """채널의 모든 멤버 조회"""
        return db.query(User).join(channel_members).filter(
            channel_members.c.channel_id == channel_id
        ).all()
    
    @staticmethod
    def is_user_member_of_channel(db: Session, channel_id: int, user_id: int) -> bool:
        """사용자가 채널의 멤버인지 확인"""
        member = db.query(channel_members).filter(
            and_(
                channel_members.c.channel_id == channel_id,
                channel_members.c.user_id == user_id
            )
        ).first()
        return member is not None
    
    @staticmethod
    def update_channel(
        db: Session,
        channel_id: int,
        name: Optional[str] = None,
        description: Optional[str] = None,
        is_public: Optional[bool] = None,
        updated_by: int = None
    ) -> Optional[Channel]:
        """채널 정보 업데이트"""
        channel = db.query(Channel).filter(Channel.id == channel_id).first()
        if not channel:
            return None
        
        if name is not None:
            channel.name = name
        if description is not None:
            channel.description = description
        if is_public is not None:
            channel.is_public = is_public
        if updated_by is not None:
            channel.updated_by = updated_by
        
        channel.updated_at = datetime.utcnow()
        db.commit()
        db.refresh(channel)
        return channel
    
    @staticmethod
    def delete_channel(db: Session, channel_id: int) -> bool:
        """채널 삭제"""
        try:
            channel = db.query(Channel).filter(Channel.id == channel_id).first()
            if channel:
                db.delete(channel)
                db.commit()
                return True
            return False
        except Exception:
            db.rollback()
            return False 