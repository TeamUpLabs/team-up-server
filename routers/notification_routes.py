from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import StreamingResponse
from database import SessionLocal
from crud.notification import update_notification, accept_scout_member, reject_scout_member, delete_notification, delete_all_notifications, get_notifications
from schemas.member import NotificationUpdate
import asyncio
import json
from typing import AsyncGenerator
import logging

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
def update_notification_endpoint(member_id: int, notification_id: int, notification_update: NotificationUpdate, db: SessionLocal = Depends(get_db)):  # type: ignore
    try:
        updated_notification = update_notification(db, member_id, notification_id, notification_update)
        return updated_notification
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) 
      
      
@router.post("/member/{member_id}/notification/{notification_id}/scout/accept")
def accept_scout_member_endpoint(member_id: int, notification_id: int, db: SessionLocal = Depends(get_db)):  # type: ignore
    try:
        return accept_scout_member(db, member_id, notification_id)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    
    
@router.post("/member/{member_id}/notification/{notification_id}/scout/reject")
def reject_scout_member_endpoint(member_id: int, notification_id: int, db: SessionLocal = Depends(get_db)):  # type: ignore
    try:
        return reject_scout_member(db, member_id, notification_id)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
      
  
@router.delete("/member/{member_id}/notification/{notification_id}")
def delete_notification_endpoint(member_id: int, notification_id: int, db: SessionLocal = Depends(get_db)):  # type: ignore
    try:
        return delete_notification(db, member_id, notification_id)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    
@router.delete("/member/{member_id}/notifications")
def delete_all_notifications_endpoint(member_id: int, db: SessionLocal = Depends(get_db)):  # type: ignore
    try:
        return delete_all_notifications(db, member_id)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    
@router.get("/member/{member_id}/notifications/sse")
async def notification_sse(member_id: int, request: Request):  # type: ignore   
    """
    Server-Sent Events endpoint for real-time notification updates.
    """
    def convert_to_dict(obj):
        if hasattr(obj, '__dict__'):
            return {
                key: convert_to_dict(value)
                for key, value in obj.__dict__.items()
                if not key.startswith('_')
            }
        elif isinstance(obj, (list, tuple)):
            return [convert_to_dict(item) for item in obj]
        elif isinstance(obj, dict):
            return {key: convert_to_dict(value) for key, value in obj.items()}
        else:
            return obj

    async def event_generator() -> AsyncGenerator[str, None]:
        db = None
        try:
            db = SessionLocal()
            last_notifications = None
            while True:
                if await request.is_disconnected():
                    logging.info(f"Client disconnected from member {member_id} notifications SSE")
                    break

                try:
                    current_notifications = get_notifications(db, member_id)
                    notifications_dict = convert_to_dict(current_notifications or [])
                    
                    if last_notifications != notifications_dict:
                        yield f"data: {json.dumps(notifications_dict)}\n\n"
                        last_notifications = notifications_dict
                except Exception as e:
                    logging.error(f"Error in SSE for member {member_id} notifications: {str(e)}")
                    error_message = {
                        'error': str(e),
                        'status': 'error'
                    }
                    yield f"data: {json.dumps(error_message)}\n\n"
                    # Don't break the connection on error, just log it and continue
                    await asyncio.sleep(3)
                    continue

                await asyncio.sleep(3)
        except Exception as e:
            logging.error(f"Critical error in SSE for member {member_id}: {str(e)}")
            yield f"data: {json.dumps({'error': str(e), 'status': 'error'})}\n\n"
        finally:
            if db:
                db.close()
            logging.info(f"SSE connection closed for member {member_id} notifications")

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