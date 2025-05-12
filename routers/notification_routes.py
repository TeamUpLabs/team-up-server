from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import StreamingResponse
from database import SessionLocal
from crud.notification import update_notification, accept_scout_member, reject_scout_member, delete_notification, delete_all_notifications, get_notifications
from schemas.member import NotificationUpdate
import asyncio
import json
from typing import AsyncGenerator

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
def get_notifications_endpoint(member_id: int, db: SessionLocal = Depends(get_db)):
    try:
        return get_notifications(db, member_id)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.put("/member/{member_id}/notification/{notification_id}")
def update_notification_endpoint(member_id: int, notification_id: int, notification_update: NotificationUpdate, db: SessionLocal = Depends(get_db)):
    try:
        updated_notification = update_notification(db, member_id, notification_id, notification_update)
        return updated_notification
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) 
      
      
@router.post("/member/{member_id}/notification/{notification_id}/scout/accept")
def accept_scout_member_endpoint(member_id: int, notification_id: int, db: SessionLocal = Depends(get_db)):
    try:
        return accept_scout_member(db, member_id, notification_id)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    
    
@router.post("/member/{member_id}/notification/{notification_id}/scout/reject")
def reject_scout_member_endpoint(member_id: int, notification_id: int, db: SessionLocal = Depends(get_db)):
    try:
        return reject_scout_member(db, member_id, notification_id)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
      
  
@router.delete("/member/{member_id}/notification/{notification_id}")
def delete_notification_endpoint(member_id: int, notification_id: int, db: SessionLocal = Depends(get_db)):
    try:
        return delete_notification(db, member_id, notification_id)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
      
@router.delete("/member/{member_id}/notifications")
def delete_all_notifications_endpoint(member_id: int, db: SessionLocal = Depends(get_db)):
    try:
        return delete_all_notifications(db, member_id)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
      
@router.get("/member/{member_id}/notifications/sse")
async def notification_sse(member_id: int, request: Request):
    """
    Server-Sent Events endpoint for real-time notification updates.
    """
    async def event_generator() -> AsyncGenerator[str, None]:
        last_notifications = None
        
        while True:
            if await request.is_disconnected():
                break
                
            # Check for notifications
            db = SessionLocal()
            try:
                current_notifications = get_notifications(db, member_id)
                
                # Send data only if it's the first time or there's a change
                if last_notifications != current_notifications:
                    yield f"data: {json.dumps(current_notifications or [])}\n\n"
                    last_notifications = current_notifications
            finally:
                db.close()
                
            await asyncio.sleep(3)
    
    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        }
    )
      