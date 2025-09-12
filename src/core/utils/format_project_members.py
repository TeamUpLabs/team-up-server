from sqlalchemy.orm import Session
from api.v1.models.association_tables import project_members
from api.v1.models.user.user import User
from typing import Dict, Any
from api.v1.schemas.brief import UserBrief

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
    
    return {
        "user": user_brief,
        "role": getattr(assoc, 'role', None) if assoc else None,
        "joined_at": getattr(assoc, 'joined_at', None) if assoc else None
    }