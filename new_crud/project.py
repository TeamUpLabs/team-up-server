from typing import List, Dict, Any
from sqlalchemy.orm import Session
from fastapi import HTTPException, status
from new_models.project import Project
from new_models.user import User
from new_models.participation_request import ParticipationRequest
from new_schemas.project import ProjectCreate, ProjectUpdate
from new_crud.base import CRUDBase
from new_models.association_tables import project_members

class CRUDProject(CRUDBase[Project, ProjectCreate, ProjectUpdate]):
    """프로젝트 모델에 대한 CRUD 작업"""
    
    def create(self, db: Session, *, obj_in: ProjectCreate) -> Project:
        """
        새 프로젝트 생성
        사용자, 기술 스택 및 멤버 관계 처리
        """
        # 기본 데이터 준비
        obj_in_data = obj_in.model_dump(exclude={"tech_stack_ids", "member_ids"})
        
        # 소유자 확인
        owner = db.query(User).filter(User.id == obj_in.owner_id).first()
        if not owner:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"소유자 ID {obj_in.owner_id}를 찾을 수 없습니다."
            )
        
        # 프로젝트 생성
        db_obj = Project(**obj_in_data)
        
        # 멤버 추가
        if obj_in.member_ids:
            member_ids = set(obj_in.member_ids)
            # 소유자는 항상 멤버로 포함
            member_ids.add(obj_in.owner_id)
            
            members = db.query(User).filter(User.id.in_(member_ids)).all()
            if len(members) != len(member_ids):
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="일부 사용자를 찾을 수 없습니다."
                )
            db_obj.members = members
        else:
            # 소유자만 멤버로 추가
            db_obj.members = [owner]
        
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        
        # 소유자를 리더로 설정
        db.query(project_members).filter(
            project_members.c.project_id == db_obj.id,
            project_members.c.user_id == obj_in.owner_id
        ).update({
            "role": "leader",
            "is_leader": 1,
            "is_manager": 0
        })
        
        db.commit()
        db.refresh(db_obj)
        return db_obj
    
    def update(self, db: Session, *, db_obj: Project, obj_in: ProjectUpdate) -> Project:
        """
        프로젝트 정보 업데이트
        기술 스택 관계 처리
        """
        update_data = obj_in.model_dump(exclude_unset=True)
        
        return super().update(db, db_obj=db_obj, obj_in=update_data)
    
    def get_project_members(self, db: Session, *, project_id: str) -> List[Dict[str, Any]]:
        """
        프로젝트 멤버 정보 조회 (역할, 리더 여부, 관리자 여부, 가입일 포함)
        """
        result = []
        stmt = db.query(
            User, 
            project_members.c.role,
            project_members.c.is_leader,
            project_members.c.is_manager,
            project_members.c.joined_at
        ).join(
            project_members, 
            User.id == project_members.c.user_id
        ).filter(
            project_members.c.project_id == project_id
        ).all()
        
        for user, role, is_leader, is_manager, joined_at in stmt:
            result.append({
                "user": user,
                "role": role,
                "is_leader": bool(is_leader),
                "is_manager": bool(is_manager),
                "joined_at": joined_at
            })
        
        return result
    
    def get_members(self, db: Session, *, project_id: str) -> List[User]:
        """프로젝트 멤버 목록 조회"""
        project = self.get(db, id=project_id)
        if not project:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="프로젝트를 찾을 수 없습니다."
            )
        return project.members
    
    def add_member(self, db: Session, *, project_id: str, user_id: int) -> Project:
        """프로젝트에 멤버 추가"""
        project = self.get(db, id=project_id)
        if not project:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="프로젝트를 찾을 수 없습니다."
            )
            
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="사용자를 찾을 수 없습니다."
            )
            
        if user in project.members:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="이미 프로젝트의 멤버입니다."
            )
            
        project.members.append(user)
        db.commit()
        db.refresh(project)
        return project
    
    def remove_member(self, db: Session, *, project_id: str, user_id: int) -> Project:
        """프로젝트에서 멤버 제거"""
        project = self.get(db, id=project_id)
        if not project:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="프로젝트를 찾을 수 없습니다."
            )
            
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="사용자를 찾을 수 없습니다."
            )
            
        if user not in project.members:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="프로젝트의 멤버가 아닙니다."
            )
            
        if project.owner_id == user_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="프로젝트 소유자는 제거할 수 없습니다."
            )
            
        project.members.remove(user)
        db.commit()
        db.refresh(project)
        return project
    
    def is_manager(self, db: Session, *, project_id: str, user_id: int) -> bool:
        """사용자가 프로젝트 관리자인지 확인"""
        stmt = db.query(project_members).filter(
            project_members.c.project_id == project_id,
            project_members.c.user_id == user_id,
            project_members.c.is_leader == 1
        ).first()
        
        return stmt is not None
    
    def get_milestones(self, db: Session, *, project_id: str) -> List:
        """프로젝트 마일스톤 목록 조회"""
        project = self.get(db, id=project_id)
        if not project:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="프로젝트를 찾을 수 없습니다."
            )
        return project.milestones
    
    def get_tasks(self, db: Session, *, project_id: str) -> List:
        """프로젝트 업무 목록 조회"""
        project = self.get(db, id=project_id)
        if not project:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="프로젝트를 찾을 수 없습니다."
            )
        return project.tasks
    
    def get_participation_requests(self, db: Session, *, project_id: str, status: str = None) -> List[ParticipationRequest]:
        """프로젝트 참여 요청/초대 목록 조회"""
        query = db.query(ParticipationRequest).filter(ParticipationRequest.project_id == project_id)
        
        if status:
            query = query.filter(ParticipationRequest.status == status)
            
        return query.all()
    
    def get_all_project_excluding_me(self, db: Session, *, member_id: int) -> List[Project]:
        """내가 속한 프로젝트를 제외한 모든 프로젝트 조회"""
        member = db.query(User).filter(User.id == member_id).first()
        if not member:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="사용자를 찾을 수 없습니다."
            )
            
        projects_to_exclude = member.projects if member.projects is not None else []
        other_projects = db.query(Project).filter(Project.id.not_in([p.id for p in projects_to_exclude])).all()
            
        return other_projects

    def get_all_project_ids(self, db: Session) -> List[str]:
        """모든 프로젝트 ID 조회"""
        projects = db.query(Project).all()
        return [project.id for project in projects]
    
    def update_project_member_permission(self, db: Session, *, project_id: str, user_id: int, permission: str) -> Project:
        """프로젝트 멤버 권한 수정"""
        project = self.get(db, id=project_id)
        if not project:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="프로젝트를 찾을 수 없습니다."
            )
        member = db.query(User).filter(User.id == user_id).first()
        if not member:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="사용자를 찾을 수 없습니다."
            )
            
        # 사용자가 프로젝트에 속해 있는지 확인
        if member not in project.members:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="이 사용자는 프로젝트의 멤버가 아닙니다."
            )
            
        # 권한 설정에 따른 값 변경
        role = "member"
        is_leader = 0
        is_manager = 0
        
        if permission == "leader":
            role = "leader"
            is_leader = 1
        elif permission == "manager":
            role = "manager"
            is_manager = 1
        # "member"인 경우 둘 다 0으로 유지
        
        # 프로젝트-멤버 관계 테이블 업데이트
        db.query(project_members).filter(
            project_members.c.project_id == project_id,
            project_members.c.user_id == user_id
        ).update({
            "role": role,
            "is_leader": is_leader,
            "is_manager": is_manager
        })
            
        db.commit()
        db.refresh(project)
        return project
# CRUDProject 클래스 인스턴스 생성
project = CRUDProject(Project) 