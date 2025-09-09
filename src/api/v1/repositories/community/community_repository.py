from typing import Dict, Any, List
from collections import Counter
from sqlalchemy.orm import Session
from api.v1.repositories.community.post_repository import PostRepository
from api.v1.repositories.community.recommendation_repository import RecommendationRepository
from api.v1.models.community.post import Post

class CommunityRepository:
  def __init__(self, db: Session):
    self.db = db
    
  def get_info(self, user_id: int) -> Dict[str, Any]:
    hot_topic = self.get_all_tags(self.db, limit=3)
    posts = PostRepository(self.db).get_all(skip=0, limit=10)
    recommended_follow = RecommendationRepository(self.db).get_follow_recommendations(user_id=user_id, limit=3)
    
    return {
      "hot_topic": hot_topic,
      "posts": posts,
      "recommended_follow": recommended_follow
    }
    
  def get_all_tags(self, db: Session, limit: int = None) -> List[Dict[str, int]]:
    all_tags = [tag for tags in db.query(Post.tags).filter(Post.tags.isnot(None)).all() for tag in (tags[0] or [])]
    tag_counts = Counter(all_tags)
    
    # limit이 None이면 모든 태그 반환, 아니면 limit만큼만 반환
    most_common = tag_counts.most_common()
    if limit is not None:
      most_common = most_common[:limit]
      
    return [{"tag": tag, "count": count} for tag, count in most_common]
    