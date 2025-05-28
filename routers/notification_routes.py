from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import StreamingResponse
from database import SessionLocal
from crud.notification import update_notification, accept_scout_member, reject_scout_member, delete_notification, delete_all_notifications, get_notifications
from schemas.member import NotificationUpdate
import asyncio
import json
from typing import AsyncGenerator
import logging
from utils.sse_manager import notification_sse_manager

router = APIRouter(
    tags=["notification"]
)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
      
        
@router.get("/member/{member_id}/notifications")
def get_notifications_endpoint(member_id: int, db: SessionLocal = Depends(get_db)):  # type: ignore
    try:
        return get_notifications(db, member_id)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.put("/member/{member_id}/notification/{notification_id}")
async def update_notification_endpoint(member_id: int, notification_id: int, notification_update: NotificationUpdate, db: SessionLocal = Depends(get_db)):  # type: ignore
    try:
        updated_notification = await update_notification(db, member_id, notification_id, notification_update)
        if updated_notification:
            await notification_sse_manager.send_event(
                member_id,
                json.dumps(notification_sse_manager.convert_to_dict(update_notification))
            )
            logging.info(f"[SSE] Member {member_id} updated from Notification update.")
        else:
            raise HTTPException(status_code=404, detail="Notification not found")
        return updated_notification
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) 
      
      
@router.post("/member/{member_id}/notification/{notification_id}/scout/accept")
async def accept_scout_member_endpoint(member_id: int, notification_id: int, db: SessionLocal = Depends(get_db)):  # type: ignore
    try:
        result = accept_scout_member(db, member_id, notification_id)
        if result:
            notification_data = get_notifications(db, member_id)
            await notification_sse_manager.send_event(
                member_id,
                json.dumps(notification_sse_manager.convert_to_dict(notification_data))
            )
            logging.info(f"[SSE] Member {member_id} updated from Notification accept.")
        else:
            raise HTTPException(status_code=404, detail="Notification not found")
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    
    
@router.post("/member/{member_id}/notification/{notification_id}/scout/reject")
async def reject_scout_member_endpoint(member_id: int, notification_id: int, db: SessionLocal = Depends(get_db)):  # type: ignore
    try:
        result = reject_scout_member(db, member_id, notification_id)
        if result:
            notification_data = get_notifications(db, member_id)
            await notification_sse_manager.send_event(
                member_id,
                json.dumps(notification_sse_manager.convert_to_dict(notification_data))
            )
            logging.info(f"[SSE] Member {member_id} updated from Notification reject.")
        else:
            raise HTTPException(status_code=404, detail="Notification not found")
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
      
  
@router.delete("/member/{member_id}/notification/{notification_id}")
async def delete_notification_endpoint(member_id: int, notification_id: int, db: SessionLocal = Depends(get_db)):  # type: ignore
    try:
        result = delete_notification(db, member_id, notification_id)
        if result:
            notification_data = get_notifications(db, member_id)
            await notification_sse_manager.send_event(
                member_id,
                json.dumps(notification_sse_manager.convert_to_dict(notification_data))
            )
            logging.info(f"[SSE] Member {member_id} updated from Notification delete.")
        else:
            raise HTTPException(status_code=404, detail="Notification not found")
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    
@router.delete("/member/{member_id}/notifications")
async def delete_all_notifications_endpoint(member_id: int, db: SessionLocal = Depends(get_db)):  # type: ignore
    try:
        result = delete_all_notifications(db, member_id)
        if result:
            notification_data = get_notifications(db, member_id)
            await notification_sse_manager.send_event(
                member_id,
                json.dumps(notification_sse_manager.convert_to_dict(notification_data))
            )
            logging.info(f"[SSE] Member {member_id} updated from Notification delete all.")
        else:
            raise HTTPException(status_code=404, detail="Notification not found")
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    
@router.get("/member/{member_id}/notifications/sse")
async def notification_sse(member_id: int, request: Request):  # type: ignore   
    queue = await notification_sse_manager.connect(member_id)
    
    async def event_generator():
        db = SessionLocal()
        try:
            notifications = get_notifications(db, member_id)
            notifications_dict = notification_sse_manager.convert_to_dict(notifications)
            yield f"data: {json.dumps(notifications_dict)}\n\n"
        finally:
            db.close()
            
        async for event in notification_sse_manager.event_generator(member_id, queue):
            if await request.is_disconnected():
                await notification_sse_manager.disconnect(member_id, queue)
                break
            yield event
        

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
            "Access-Control-Allow-Origin": "*"  # Add CORS header
        }
    )