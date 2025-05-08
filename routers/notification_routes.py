from fastapi import APIRouter, Depends, HTTPException
from database import SessionLocal
from crud.notification import update_notification, accept_scout_member, reject_scout_member
from schemas.member import NotificationUpdate

router = APIRouter(
    tags=["notification"]
)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

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
    
    
@router.put("/member/{member_id}/notification/{notification_id}/scout/reject")
def reject_scout_member_endpoint(member_id: int, notification_id: int, db: SessionLocal = Depends(get_db)):
    try:
        return reject_scout_member(db, member_id, notification_id)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))