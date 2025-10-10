from typing import Dict, Any, List
from sqlalchemy.orm import Session
from src.api.v1.repositories.community.community_repository import CommunityRepository

class CommunityService:
  def __init__(self, db: Session):
    self.repository = CommunityRepository(db)
    
  def get_info(self, user_id: int) -> Dict[str, Any]:
    return self.repository.get_info(user_id=user_id)
  
  def get_all_tags(self, limit: int = None) -> List[Dict[str, int]]:
    return self.repository.get_all_tags(limit=limit)