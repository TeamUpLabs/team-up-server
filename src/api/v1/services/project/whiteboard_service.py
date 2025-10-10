from sqlalchemy.orm import Session
from src.api.v1.repositories.project.whiteboard_repository import WhiteBoardRepository
from src.api.v1.schemas.project.whiteboard_schema import WhiteBoardCreate, WhiteBoardUpdate, WhiteBoardDetail, Comment, CommentCreate
from typing import List

class WhiteBoardService:
  def __init__(self, db: Session):
    self.repository = WhiteBoardRepository(db)
    
  def create(self, project_id: str, whiteboard: WhiteBoardCreate) -> WhiteBoardDetail:
    return self.repository.create(project_id, whiteboard)
    
  def get(self, project_id: str, whiteboard_id: int) -> WhiteBoardDetail:
    return self.repository.get(project_id, whiteboard_id)
    
  def get_by_project(self, project_id: str, skip: int = 0, limit: int = 100) -> List[WhiteBoardDetail]:
    return self.repository.get_by_project(project_id, skip, limit)
    
  def update(self, project_id: str, whiteboard_id: int, whiteboard: WhiteBoardUpdate) -> WhiteBoardDetail:
    return self.repository.update(project_id, whiteboard_id, whiteboard)
    
  def delete(self, project_id: str, whiteboard_id: int) -> WhiteBoardDetail:
    return self.repository.delete(project_id, whiteboard_id)
  
  def update_like(self, project_id: str, whiteboard_id: int, user_id: int) -> WhiteBoardDetail:
    return self.repository.update_like(project_id, whiteboard_id, user_id)
  
  def update_view(self, project_id: str, whiteboard_id: int) -> WhiteBoardDetail:
    return self.repository.update_view(project_id, whiteboard_id)
  
  def get_comments(self, project_id: str, whiteboard_id: int, skip: int = 0, limit: int = 100) -> List[Comment]:
    return self.repository.get_comments(project_id, whiteboard_id, skip, limit)
  
  def create_comment(self, project_id: str, whiteboard_id: int, comment: CommentCreate) -> Comment:
    return self.repository.create_comment(project_id, whiteboard_id, comment)
  
  def delete_comment(self, project_id: str, whiteboard_id: int, comment_id: int) -> WhiteBoardDetail:
    return self.repository.delete_comment(project_id, whiteboard_id, comment_id)
    