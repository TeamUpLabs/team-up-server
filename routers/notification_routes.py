from fastapi import APIRouter, Depends, HTTPException
from database import SessionLocal
from crud.notification import update_notification
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