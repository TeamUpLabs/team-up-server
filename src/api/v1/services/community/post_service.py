from src.api.v1.repositories.community.post_repository import PostRepository
from src.api.v1.schemas.community.post_schema import PostCreate, PostUpdate, PostDetail, CommentCreate
from src.api.v1.models.community.post import Post
from typing import List
from sqlalchemy.orm import Session

class PostService:
  def __init__(self, db: Session):
    self.repository = PostRepository(db)
  
  def create(self, post_in: PostCreate) -> Post:
    return self.repository.create(post_in)
  
  def update(self, post_id: int, post_in: PostUpdate) -> Post:
    return self.repository.update(post_id, post_in)
  
  def delete(self, post_id: int) -> Post:
    return self.repository.delete(post_id)

  def get_by_user(self, user_id: int, skip: int = 0, limit: int = 100) -> List[PostDetail]:
    return self.repository.get_by_user(user_id, skip, limit)
  
  def get_by_id(self, post_id: int) -> PostDetail:
    return self.repository.get_by_id(post_id)

  def get_all(self, skip: int = 0, limit: int = 100) -> List[PostDetail]:
    return self.repository.get_all(skip, limit)
  
  def get_bookmarked_posts(self, user_id: int, skip: int = 0, limit: int = 100) -> List[PostDetail]:
    return self.repository.get_bookmarked_posts(user_id, skip, limit)

  def like(self, post_id: int, user_id: int) -> PostDetail:
    return self.repository.like(post_id, user_id)

  def delete_like(self, post_id: int, user_id: int) -> PostDetail:
    return self.repository.delete_like(post_id, user_id)

  def dislike(self, post_id: int, user_id: int) -> PostDetail:
    return self.repository.dislike(post_id, user_id)

  def delete_dislike(self, post_id: int, user_id: int) -> PostDetail:
    return self.repository.delete_dislike(post_id, user_id)

  def view(self, post_id: int, user_id: int) -> PostDetail:
    return self.repository.view(post_id, user_id)

  def share(self, post_id: int, user_id: int) -> PostDetail:
    return self.repository.share(post_id, user_id)

  def create_comment(self, post_id: int, user_id: int, comment_in: CommentCreate) -> PostDetail:
    return self.repository.create_comment(post_id, user_id, comment_in)

  def delete_comment(self, post_id: int, user_id: int, comment_id: int) -> PostDetail:
    return self.repository.delete_comment(post_id, user_id, comment_id)
  
  def bookmark(self, post_id: int, user_id: int) -> PostDetail:
    return self.repository.bookmark(post_id, user_id)
  
  def delete_bookmark(self, post_id: int, user_id: int) -> PostDetail:
    return self.repository.delete_bookmark(post_id, user_id)
    