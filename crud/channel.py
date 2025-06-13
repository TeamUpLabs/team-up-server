from schemas.channel import ChannelCreate, ChannelUpdate
from models.channel import Channel
from sqlalchemy.orm import Session
from crud.member import get_member_by_id

def create_channel(db: Session, channel: ChannelCreate):
  db_channel = Channel(**channel.model_dump())
  db.add(db_channel)
  db.commit()
  db.refresh(db_channel)
  return db_channel

def get_channel_by_project_id(db: Session, projectId: str):
  channels = db.query(Channel).filter(Channel.projectId == projectId).all()
  result = []
    
  for channel in channels:
    members = []
    if channel.member_id:
      for member_id in channel.member_id:
        members.append(get_member_by_id(db, member_id))
    channel.members = members
    result.append(channel)
  if not channels:
    return []
  return result

def get_channel_by_channel_id(db: Session, projectId: str, channelId: str):
  try:
    return db.query(Channel).filter(Channel.projectId == projectId, Channel.channelId == channelId).first()
  except Exception as e:
    logging.error(e)
    return None
  
def update_channel(db: Session, projectId: str, channelId: str, channel_update: ChannelUpdate):
  channel = db.query(Channel).filter(Channel.projectId == projectId, Channel.channelId == channelId).first()
  if not channel:
    return None
  
  channel_data = channel_update.model_dump(exclude_unset=True, exclude_none=True)
  for field, value in channel_data.items():
    setattr(channel, field, value) 
  
  db.commit()
  db.refresh(channel)
  return channel

def delete_channel_by_id(db: Session, projectId: str, channelId: str):
  channel = db.query(Channel).filter(Channel.projectId == projectId, Channel.channelId == channelId).first()
  if not channel:
    return None
  db.delete(channel)
  db.commit()
  return True