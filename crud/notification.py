from sqlalchemy.orm import Session
from models.member import Member as MemberModel
from schemas.member import NotificationUpdate

def update_notification(db: Session, member_id: int, notification_id: int, notification_update: NotificationUpdate):
  member = db.query(MemberModel).filter(MemberModel.id == member_id).first()
  if not member:
    return None
  
  notifications = member.notification
  for i, notification in enumerate(notifications):
    if notification['id'] == notification_id:
      for field, value in notification_update.dict(exclude_unset=True, exclude_none=True).items():
        notification[field] = value
        
  db.query(MemberModel).filter(MemberModel.id == member_id).update(
    {"notification": notifications},
    synchronize_session="fetch"
  )
  
  db.commit()
  db.refresh(member)
  return member
      