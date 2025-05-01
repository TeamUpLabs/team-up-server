from sqlalchemy.orm import Session
from models.chat import ChatMessage
from schemas.chat import ChatCreate


def save_chat_message(db: Session, chat: ChatCreate):
  db_chat = ChatMessage(**chat.dict())
  db.add(db_chat)
  db.commit()
  db.refresh(db_chat)
  return db_chat


def get_chat_history(db: Session, projectId: str, channelId: str, limit: int = 50):
  try:
    return db.query(ChatMessage).filter(
        ChatMessage.projectId == projectId,
        ChatMessage.channelId == channelId
    ).order_by(ChatMessage.timestamp.desc()).limit(limit).all()
  except Exception as e:
    print(e)
    return []
    
