from sqlalchemy.orm import Session
from models.member import Member as MemberModel
from models.project import Project as ProjectModel
from schemas.member import NotificationUpdate, NotificationInfo
from crud.project import add_member_to_project
from datetime import datetime

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

def accept_scout_member(db: Session, member_id: int, notification_id: int):
  member = db.query(MemberModel).filter(MemberModel.id == member_id).first()
  if not member:
    return None
  
  target_notification = None
  for notification in member.notification:
    if notification['id'] == notification_id:
      target_notification = notification
      break
  
  if not target_notification:
    return None
  
  target_project = db.query(ProjectModel).filter(ProjectModel.id == target_notification['project_id']).first()
  if not target_project:
    return None
  
  sender_member = db.query(MemberModel).filter(MemberModel.id == target_notification['sender_id']).first()
  if not sender_member:
    return None
  
  receiver_member = db.query(MemberModel).filter(MemberModel.id == target_notification["receiver_id"]).first()
  if not receiver_member:
    return None
  
  add_member_to_project(db, target_notification['project_id'], member_id)
  
  sender_notification = NotificationInfo(
    id=int(datetime.now().timestamp()),
    title="스카우트 요청 수락",
    message=f'"{receiver_member.name}" 님이 "{target_project.title}" 프로젝트에 참여 요청을 수락했습니다.',
    type="info",
    timestamp=datetime.now().isoformat().split('T')[0],
    isRead=False,
    sender_id=receiver_member.id,
    receiver_id=sender_member.id,
    project_id=target_notification['project_id'],
    result="accept"
  )
  
  if not hasattr(sender_member, 'notification') or sender_member.notification is None:
    sender_member.notification = []
    
  sender_member.notification.append(sender_notification.model_dump())
  
  db.query(MemberModel).filter(MemberModel.id == sender_member.id).update(
    {"notification": sender_member.notification},
    synchronize_session="fetch"
  )
  
  update_notification(db, receiver_member.id, notification_id, NotificationUpdate(result="accept"))
  
  db.commit()
  db.refresh(sender_member)
  return {"message": "스카우트 요청 수락 완료"}
  
def reject_scout_member(db: Session, member_id: int, notification_id: int):
  member = db.query(MemberModel).filter(MemberModel.id == member_id).first()
  if not member:
    return None
  
  target_notification = None
  for notification in member.notification:
    if notification['id'] == notification_id:
      target_notification = notification
      break
  
  if not target_notification:
    return None
  
  target_project = db.query(ProjectModel).filter(ProjectModel.id == target_notification['project_id']).first()
  if not target_project:
    return None
  
  sender_member = db.query(MemberModel).filter(MemberModel.id == target_notification['sender_id']).first()
  if not sender_member:
    return None
  
  receiver_member = db.query(MemberModel).filter(MemberModel.id == member_id).first()
  if not receiver_member:
    return None
  
  reject_notification = NotificationInfo(
    id=int(datetime.now().timestamp()),
    title="스카우트 요청 거절",
    message=f'"{receiver_member.name}" 님이 "{target_project.title}" 프로젝트에 참여 요청을 거절했습니다.',
    type="info",
    timestamp=datetime.now().isoformat().split('T')[0],
    isRead=False,
    sender_id=receiver_member.id,
    receiver_id=sender_member.id,
    project_id=target_notification['project_id'],
    result="reject"
  )
  
  if not hasattr(sender_member, 'notification') or sender_member.notification is None:
    sender_member.notification = []
    
  sender_member.notification.append(reject_notification.model_dump())
  
  db.query(MemberModel).filter(MemberModel.id == sender_member.id).update(
    {"notification": sender_member.notification},
    synchronize_session="fetch"
  )
  
  update_notification(db, sender_member.id, notification_id, NotificationUpdate(result="reject"))
  
  db.commit()
  db.refresh(sender_member)
  return {"message": "스카우트 요청 거절 완료"}

def delete_notification(db: Session, member_id: int, notification_id: int):
  member = db.query(MemberModel).filter(MemberModel.id == member_id).first()
  if not member:
    return None
  
  member.notification = [notification for notification in member.notification if notification['id'] != notification_id]
  
  db.query(MemberModel).filter(MemberModel.id == member_id).update(
    {"notification": member.notification},
    synchronize_session="fetch"
  )
  
  db.commit()
  db.refresh(member)
  return {"message": "알림 삭제 완료"}

def delete_all_notifications(db: Session, member_id: int):
  member = db.query(MemberModel).filter(MemberModel.id == member_id).first()
  if not member:
    return None
  
  member.notification = []
  
  db.query(MemberModel).filter(MemberModel.id == member_id).update(
    {"notification": member.notification},
    synchronize_session="fetch"
  )
  
  db.commit()
  db.refresh(member)
  return {"message": "모든 알림 삭제 완료"}

def get_notifications(db: Session, member_id: int):
  member = db.query(MemberModel).filter(MemberModel.id == member_id).first()
  if not member:
    return None
  
  return member.notification