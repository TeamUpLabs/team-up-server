from sqlalchemy.orm import Session
from src.api.v1.models.association_tables import project_members
from src.api.v1.models.user.user import User
from typing import Dict, Any
from src.api.v1.schemas.brief import UserBrief

def format_member_details(db: Session, project_id: str, member: User) -> Dict[str, Any]:
    """
    프로젝트 멤버의 상세 정보를 포맷팅합니다.
    """
    # Get the association data from the association table
    stmt = project_members.select().where(
        (project_members.c.project_id == project_id) & 
        (project_members.c.user_id == member.id)
    )
    assoc = db.execute(stmt).first()
    
    # Create UserBrief instance and explicitly set links
    user_brief = UserBrief.model_validate(member, from_attributes=True)
    
    # Explicitly set the links since they might not be set during model_validate
    user_brief.links = {
        "self": {
            "href": f"/api/v1/users/{user_brief.id}",
            "method": "GET",
            "title": "사용자 정보 조회"
        }
    }
    
    # Determine the role based on is_leader and is_manager flags
    role = None
    if assoc:
        if assoc.is_leader == 1:
            role = "leader"
        elif assoc.is_manager == 1:
            role = "manager"
        else:
            role = getattr(assoc, 'role', 'member')  # Default to 'member' if role is not set
    
    return {
        "user": user_brief,
        "role": role,
        "is_leader": bool(assoc.is_leader) if assoc else False,
        "is_manager": bool(assoc.is_manager) if assoc else False,
        "joined_at": getattr(assoc, 'joined_at', None) if assoc else None
    }