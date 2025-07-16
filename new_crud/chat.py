from sqlalchemy.orm import Session
from sqlalchemy import and_, desc
from typing import List, Optional
from new_models.chat import Chat
from new_models.channel import Channel
from new_models.user import User
from datetime import datetime

class ChatCRUD:
    """채팅 관련 CRUD 작업"""
    
    @staticmethod
    def create_chat(
        db: Session,
        project_id: str,
        channel_id: str,
        user_id: int,
        message: str
    ) -> Chat:
        """새로운 채팅 메시지 생성"""
        chat = Chat(
            project_id=project_id,
            channel_id=channel_id,
            user_id=user_id,
            message=message,
            timestamp=datetime.utcnow()
        )
        db.add(chat)
        db.commit()
        db.refresh(chat)
        return chat
    
    @staticmethod
    def get_chat_by_id(db: Session, chat_id: int) -> Optional[Chat]:
        """ID로 채팅 메시지 조회"""
        return db.query(Chat).filter(Chat.id == chat_id).first()
    
    @staticmethod
    def get_channel_chats(
        db: Session,
        channel_id: str,
        limit: int = 50,
        offset: int = 0
    ) -> List[Chat]:
        """채널의 채팅 메시지 조회 (최신순)"""
        return db.query(Chat).filter(
            Chat.channel_id == channel_id
        ).order_by(desc(Chat.timestamp)).offset(offset).limit(limit).all()
    
    @staticmethod
    def get_project_chats(
        db: Session,
        project_id: str,
        limit: int = 50,
        offset: int = 0
    ) -> List[Chat]:
        """프로젝트의 모든 채팅 메시지 조회 (최신순)"""
        return db.query(Chat).filter(
            Chat.project_id == project_id
        ).order_by(desc(Chat.timestamp)).offset(offset).limit(limit).all()
    
    @staticmethod
    def get_user_chats(
        db: Session,
        user_id: int,
        limit: int = 50,
        offset: int = 0
    ) -> List[Chat]:
        """사용자가 작성한 채팅 메시지 조회 (최신순)"""
        return db.query(Chat).filter(
            Chat.user_id == user_id
        ).order_by(desc(Chat.timestamp)).offset(offset).limit(limit).all()
    
    @staticmethod
    def get_chats_by_date_range(
        db: Session,
        channel_id: str,
        start_date: datetime,
        end_date: datetime,
        limit: int = 100
    ) -> List[Chat]:
        """특정 기간의 채팅 메시지 조회"""
        return db.query(Chat).filter(
            and_(
                Chat.channel_id == channel_id,
                Chat.timestamp >= start_date,
                Chat.timestamp <= end_date
            )
        ).order_by(desc(Chat.timestamp)).limit(limit).all()
    
    @staticmethod
    def search_chats(
        db: Session,
        channel_id: str,
        search_term: str,
        limit: int = 50
    ) -> List[Chat]:
        """채널에서 메시지 내용으로 검색"""
        return db.query(Chat).filter(
            and_(
                Chat.channel_id == channel_id,
                Chat.message.contains(search_term)
            )
        ).order_by(desc(Chat.timestamp)).limit(limit).all()
    
    @staticmethod
    def update_chat(
        db: Session,
        chat_id: int,
        message: str
    ) -> Optional[Chat]:
        """채팅 메시지 수정"""
        chat = db.query(Chat).filter(Chat.id == chat_id).first()
        if not chat:
            return None
        
        chat.message = message
        db.commit()
        db.refresh(chat)
        return chat
    
    @staticmethod
    def delete_chat(db: Session, chat_id: int) -> bool:
        """채팅 메시지 삭제"""
        try:
            chat = db.query(Chat).filter(Chat.id == chat_id).first()
            if chat:
                db.delete(chat)
                db.commit()
                return True
            return False
        except Exception:
            db.rollback()
            return False
    
    @staticmethod
    def get_chat_with_user_info(db: Session, chat_id: int) -> Optional[dict]:
        """채팅 메시지와 사용자 정보를 함께 조회"""
        chat = db.query(Chat).join(User).filter(Chat.id == chat_id).first()
        if not chat:
            return None
        
        return {
            "id": chat.id,
            "message": chat.message,
            "timestamp": chat.timestamp,
            "user_id": chat.user_id,
            "user": {
                "id": chat.user.id,
                "name": chat.user.name,
                "profile_image": chat.user.profile_image,
                "email": chat.user.email
            },
            "channel_id": chat.channel_id,
            "project_id": chat.project_id
        }
    
    @staticmethod
    def get_channel_chats_with_user_info(
        db: Session,
        channel_id: str,
        limit: int = 50,
        offset: int = 0
    ) -> List[dict]:
        """채널의 채팅 메시지와 사용자 정보를 함께 조회"""
        chats = db.query(Chat).join(User).filter(
            Chat.channel_id == channel_id
        ).order_by(desc(Chat.timestamp)).offset(offset).limit(limit).all()
        
        return [
            {
                "id": chat.id,
                "message": chat.message,
                "timestamp": chat.timestamp,
                "user_id": chat.user_id,
                "user": {
                    "id": chat.user.id,
                    "name": chat.user.name,
                    "profile_image": chat.user.profile_image,
                    "email": chat.user.email
                },
                "channel_id": chat.channel_id,
                "project_id": chat.project_id
            }
            for chat in chats
        ] 