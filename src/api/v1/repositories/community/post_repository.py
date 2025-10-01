from sqlalchemy.orm import Session, joinedload
from api.v1.schemas.community.post_schema import PostCreate, PostUpdate, PostDetail, CommentCreate
from api.v1.models.community.post import Post, PostReaction, PostComment
from api.v1.models.user import User
from api.v1.schemas.brief import UserBrief
from collections import defaultdict
from typing import Dict, Any, List
from fastapi import HTTPException
from api.v1.models.association_tables import user_post_bookmarks

class PostRepository:
  def __init__(self, db: Session):
    self.db = db
    
  def create(self, post_in: PostCreate) -> Post:
    post = Post(**post_in.model_dump())
    self.db.add(post)
    self.db.commit()
    self.db.refresh(post)
    return post
  
  def update(self, post_id: int, post_in: PostUpdate) -> Post:
    post = self.db.query(Post).filter(Post.id == post_id).first()
    if not post:
      raise HTTPException(status_code=404, detail="Post not found")
    update_data = post_in.model_dump(exclude_unset=True)
    for key, value in update_data.items():
      setattr(post, key, value)
    self.db.add(post)
    self.db.commit()
    self.db.refresh(post)
    return post
  
  def delete(self, post_id: int) -> Post:
    post = self.db.query(Post).filter(Post.id == post_id).first()
    if not post:
      raise HTTPException(status_code=404, detail="Post not found")
    self.db.delete(post)
    self.db.commit()
    return post
      
  def _get_reactions_for_post(self, post_id: int) -> Dict[str, Dict[str, Any]]:
    reactions = self.db.query(PostReaction).options(
      joinedload(PostReaction.user)
    ).filter(PostReaction.post_id == post_id).all()
    reaction_groups = defaultdict(list)
    for reaction in reactions:
      if reaction.user:
        user_brief = UserBrief.model_validate(reaction.user, from_attributes=True)
        reaction_groups[reaction.reaction_type].append(user_brief)
    comments = self.db.query(PostComment).options(
      joinedload(PostComment.user)
    ).filter(PostComment.post_id == post_id).all()
    reaction_data = {}
    for reaction_type in ['like', 'dislike', 'view', 'share']:
      users = reaction_groups.get(reaction_type, [])
      reaction_data[reaction_type] = {
        'count': len(users),
        'users': users
      }
    reaction_data['comment'] = {
      'count': len(comments),
      'comments': comments
    }
    return reaction_data
  
  def get_by_user(self, user_id: int, skip: int = 0, limit: int = 100) -> List[PostDetail]:
    posts = self.db.query(Post).options(
      joinedload(Post.creator)
    ).filter(Post.user_id == user_id).offset(skip).limit(limit).all()
    
    result = []
    for post in posts:
      reaction_data = self._get_reactions_for_post(post.id)
      post_dict = {
        **post.__dict__,
        'reaction': {
          'likes': reaction_data['like'],
          'dislikes': reaction_data['dislike'],
          'views': reaction_data['view'],
          'shares': reaction_data.get('share', {'count': 0, 'users': []}),
          'comments': reaction_data.get('comment', {}).get('comments', [])
        }
      }
      post_detail = PostDetail.model_validate(post_dict, from_attributes=True)
      result.append(post_detail)
    
    return result
  
  def get_by_id(self, post_id: int) -> PostDetail:
    post = self.db.query(Post).filter(Post.id == post_id).first()
    if not post:
      raise HTTPException(status_code=404, detail="Post not found")
    reaction_data = self._get_reactions_for_post(post.id)
    post_dict = {
      **post.__dict__,
      'reaction': {
        'likes': reaction_data['like'],
        'dislikes': reaction_data['dislike'],
        'views': reaction_data['view'],
        'shares': reaction_data.get('share', {'count': 0, 'users': []}),
        'comments': reaction_data.get('comment', {}).get('comments', [])
      }
    }
    post_detail = PostDetail.model_validate(post_dict, from_attributes=True)
    return post_detail
  
  def get_all(self, skip: int = 0, limit: int = 100) -> List[PostDetail]:
    posts = self.db.query(Post).options(
      joinedload(Post.creator)
    ).offset(skip).limit(limit).all()
    
    result = []
    for post in posts:
      reaction_data = self._get_reactions_for_post(post.id)
      post_dict = {
        **post.__dict__,
        'reaction': {
          'likes': reaction_data['like'],
          'dislikes': reaction_data['dislike'],
          'views': reaction_data['view'],
          'shares': reaction_data.get('share', {'count': 0, 'users': []}),
          'comments': reaction_data.get('comment', {}).get('comments', [])
        }
      }
      post_detail = PostDetail.model_validate(post_dict, from_attributes=True)
      result.append(post_detail)
    
    return result
  
  def get_bookmarked_posts(self, user_id: int, skip: int = 0, limit: int = 100) -> List[PostDetail]:
    posts = self.db.query(Post).options(
      joinedload(Post.creator)
    ).filter(Post.bookmarked_users.any(User.id == user_id)).offset(skip).limit(limit).all()
    
    result = []
    for post in posts:
      reaction_data = self._get_reactions_for_post(post.id)
      post_dict = {
        **post.__dict__,
        'reaction': {
          'likes': reaction_data['like'],
          'dislikes': reaction_data['dislike'],
          'views': reaction_data['view'],
          'shares': reaction_data.get('share', {'count': 0, 'users': []}),
          'comments': reaction_data.get('comment', {}).get('comments', [])
        }
      }
      post_detail = PostDetail.model_validate(post_dict, from_attributes=True)
      result.append(post_detail)
    
    return result
  
  def like(self, post_id: int, user_id: int) -> PostDetail:
    post = self.get_by_id(post_id)
    if not post:
      raise HTTPException(status_code=404, detail="Post not found")
    reaction = PostReaction(reaction_type="like", user_id=user_id, post_id=post_id)
    if self.db.query(PostReaction).filter(PostReaction.post_id == post_id, PostReaction.user_id == user_id).first():
      raise HTTPException(status_code=400, detail="Already liked this post")
    self.db.add(reaction)
    self.db.commit()
    return self.get_by_id(post_id)
  
  def delete_like(self, post_id: int, user_id: int) -> PostDetail:
    post = self.get_by_id(post_id)
    if not post:
      raise HTTPException(status_code=404, detail="Post not found")
    reaction = self.db.query(PostReaction).filter(PostReaction.post_id == post_id, PostReaction.user_id == user_id).first()
    if not reaction:
      raise HTTPException(status_code=400, detail="Reaction not found")
    self.db.delete(reaction)
    self.db.commit()
    return self.get_by_id(post_id)
    
  def dislike(self, post_id: int, user_id: int) -> PostDetail:
    post = self.get_by_id(post_id)
    if not post:
      raise HTTPException(status_code=404, detail="Post not found")
    reaction = PostReaction(reaction_type="dislike", user_id=user_id, post_id=post_id)
    if self.db.query(PostReaction).filter(PostReaction.post_id == post_id, PostReaction.user_id == user_id).first():
      raise HTTPException(status_code=400, detail="Already disliked this post")
    self.db.add(reaction)
    self.db.commit()
    return self.get_by_id(post_id)
  
  def delete_dislike(self, post_id: int, user_id: int) -> PostDetail:
    post = self.get_by_id(post_id)
    if not post:
      raise HTTPException(status_code=404, detail="Post not found")
    reaction = self.db.query(PostReaction).filter(PostReaction.post_id == post_id, PostReaction.user_id == user_id).first()
    if not reaction:
      raise HTTPException(status_code=400, detail="Reaction not found")
    self.db.delete(reaction)
    self.db.commit()
    return self.get_by_id(post_id)
  
  def view(self, post_id: int, user_id: int) -> PostDetail:
    post = self.get_by_id(post_id)
    if not post:
      raise HTTPException(status_code=404, detail="Post not found")
    reaction = PostReaction(reaction_type="view", user_id=user_id, post_id=post_id)
    if self.db.query(PostReaction).filter(PostReaction.post_id == post_id, PostReaction.user_id == user_id).first():
      raise HTTPException(status_code=400, detail="Already viewed this post")
    self.db.add(reaction)
    self.db.commit()
    return self.get_by_id(post_id)
  
  def share(self, post_id: int, user_id: int) -> PostDetail:
    post = self.get_by_id(post_id)
    if not post:
      raise HTTPException(status_code=404, detail="Post not found")
    reaction = PostReaction(reaction_type="share", user_id=user_id, post_id=post_id)
    if self.db.query(PostReaction).filter(PostReaction.post_id == post_id, PostReaction.user_id == user_id).first():
      raise HTTPException(status_code=400, detail="Already shared this post")
    self.db.add(reaction)
    self.db.commit()
    return self.get_by_id(post_id)
  
  def create_comment(self, post_id: int, user_id: int, comment_in: CommentCreate) -> PostDetail:
    post = self.get_by_id(post_id)
    if not post:
      raise HTTPException(status_code=404, detail="Post not found")
    comment = PostComment(post_id=post_id, user_id=user_id, content=comment_in.content)
    self.db.add(comment)
    self.db.commit()
    return self.get_by_id(post_id)
  
  def delete_comment(self, post_id: int, user_id: int, comment_id: int) -> PostDetail:
    post = self.get_by_id(post_id)
    if not post:
      raise HTTPException(status_code=404, detail="Post not found")
    comment = self.db.query(PostComment).filter(PostComment.post_id == post_id, PostComment.user_id == user_id, PostComment.id == comment_id).first()
    if not comment:
      raise HTTPException(status_code=404, detail="Comment not found")
    self.db.delete(comment)
    self.db.commit()
    return self.get_by_id(post_id)
  
  def bookmark(self, post_id: int, user_id: int) -> PostDetail:
    post = self.get_by_id(post_id)
    if not post:
      raise HTTPException(status_code=404, detail="Post not found")
    
    # Check if bookmark already exists
    existing = self.db.query(user_post_bookmarks).filter(
        user_post_bookmarks.c.post_id == post_id,
        user_post_bookmarks.c.user_id == user_id
    ).first()
    
    if existing:
      return self.get_by_id(post_id)
      
    # Insert new bookmark
    stmt = user_post_bookmarks.insert().values(post_id=post_id, user_id=user_id)
    self.db.execute(stmt)
    self.db.commit()
    return self.get_by_id(post_id)
  
  def delete_bookmark(self, post_id: int, user_id: int) -> PostDetail:
    post = self.get_by_id(post_id)
    if not post:
      raise HTTPException(status_code=404, detail="Post not found")
    
    # Check if bookmark exists
    existing = self.db.query(user_post_bookmarks).filter(
        user_post_bookmarks.c.post_id == post_id,
        user_post_bookmarks.c.user_id == user_id
    ).first()
    
    if not existing:
      return self.get_by_id(post_id)
      
    # Delete bookmark
    stmt = user_post_bookmarks.delete().where(
        user_post_bookmarks.c.post_id == post_id,
        user_post_bookmarks.c.user_id == user_id
    )
    self.db.execute(stmt)
    self.db.commit()
    return self.get_by_id(post_id)