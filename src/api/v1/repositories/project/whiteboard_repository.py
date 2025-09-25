from sqlalchemy.orm import Session, joinedload
from fastapi import HTTPException, status
from api.v1.models.project.whiteboard import (
  WhiteBoard,
  Document,
  Attachment,
  WhiteboardReaction,
  WhiteboardReactionLike,
  WhiteboardComment,
)
from api.v1.schemas.project.whiteboard_schema import (
  WhiteBoardDetail,
  WhiteBoardCreate,
  WhiteBoardUpdate,
  Reaction,
  ReactionLikes,
  ReactionComments,
  Comment,
  CommentCreate
)
from api.v1.schemas.brief import UserBrief
from api.v1.models.project.project import Project
from typing import List, Set
from datetime import datetime
import logging

class WhiteBoardRepository:
  def __init__(self, db: Session):
    self.db = db
    
  def _build_reaction(self, whiteboard: WhiteBoard) -> Reaction:
    # Aggregate over all reaction rows (if multiple exist) to one dictionary payload
    total_views = 0
    user_briefs: List[UserBrief] = []
    seen_user_ids: Set[int] = set()
    comment_items: List[Comment] = []

    for r in (whiteboard.reactions or []):
      total_views += (r.views or 0)
      # Collect unique users who liked
      for like in (r.likes or []):
        if like.user and getattr(like.user, "id", None) is not None and like.user.id not in seen_user_ids:
          seen_user_ids.add(like.user.id)
          user_briefs.append(UserBrief.model_validate(like.user, from_attributes=True))
      # Collect comments
      for c in (r.comments or []):
        comment_items.append(Comment.model_validate(c, from_attributes=True))

    likes = ReactionLikes(count=len(seen_user_ids), users=user_briefs)
    comments = ReactionComments(count=len(comment_items), comments=comment_items)
    # Return single objects for likes/comments to match schema
    return Reaction(likes=likes, views=total_views, comments=comments)

  def _attach_reactions(self, whiteboard: WhiteBoard) -> WhiteBoardDetail:
    detail = WhiteBoardDetail.model_validate(whiteboard, from_attributes=True)
    detail.reactions = self._build_reaction(whiteboard)
    return detail
    
  def create(self, project_id: str, obj_in: WhiteBoardCreate) -> WhiteBoardDetail:
    """
    새 화이트보드 생성
    관계 검증 및 처리
    """
    project = self.db.query(Project).filter(Project.id == project_id).first()
    if not project:
      raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="프로젝트를 찾을 수 없습니다.")
    
    try:
      whiteboard = WhiteBoard(
        project_id=project_id,
        type=obj_in.type,
        title=obj_in.title,
        created_by=obj_in.created_by,
        updated_by=obj_in.updated_by,
      )
      self.db.add(whiteboard)
      self.db.flush()
      
      if whiteboard.type == "document":
        try:
          document = Document(
            whiteboard_id=whiteboard.id,
            content=obj_in.content,
            tags=obj_in.tags
          )
          self.db.add(document)
          self.db.flush()
        except Exception as e:
          self.db.rollback()
          raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"문서 생성 중 오류 발생: {str(e)}"
          )
        
        try:
          if obj_in.attachments:
            for attachment in obj_in.attachments:
              attachment = Attachment(
                filename=attachment.filename,
                file_url=attachment.file_url,
                file_type=attachment.file_type,
                file_size=attachment.file_size,
                document_id=document.id
              )
              self.db.add(attachment)
              self.db.flush()
        except Exception as e:
          self.db.rollback()
          raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"첨부 파일 생성 중 오류 발생: {str(e)}"
          )
      
      # Ensure commit for both document and non-document types
      self.db.commit()
      self.db.refresh(whiteboard)
      
      return self._attach_reactions(whiteboard)
    except Exception as e:
      self.db.rollback()
      raise HTTPException(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        detail=f"화이트보드 생성 중 오류 발생: {str(e)}"
      )
    
  def get(self, project_id: str, whiteboard_id: int) -> WhiteBoardDetail:
    """
    프로젝트별 화이트보드 조회
    """
    whiteboard = (
      self.db.query(WhiteBoard)
      .options(
        joinedload(WhiteBoard.reactions)
          .joinedload(WhiteboardReaction.likes)
          .joinedload(WhiteboardReactionLike.user),
        joinedload(WhiteBoard.reactions).joinedload(WhiteboardReaction.comments),
      )
      .filter(WhiteBoard.project_id == project_id, WhiteBoard.id == whiteboard_id)
      .first()
    )
    if not whiteboard:
      raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="화이트보드를 찾을 수 없습니다.")
    return self._attach_reactions(whiteboard)
  
  def get_by_project(self, project_id: str, skip: int = 0, limit: int = 100) -> List[WhiteBoardDetail]:
    """프로젝트별 화이트보드 목록 조회"""
    project = self.db.query(Project).filter(Project.id == project_id).first()
    if not project:
      raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="프로젝트를 찾을 수 없습니다.")
    
    whiteboards = (
      self.db.query(WhiteBoard)
      .options(
        joinedload(WhiteBoard.reactions)
          .joinedload(WhiteboardReaction.likes)
          .joinedload(WhiteboardReactionLike.user),
        joinedload(WhiteBoard.reactions).joinedload(WhiteboardReaction.comments),
      )
      .filter(WhiteBoard.project_id == project_id)
      .offset(skip)
      .limit(limit)
      .all()
    )
    
    return [self._attach_reactions(w) for w in whiteboards]
    
  def update(self, project_id: str, whiteboard_id: int, whiteboard: WhiteBoardUpdate) -> WhiteBoardDetail:
    """
    화이트보드 업데이트
    """
    try:
      entity = self.db.query(WhiteBoard).filter(WhiteBoard.project_id == project_id, WhiteBoard.id == whiteboard_id).first()
      if not entity:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="화이트보드를 찾을 수 없습니다.")
      
      update_data = whiteboard.model_dump(exclude_unset=True)
      
      if entity.type == "document":
        document = self.db.query(Document).filter(Document.whiteboard_id == whiteboard_id).first()
        if document:
          if "content" in update_data:
            document.content = update_data.pop("content")
          document.updated_at = datetime.utcnow()
          self.db.add(document)
          
      for field, value in update_data.items():
        if hasattr(entity, field):
          setattr(entity, field, value)
      
      entity.updated_at = datetime.utcnow()
      self.db.add(entity)
      self.db.commit()
      self.db.refresh(entity)
          
      return self._attach_reactions(entity)
    except Exception as e:
      self.db.rollback()
      logging.error(f"화이트보드 업데이트 중 오류 발생: {str(e)}")
      raise HTTPException(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        detail=f"화이트보드 업데이트 중 오류 발생: {str(e)}"
      )
    
    return self._attach_reactions(whiteboard)
    
  def delete(self, project_id: str, whiteboard_id: int) -> WhiteBoardDetail:
    """
    화이트보드 삭제
    """
    try:
      whiteboard = self.db.query(WhiteBoard).filter(WhiteBoard.project_id == project_id, WhiteBoard.id == whiteboard_id).first()
      if not whiteboard:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="화이트보드를 찾을 수 없습니다.")
      
      self.db.delete(whiteboard)
      self.db.commit()
      
      return self._attach_reactions(whiteboard)
    except Exception as e:
      self.db.rollback()
      raise HTTPException(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        detail=f"화이트보드 삭제 중 오류 발생: {str(e)}"
      )
      
  def update_like(self, project_id: str, whiteboard_id: int, user_id: int) -> WhiteBoardDetail:
    """
    화이트보드 좋아요 업데이트
    """
    try:
      whiteboard = self.db.query(WhiteBoard).filter(WhiteBoard.project_id == project_id, WhiteBoard.id == whiteboard_id).first()
      if not whiteboard:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="화이트보드를 찾을 수 없습니다.")

      # Ensure there is a reaction row for this whiteboard (we treat it as a single aggregate per whiteboard)
      reaction = (
        self.db.query(WhiteboardReaction)
        .filter(WhiteboardReaction.whiteboard_id == whiteboard_id)
        .first()
      )
      if not reaction:
        reaction = WhiteboardReaction(whiteboard_id=whiteboard_id, views=0)
        self.db.add(reaction)
        self.db.flush()

      # Toggle like for this user on the reaction
      existing_like = (
        self.db.query(WhiteboardReactionLike)
        .filter(
          WhiteboardReactionLike.reaction_id == reaction.id,
          WhiteboardReactionLike.user_id == user_id,
        )
        .first()
      )

      if existing_like:
        self.db.delete(existing_like)
      else:
        self.db.add(WhiteboardReactionLike(reaction_id=reaction.id, user_id=user_id))

      self.db.commit()
      # Re-load with eager relationships to build reactions
      whiteboard = (
        self.db.query(WhiteBoard)
        .options(
          joinedload(WhiteBoard.reactions)
            .joinedload(WhiteboardReaction.likes)
            .joinedload(WhiteboardReactionLike.user),
          joinedload(WhiteBoard.reactions).joinedload(WhiteboardReaction.comments),
        )
        .filter(WhiteBoard.project_id == project_id, WhiteBoard.id == whiteboard_id)
        .first()
      )

      return self._attach_reactions(whiteboard)
    except Exception as e:
      self.db.rollback()
      raise HTTPException(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        detail=f"화이트보드 좋아요 업데이트 중 오류 발생: {str(e)}"
      )
      
  def update_view(self, project_id: str, whiteboard_id: int) -> WhiteBoardDetail:
    """
    화이트보드 조회수 업데이트
    """
    try:
      whiteboard = self.db.query(WhiteBoard).filter(WhiteBoard.project_id == project_id, WhiteBoard.id == whiteboard_id).first()
      if not whiteboard:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="화이트보드를 찾을 수 없습니다.")

      # Find or create a reaction aggregate for this whiteboard
      reaction = (
        self.db.query(WhiteboardReaction)
        .filter(WhiteboardReaction.whiteboard_id == whiteboard_id)
        .first()
      )
      if not reaction:
        reaction = WhiteboardReaction(whiteboard_id=whiteboard_id, views=1)
        self.db.add(reaction)
        self.db.flush()
      else:
        reaction.views = (reaction.views or 0) + 1
        self.db.add(reaction)

      self.db.commit()
      self.db.refresh(whiteboard)

      return self._attach_reactions(whiteboard)
    except Exception as e:
      self.db.rollback()
      raise HTTPException(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        detail=f"화이트보드 조회수 업데이트 중 오류 발생: {str(e)}"
      )
      
  def get_comments(self, project_id: str, whiteboard_id: int, skip: int = 0, limit: int = 100) -> List[Comment]:
    """댓글 목록 조회"""
    try:
      whiteboard = self.db.query(WhiteBoard).filter(WhiteBoard.project_id == project_id, WhiteBoard.id == whiteboard_id).first()
      if not whiteboard:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="화이트보드를 찾을 수 없습니다.")
      reaction = self.db.query(WhiteboardReaction).filter(WhiteboardReaction.whiteboard_id == whiteboard_id).first()
      if not reaction:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="화이트보드를 찾을 수 없습니다.")
      comments = self.db.query(WhiteboardComment).filter(WhiteboardComment.reaction_id == reaction.id).offset(skip).limit(limit).all()
      return [Comment.model_validate(c, from_attributes=True) for c in comments]
    except Exception as e:
      self.db.rollback()
      raise HTTPException(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        detail=f"댓글 목록 조회 중 오류 발생: {str(e)}"
      )
      
  def create_comment(self, project_id: str, whiteboard_id: int, comment: CommentCreate) -> Comment:
    """댓글 생성"""
    try:
      whiteboard = self.db.query(WhiteBoard).filter(WhiteBoard.project_id == project_id, WhiteBoard.id == whiteboard_id).first()
      if not whiteboard:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="화이트보드를 찾을 수 없습니다.")
      reaction = self.db.query(WhiteboardReaction).filter(WhiteboardReaction.whiteboard_id == whiteboard_id).first()
      if not reaction:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="화이트보드를 찾을 수 없습니다.")
      comment = WhiteboardComment(
        reaction_id=reaction.id,
        whiteboard_id=whiteboard_id,
        content=comment.content,
        created_by=comment.created_by,
      )
      self.db.add(comment)
      self.db.commit()
      self.db.refresh(comment)
      return Comment.model_validate(comment, from_attributes=True)
    except Exception as e:
      self.db.rollback()
      raise HTTPException(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        detail=f"댓글 생성 중 오류 발생: {str(e)}"
      )
      
  def delete_comment(self, project_id: str, whiteboard_id: int, comment_id: int) -> WhiteBoardDetail:
    """댓글 삭제"""
    try:
      whiteboard = self.db.query(WhiteBoard).filter(WhiteBoard.project_id == project_id, WhiteBoard.id == whiteboard_id).first()
      if not whiteboard:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="화이트보드를 찾을 수 없습니다.")
      reaction = self.db.query(WhiteboardReaction).filter(WhiteboardReaction.whiteboard_id == whiteboard_id).first()
      if not reaction:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="화이트보드를 찾을 수 없습니다.")
      comment = self.db.query(WhiteboardComment).filter(WhiteboardComment.id == comment_id).first()
      if not comment:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="댓글을 찾을 수 없습니다.")
      self.db.delete(comment)
      self.db.commit()
      self.db.refresh(whiteboard)
      return self._attach_reactions(whiteboard)
    except Exception as e:
      self.db.rollback()
      raise HTTPException(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        detail=f"댓글 삭제 중 오류 발생: {str(e)}"
      )