from fastapi import APIRouter, Depends, HTTPException, status, Query
from typing import List, Optional
from sqlalchemy.orm import Session

from database import get_db
from auth import get_current_user
from new_crud import notification
from new_schemas.notification import (
    NotificationCreate, NotificationUpdate, NotificationResponse, 
    NotificationListResponse
)
from new_models.user import User

router = APIRouter(
    prefix="/api/notifications",
    tags=["notifications"]
)

@router.get("/", response_model=NotificationListResponse)
def get_user_notifications(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    is_read: Optional[bool] = Query(None),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """사용자의 알림 목록 조회"""
    notifications = notification.get_user_notifications(
        db=db, 
        user_id=current_user.id, 
        skip=skip, 
        limit=limit,
        is_read=is_read
    )
    
    unread_count = notification.get_unread_count(db=db, user_id=current_user.id)
    total_count = len(notifications)  # 실제로는 전체 개수를 별도로 조회해야 함
    
    return NotificationListResponse(
        notifications=[NotificationResponse.model_validate(n, from_attributes=True) for n in notifications],
        total_count=total_count,
        unread_count=unread_count
    )

@router.get("/unread-count")
def get_unread_count(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """읽지 않은 알림 개수 조회"""
    count = notification.get_unread_count(db=db, user_id=current_user.id)
    return {"unread_count": count}

@router.get("/{notification_id}", response_model=NotificationResponse)
def get_notification(
    notification_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """특정 알림 조회"""
    notification_obj = notification.get(db=db, id=notification_id)
    if not notification_obj:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="알림을 찾을 수 없습니다."
        )
    
    # 본인의 알림만 조회 가능
    if notification_obj.receiver_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="접근 권한이 없습니다."
        )
    
    return NotificationResponse.model_validate(notification_obj, from_attributes=True)

@router.put("/{notification_id}/read", response_model=NotificationResponse)
def mark_notification_as_read(
    notification_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """알림을 읽음으로 표시"""
    notification_obj = notification.mark_as_read(
        db=db, 
        notification_id=notification_id, 
        user_id=current_user.id
    )
    return NotificationResponse.model_validate(notification_obj, from_attributes=True)

@router.put("/mark-all-read")
def mark_all_notifications_as_read(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """모든 알림을 읽음으로 표시"""
    return notification.mark_all_as_read(db=db, user_id=current_user.id)

@router.delete("/{notification_id}")
def delete_notification(
    notification_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """알림 삭제"""
    return notification.delete_notification(
        db=db, 
        notification_id=notification_id, 
        user_id=current_user.id
    )

@router.post("/", response_model=NotificationResponse, status_code=status.HTTP_201_CREATED)
def create_notification(
    notification_in: NotificationCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """새 알림 생성 (관리자 또는 시스템용)"""
    # 실제로는 권한 체크가 필요할 수 있음
    # 현재는 간단히 sender_id를 현재 사용자로 설정
    notification_in.sender_id = current_user.id
    
    notification_obj = notification.create_notification(db=db, obj_in=notification_in)
    return NotificationResponse.model_validate(notification_obj, from_attributes=True) 