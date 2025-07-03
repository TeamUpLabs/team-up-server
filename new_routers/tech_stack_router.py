from fastapi import APIRouter, Depends, HTTPException, status
from typing import List, Optional
from sqlalchemy.orm import Session

from database import get_db
from auth import get_current_user
from new_crud import tech_stack
from new_schemas.tech_stack import TechStackCreate, TechStackUpdate, TechStackDetail
from new_models.user import User

router = APIRouter(
    prefix="/api/tech-stacks",
    tags=["tech_stacks"]
)

@router.post("/", response_model=TechStackDetail, status_code=status.HTTP_201_CREATED)
def create_tech_stack(tech_in: TechStackCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """새 기술 스택 생성"""
    db_tech = tech_stack.create(db=db, obj_in=tech_in)
    return TechStackDetail.model_validate(db_tech, from_attributes=True)

@router.get("/", response_model=List[TechStackDetail])
def read_tech_stacks(
    skip: int = 0, 
    limit: int = 100, 
    category: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """기술 스택 목록 조회 (카테고리별 필터링 가능)"""
    if category:
        techs = tech_stack.get_by_category(db=db, category=category, skip=skip, limit=limit)
    else:
        techs = tech_stack.get_multi(db=db, skip=skip, limit=limit)
    return [TechStackDetail.model_validate(t, from_attributes=True) for t in techs]

@router.get("/{tech_id}", response_model=TechStackDetail)
def read_tech_stack(tech_id: int, db: Session = Depends(get_db)):
    """특정 기술 스택 정보 조회"""
    db_tech = tech_stack.get(db=db, id=tech_id)
    if db_tech is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="기술 스택을 찾을 수 없습니다.")
    return TechStackDetail.model_validate(db_tech, from_attributes=True)

@router.put("/{tech_id}", response_model=TechStackDetail)
def update_tech_stack(
    tech_id: int, 
    tech_in: TechStackUpdate, 
    db: Session = Depends(get_db), 
    current_user: User = Depends(get_current_user)
):
    """기술 스택 정보 수정"""
    db_tech = tech_stack.get(db=db, id=tech_id)
    if db_tech is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="기술 스택을 찾을 수 없습니다.")
    
    # 관리자만 수정 가능 (추후 권한 체크 로직 추가)
    
    db_tech = tech_stack.update(db=db, db_obj=db_tech, obj_in=tech_in)
    return TechStackDetail.model_validate(db_tech, from_attributes=True)

@router.delete("/{tech_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_tech_stack(tech_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """기술 스택 삭제"""
    db_tech = tech_stack.get(db=db, id=tech_id)
    if db_tech is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="기술 스택을 찾을 수 없습니다.")
    
    # 관리자만 삭제 가능 (추후 권한 체크 로직 추가)
    
    tech_stack.remove(db=db, id=tech_id)
    return None

@router.get("/{tech_id}/projects", response_model=List)
def read_tech_stack_projects(tech_id: int, db: Session = Depends(get_db)):
    """기술 스택을 사용하는 프로젝트 목록 조회"""
    from new_schemas.project import ProjectBrief
    projects = tech_stack.get_projects(db=db, tech_id=tech_id)
    return [ProjectBrief.model_validate(p, from_attributes=True) for p in projects] 