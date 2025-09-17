from sqlalchemy.orm import Session
from fastapi import HTTPException, status
from api.v1.models.project.whiteboard import WhiteBoard, Document, Attachment
from api.v1.schemas.project.whiteboard_schema import WhiteBoardDetail, WhiteBoardCreate, WhiteBoardUpdate
from api.v1.models.project.project import Project
from typing import List
from datetime import datetime

class WhiteBoardRepository:
  def __init__(self, db: Session):
    self.db = db
    
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
        
        self.db.commit()
        self.db.refresh(whiteboard)
      
      return WhiteBoardDetail.model_validate(whiteboard, from_attributes=True)
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
    whiteboard = self.db.query(WhiteBoard).filter(WhiteBoard.project_id == project_id, WhiteBoard.id == whiteboard_id).first()
    if not whiteboard:
      raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="화이트보드를 찾을 수 없습니다.")
    return WhiteBoardDetail.model_validate(whiteboard, from_attributes=True)
  
  def get_by_project(self, project_id: str, skip: int = 0, limit: int = 100) -> List[WhiteBoardDetail]:
    """프로젝트별 화이트보드 목록 조회"""
    project = self.db.query(Project).filter(Project.id == project_id).first()
    if not project:
      raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="프로젝트를 찾을 수 없습니다.")
    
    whiteboards = self.db.query(WhiteBoard).filter(WhiteBoard.project_id == project_id).offset(skip).limit(limit).all()
    
    return [WhiteBoardDetail.model_validate(w, from_attributes=True) for w in whiteboards]
    
  def update(self, project_id: str, whiteboard_id: int, whiteboard: WhiteBoardUpdate) -> WhiteBoardDetail:
    """
    화이트보드 업데이트
    """
    try:
      whiteboard = self.db.query(WhiteBoard).filter(WhiteBoard.project_id == project_id, WhiteBoard.id == whiteboard_id).first()
      if not whiteboard:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="화이트보드를 찾을 수 없습니다.")
      
      update_data = whiteboard.model_dump(exclude_unset=True)
      
      if whiteboard.type == "document":
        document = self.db.query(Document).filter(Document.whiteboard_id == whiteboard_id).first()
        if document:
          if "content" in update_data:
            document.content = update_data.pop("content")
          document.updated_at = datetime.utcnow()
          self.db.add(document)
          self.db.flush()
      
      for field, value in update_data.items():
        if hasattr(whiteboard, field):
          setattr(whiteboard, field, value)
      
      whiteboard.updated_at = datetime.utcnow()
      self.db.add(whiteboard)
      self.db.commit()
      self.db.refresh(whiteboard)
      
      if whiteboard.type == "document":
        document = self.db.query(Document).filter(Document.whiteboard_id == whiteboard_id).first()
        if document:
          whiteboard.content = document.content
    except Exception as e:
      self.db.rollback()
      raise HTTPException(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        detail=f"화이트보드 업데이트 중 오류 발생: {str(e)}"
      )
    
    return WhiteBoardDetail.model_validate(whiteboard, from_attributes=True)
    
  def remove(self, project_id: str, whiteboard_id: int) -> WhiteBoardDetail:
    """
    화이트보드 삭제
    """
    try:
      whiteboard = self.db.query(WhiteBoard).filter(WhiteBoard.project_id == project_id, WhiteBoard.id == whiteboard_id).first()
      if not whiteboard:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="화이트보드를 찾을 수 없습니다.")
      
      self.db.delete(whiteboard)
      self.db.commit()
      
      return WhiteBoardDetail.model_validate(whiteboard, from_attributes=True)
    except Exception as e:
      self.db.rollback()
      raise HTTPException(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        detail=f"화이트보드 삭제 중 오류 발생: {str(e)}"
      )