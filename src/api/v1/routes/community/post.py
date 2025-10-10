from fastapi import APIRouter, Depends, HTTPException, status
from src.api.v1.services.community.post_service import PostService
from src.api.v1.schemas.community.post_schema import PostCreate, PostUpdate, CommentCreate, PostDetail
from src.core.security.auth import get_current_user
from sqlalchemy.orm import Session
from src.core.database.database import get_db

router = APIRouter(prefix="/api/v1/community/posts", tags=["community_posts"])

@router.post("/")
def create_post(
    post_in: PostCreate,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
  if not current_user:
    raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Unauthorized")
  
  try:
    post_service = PostService(db)
    return post_service.create(post_in)
  except HTTPException as e:
    raise e
  except Exception as e:
    raise HTTPException(status_code=400, detail=str(e))
  
@router.get("/")
def get_posts(
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
  if not current_user:
    raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Unauthorized")
  
  try:
    post_service = PostService(db)
    return post_service.get_by_user(current_user.id)
  except HTTPException as e:
    raise e
  except Exception as e:
    raise HTTPException(status_code=400, detail=str(e))
  
@router.get("/all")
def get_all_posts(
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
  if not current_user:
    raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Unauthorized")
  
  try:
    post_service = PostService(db)
    return post_service.get_all()
  except HTTPException as e:
    raise e
  except Exception as e:
    raise HTTPException(status_code=400, detail=str(e))
  
@router.get("/bookmarks")
def get_bookmarked_posts(
  current_user: dict = Depends(get_current_user),
  db: Session = Depends(get_db)
):
  if not current_user:
    raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Unauthorized")
  
  try:
    post_service = PostService(db)
    return post_service.get_bookmarked_posts(current_user.id)
  except HTTPException as e:
    raise e
  except Exception as e:
    raise HTTPException(status_code=400, detail=str(e))

@router.get("/{post_id}")
def get_post(
    post_id: int,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
  if not current_user:
    raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Unauthorized")
  
  try:
    post_service = PostService(db)
    return post_service.get_by_id(post_id)
  except HTTPException as e:
    raise e
  except Exception as e:
    raise HTTPException(status_code=400, detail=str(e))

@router.put("/{post_id}")
def update_post(
    post_id: int,
    post_in: PostUpdate,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
  if not current_user:
    raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Unauthorized")
  
  try:
    post_service = PostService(db)
    return post_service.update(post_id, post_in)
  except HTTPException as e:
    raise e
  except Exception as e:
    raise HTTPException(status_code=400, detail=str(e))

@router.delete("/{post_id}")
def delete_post(
    post_id: int,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
  if not current_user:
    raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Unauthorized")
  
  try:
    post_service = PostService(db)
    return post_service.delete(post_id)
  except HTTPException as e:
    raise e
  except Exception as e:
    raise HTTPException(status_code=400, detail=str(e))

@router.post("/{post_id}/likes")
def like_post(
    post_id: int,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
  if not current_user:
    raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Unauthorized")
  
  try:
    post_service = PostService(db)
    return post_service.like(post_id, current_user.id)
  except HTTPException as e:
    raise e
  except Exception as e:
    raise HTTPException(status_code=400, detail=str(e))

@router.delete("/{post_id}/likes")
def delete_like_post(
    post_id: int,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
  if not current_user:
    raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Unauthorized")
  
  try:
    post_service = PostService(db)
    return post_service.delete_like(post_id, current_user.id)
  except HTTPException as e:
    raise e
  except Exception as e:
    raise HTTPException(status_code=400, detail=str(e))

@router.post("/{post_id}/dislikes")
def dislike_post(
    post_id: int,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
  if not current_user:
    raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Unauthorized")
  
  try:
    post_service = PostService(db)
    return post_service.dislike(post_id, current_user.id)
  except HTTPException as e:
    raise e
  except Exception as e:
    raise HTTPException(status_code=400, detail=str(e))

@router.delete("/{post_id}/dislikes")
def delete_dislike_post(
    post_id: int,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
  if not current_user:
    raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Unauthorized")
  
  try:
    post_service = PostService(db)
    return post_service.delete_dislike(post_id, current_user.id)
  except HTTPException as e:
    raise e
  except Exception as e:
    raise HTTPException(status_code=400, detail=str(e))

@router.post("/{post_id}/views")
def view_post(
    post_id: int,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
  if not current_user:
    raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Unauthorized")
  
  try:
    post_service = PostService(db)
    return post_service.view(post_id, current_user.id)
  except HTTPException as e:
    raise e
  except Exception as e:
    raise HTTPException(status_code=400, detail=str(e))

@router.post("/{post_id}/comments")
def create_comment_post(
    post_id: int,
    comment_in: CommentCreate,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
  if not current_user:
    raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Unauthorized")
  
  try:
    post_service = PostService(db)
    return post_service.create_comment(post_id, current_user.id, comment_in)
  except HTTPException as e:
    raise e
  except Exception as e:
    raise HTTPException(status_code=400, detail=str(e))

@router.delete("/{post_id}/comments/{comment_id}")
def delete_comment_post(
    post_id: int,
    comment_id: int,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
  if not current_user:
    raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Unauthorized")
  
  try:
    post_service = PostService(db)
    return post_service.delete_comment(post_id, current_user.id, comment_id)
  except HTTPException as e:
    raise e
  except Exception as e:
    raise HTTPException(status_code=400, detail=str(e))

@router.post("/{post_id}/bookmarks", response_model=PostDetail)
def bookmark_post(
  post_id: int,
  current_user: dict = Depends(get_current_user),
  db: Session = Depends(get_db)
):
  if not current_user:
    raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Unauthorized")
  
  try:
    post_service = PostService(db)
    return post_service.bookmark(post_id, current_user.id)
  except HTTPException as e:
    raise e
  except Exception as e:
    raise HTTPException(status_code=400, detail=str(e))

@router.delete("/{post_id}/bookmarks", response_model=PostDetail)
def delete_bookmark_post(
  post_id: int,
  current_user: dict = Depends(get_current_user),
  db: Session = Depends(get_db)
):
  if not current_user:
    raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Unauthorized")
  
  try:
    post_service = PostService(db)
    return post_service.delete_bookmark(post_id, current_user.id)
  except HTTPException as e:
    raise e
  except Exception as e:
    raise HTTPException(status_code=400, detail=str(e))

