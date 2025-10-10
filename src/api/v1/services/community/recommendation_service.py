from typing import List, Dict, Any
from sqlalchemy.orm import Session
from src.api.v1.repositories.community.recommendation_repository import RecommendationRepository

class RecommendationService:
  def __init__(self, db: Session):
    self.repository = RecommendationRepository(db)
    
  def get_follow_recommendations(self, user_id: int, limit: int = 10, min_similarity: float = 0.1) -> List[Dict[str, Any]]:
    return self.repository.get_follow_recommendations(user_id=user_id, limit=limit, min_similarity=min_similarity)
  
  def get_similarity_breakdown(self, user_id: int, target_user_id: int) -> Dict[str, Any]:
    return self.repository.get_similarity_breakdown(user_id=user_id, target_user_id=target_user_id)
  
  def get_recommendation_stats(self, user_id: int) -> Dict[str, Any]:
    return self.repository.get_recommendation_stats(user_id=user_id)