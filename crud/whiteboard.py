from crud.base import CRUDBase
from models.whiteboard import WhiteBoard, Document, Attachment
from schemas.whiteboard import WhiteBoardCreate, WhiteBoardUpdate, WhiteBoardDetail, DocumentCreate
from models.project import Project
from fastapi import HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime

class CRUDWhiteBoard(CRUDBase[WhiteBoard, WhiteBoardCreate, WhiteBoardUpdate]):
    """
    WhiteBoard 모델에 대한 CRUD 작업
    """
    
    def create(self, db: Session, *, obj_in: WhiteBoardCreate) -> WhiteBoard:
        """
        새 WhiteBoard 생성
        관계 검증 및 처리
        """
        # 프로젝트 존재 확인
        project = db.query(Project).filter(Project.id == obj_in.project_id).first()
        if not project:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"프로젝트 ID {obj_in.project_id}를 찾을 수 없습니다."
            )
        
        try:
            # WhiteBoard 생성
            whiteboard = WhiteBoard(
                type=obj_in.type,
                project_id=obj_in.project_id,
                title=obj_in.title,
                created_by=obj_in.created_by,
                updated_by=obj_in.updated_by,
            )
            db.add(whiteboard)
            db.flush()
    
            if obj_in.type == "document":
                # Create document
                document = Document(
                    whiteboard_id=whiteboard.id,
                    content=obj_in.content or "",
                    tags=obj_in.tags or [],
                )
                db.add(document)
                db.flush()
                
                # Add attachments if any
                if hasattr(obj_in, 'attachments') and obj_in.attachments:
                    for attachment_in in obj_in.attachments:
                        attachment = Attachment(
                            filename=attachment_in.filename,
                            file_url=attachment_in.file_url,
                            file_type=attachment_in.file_type,
                            file_size=attachment_in.file_size,
                            document_id=document.id
                        )
                        db.add(attachment)
                
                db.commit()
                db.refresh(whiteboard)
                
            return whiteboard
        except Exception as e:
            db.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"WhiteBoard 생성 중 오류 발생: {str(e)}"
            )
            
    def get_by_project(self, db: Session, *, project_id: str, skip: int = 0, limit: int = 100) -> List[WhiteBoardDetail]:
        """프로젝트별 WhiteBoard 목록 조회"""
        project = db.query(Project).filter(Project.id == project_id).first()
        if not project:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"프로젝트 ID {project_id}를 찾을 수 없습니다."
            )
        
        whiteboards = db.query(WhiteBoard).filter(WhiteBoard.project_id == project_id).offset(skip).limit(limit).all()
        
        return [WhiteBoardDetail.model_validate(w, from_attributes=True) for w in whiteboards]
    
    def get(self, db: Session, id: int) -> WhiteBoardDetail:
        """ID로 WhiteBoard 상세 조회"""
        whiteboard = db.query(WhiteBoard).filter(WhiteBoard.id == id).first()
        if not whiteboard:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"WhiteBoard ID {id}를 찾을 수 없습니다."
            )
        
        return WhiteBoardDetail.model_validate(whiteboard, from_attributes=True)
    
    def update(self, db: Session, *, id: int, obj_in: WhiteBoardUpdate) -> Optional[WhiteBoard]:
        """
        WhiteBoard 업데이트
        """
        try:
            whiteboard = db.query(self.model).filter(self.model.id == id).first()
            if not whiteboard:
                return None
                
            update_data = obj_in.dict(exclude_unset=True)
            
            # 문서 타입인 경우 content를 document에 업데이트
            if whiteboard.type == "document":
                document = db.query(Document).filter(Document.whiteboard_id == id).first()
                if document:
                    if "content" in update_data:
                        document.content = update_data.pop("content")
                    document.updated_at = datetime.utcnow()
                    db.add(document)
            
            # WhiteBoard 필드 업데이트
            for field, value in update_data.items():
                if hasattr(whiteboard, field):
                    setattr(whiteboard, field, value)
            
            whiteboard.updated_at = datetime.utcnow()
            db.add(whiteboard)
            db.commit()
            db.refresh(whiteboard)
            
            # If it's a document type, set the content for the response
            if whiteboard.type == "document":
                document = db.query(Document).filter(Document.whiteboard_id == id).first()
                if document:
                    whiteboard.content = document.content
            
            return whiteboard
            
        except Exception as e:
            db.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"WhiteBoard 업데이트 중 오류 발생: {str(e)}"
            )
    
    def remove(self, db: Session, *, id: int) -> WhiteBoardDetail:
        """WhiteBoard 삭제"""
        try:
            # WhiteBoard 조회
            whiteboard = db.query(WhiteBoard).filter(WhiteBoard.id == id).first()
            if not whiteboard:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"WhiteBoard ID {id}를 찾을 수 없습니다."
                )
            
            # 문서 내용 조회 (응답에 포함하기 위해)
            content = None
            if whiteboard.type == "document":
                document = db.query(Document).filter(Document.whiteboard_id == id).first()
                if document:
                    content = document.content
            
            # WhiteBoard 삭제 (CASCADE로 연관된 Document도 자동 삭제됨)
            db.delete(whiteboard)
            db.commit()
            
            # 삭제된 객체의 정보를 포함한 응답 생성
            response_data = WhiteBoardDetail(
                id=whiteboard.id,
                type=whiteboard.type,
                project_id=whiteboard.project_id,
                title=whiteboard.title,
                content=content,
                created_by=whiteboard.created_by,
                updated_by=whiteboard.updated_by,
                created_at=whiteboard.created_at,
                updated_at=whiteboard.updated_at
            )
            
            return response_data
            
        except Exception as e:
            db.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"WhiteBoard 삭제 중 오류 발생: {str(e)}"
            )
      
whiteboard = CRUDWhiteBoard(WhiteBoard)