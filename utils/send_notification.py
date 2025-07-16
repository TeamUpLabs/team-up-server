from datetime import datetime
from schemas.notification import NotificationCreate
from crud import user
from utils.sse_manager import notification_sse_manager
import json
from sqlalchemy.orm import Session
from models.user import User as UserModel
import logging

async def send_notification(
    db: Session,
    id: int,
    title: str,
    message: str,
    type: str,
    is_read: bool,
    sender_id: int,
    receiver_id: int,
    project_id: str,
):
    notification_pydantic_model = NotificationCreate(
        id=id,
        title=title,
        message=message,
        type=type,
        is_read=is_read,
        sender_id=sender_id,
        receiver_id=receiver_id,
        project_id=project_id,
    )
    
    receiver = user.get(db, id=receiver_id)
    
    receiver_model_instance = db.query(UserModel).filter(UserModel.id == receiver_id).first()
    if not receiver_model_instance:
        logging.error(f"Receiver with ID {receiver_id} not found in database for notification.")
        return [] # Or raise an error, depending on desired behavior

    processed_notifications_list = []
    if hasattr(receiver_model_instance, 'notification') and receiver_model_instance.notification is not None:
        for item in receiver_model_instance.notification:
            if hasattr(item, 'model_dump'):
                processed_notifications_list.append(item.model_dump())
            elif isinstance(item, dict):
                processed_notifications_list.append(item)
            else:
                logging.warning(f"Unexpected notification item type: {type(item)}. Item: {item}")
                # Decide how to handle unexpected types. For now, append as is or a representation.
                processed_notifications_list.append(str(item) if not isinstance(item, (dict, list)) else item)

    processed_notifications_list.append(notification_pydantic_model.model_dump())
    
    receiver_model_instance.notification = processed_notifications_list

    await notification_sse_manager.send_event(
        receiver_id,
        json.dumps(notification_sse_manager.convert_to_dict(receiver_model_instance.notification))
    )
    
    db.query(UserModel).filter(UserModel.id == receiver_id).update(
        {'notification': receiver_model_instance.notification}, 
        synchronize_session="fetch"
    )
    db.commit()
    db.refresh(receiver_model_instance)
    return receiver_model_instance.notification