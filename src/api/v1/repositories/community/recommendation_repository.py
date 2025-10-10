from sqlalchemy.orm import Session
from typing import List, Dict, Any, Optional
from fastapi import HTTPException
from src.core.utils.similarity_calculator import similarity_calculator
from src.api.v1.models.user import User

class RecommendationRepository:
  def __init__(self, db: Session):
    self.db = db
    
  def get_follow_recommendations(self, user_id: int, limit: int = 10, min_similarity: float = 0.1) -> List[Dict[str, Any]]:
    """
    특정 유저를 위한 팔로우 추천을 반환합니다.
    
    Args:
        db: 데이터베이스 세션
        user_id: 추천을 받을 유저 ID
        limit: 반환할 추천 수
        min_similarity: 최소 유사도 임계값
        
    Returns:
        List[Dict]: 추천 유저 정보와 유사도 점수 리스트
    """
    target_user = self.db.query(User).filter(User.id == user_id).first()
    if not target_user:
      raise HTTPException(status_code=404, detail="User not found")
    
    all_users = self.db.query(User).filter(User.id != user_id).all()
    
    similar_users = similarity_calculator.get_top_similar_users(
      target_user=target_user,
      all_users=all_users,
      exclude_following=True,
      limit=limit * 2
    )
    
    filtered_recommendations = [
      (user, similarity) for user, similarity in similar_users 
      if similarity >= min_similarity
    ]
    
    recommendations = []
    for user, similarity in filtered_recommendations[:limit]:
      recommendation = {
        "user_id": user.id,
        "name": user.name,
        "email": user.email,
        "profile_image": user.profile_image,
        "bio": user.bio,
        "role": user.role,
        "similarity_score": similarity,
        "collaboration_preference": self._format_collaboration_preference(user.collaboration_preference),
        "tech_stacks": [{"tech": stack.tech, "level": stack.level} for stack in user.tech_stacks],
        "interests": [{"category": interest.interest_category, "name": interest.interest_name} 
                    for interest in user.interests],
        "common_tech_stacks": self._get_common_tech_stacks(target_user, user),
        "common_interests": self._get_common_interests(target_user, user)
      }
      recommendations.append(recommendation)
    
    return recommendations
  
  def get_similarity_breakdown(self, user_id: int, target_user_id: int) -> Dict[str, Any]:
    """
    두 유저 간의 상세 유사도 분석을 반환합니다.
    
    Args:
        user_id: 기준 유저 ID
        target_user_id: 비교 대상 유저 ID
        
    Returns:
        Dict: 상세 유사도 분석 결과
    """
    user1 = self.db.query(User).filter(User.id == user_id).first()
    user2 = self.db.query(User).filter(User.id == target_user_id).first()
    
    if not user1 or not user2:
      raise HTTPException(status_code=404, detail="User not found")
    
    # 각 구성요소별 유사도 계산
    collaboration_sim = similarity_calculator._calculate_collaboration_similarity(user1, user2)
    tech_stack_sim = similarity_calculator._calculate_tech_stack_similarity(user1, user2)
    interests_sim = similarity_calculator._calculate_interests_similarity(user1, user2)
    
    # 전체 유사도 계산
    total_similarity = similarity_calculator.calculate_similarity(user1, user2)
    
    return {
      "total_similarity": total_similarity,
      "breakdown": {
        "collaboration_preference": {
          "similarity": collaboration_sim,
          "weight": similarity_calculator.COLLABORATION_WEIGHT,
          "contribution": collaboration_sim * similarity_calculator.COLLABORATION_WEIGHT
        },
        "tech_stacks": {
          "similarity": tech_stack_sim,
          "weight": similarity_calculator.TECH_STACK_WEIGHT,
          "contribution": tech_stack_sim * similarity_calculator.TECH_STACK_WEIGHT
        },
        "interests": {
          "similarity": interests_sim,
          "weight": similarity_calculator.INTERESTS_WEIGHT,
          "contribution": interests_sim * similarity_calculator.INTERESTS_WEIGHT
        }
      },
      "common_elements": {
        "tech_stacks": self._get_common_tech_stacks(user1, user2),
        "interests": self._get_common_interests(user1, user2),
        "collaboration_preferences": self._get_common_collaboration_preferences(user1, user2)
      }
    }
    
  def _format_collaboration_preference(self, preference) -> Optional[Dict[str, Any]]:
    """협업 선호도를 포맷팅합니다."""
    if not preference:
      return None
    
    return {
      "collaboration_style": preference.collaboration_style,
      "preferred_project_type": preference.preferred_project_type,
      "preferred_role": preference.preferred_role,
      "available_time_zone": preference.available_time_zone,
      "work_hours": {
        "start": preference.work_hours_start,
        "end": preference.work_hours_end
      },
      "preferred_project_length": preference.preferred_project_length
    }
    
  def _get_common_tech_stacks(self, user1: User, user2: User) -> List[Dict[str, Any]]:
    """두 유저의 공통 기술 스택을 반환합니다."""
    tech1 = {stack.tech: stack.level for stack in user1.tech_stacks}
    tech2 = {stack.tech: stack.level for stack in user2.tech_stacks}
    
    common_techs = set(tech1.keys()) & set(tech2.keys())
    
    return [
      {
        "tech": tech,
        "user1_level": tech1[tech],
        "user2_level": tech2[tech],
        "level_difference": abs(tech1[tech] - tech2[tech])
      }
      for tech in common_techs
    ]
    
  def _get_common_interests(self, user1: User, user2: User) -> List[Dict[str, Any]]:
    """두 유저의 공통 관심분야를 반환합니다."""
    interests1 = {(interest.interest_category, interest.interest_name) for interest in user1.interests}
    interests2 = {(interest.interest_category, interest.interest_name) for interest in user2.interests}
    
    common_interests = interests1 & interests2
    
    return [
      {"category": category, "name": name}
      for category, name in common_interests
    ]
    
  def _get_common_collaboration_preferences(self, user1: User, user2: User) -> Dict[str, Any]:
    """두 유저의 공통 협업 선호도를 반환합니다."""
    pref1 = user1.collaboration_preference
    pref2 = user2.collaboration_preference
    
    if not pref1 or not pref2:
      return {}
    
    common_preferences = {}
    
    # 각 필드별로 공통점 찾기
    if (pref1.collaboration_style and pref2.collaboration_style and 
        pref1.collaboration_style.lower() == pref2.collaboration_style.lower()):
        common_preferences["collaboration_style"] = pref1.collaboration_style
    
    if (pref1.preferred_project_type and pref2.preferred_project_type and 
        pref1.preferred_project_type.lower() == pref2.preferred_project_type.lower()):
        common_preferences["preferred_project_type"] = pref1.preferred_project_type
    
    if (pref1.preferred_role and pref2.preferred_role and 
        pref1.preferred_role.lower() == pref2.preferred_role.lower()):
        common_preferences["preferred_role"] = pref1.preferred_role
    
    if (pref1.available_time_zone and pref2.available_time_zone and 
        pref1.available_time_zone == pref2.available_time_zone):
        common_preferences["available_time_zone"] = pref1.available_time_zone
    
    if (pref1.preferred_project_length and pref2.preferred_project_length and 
        pref1.preferred_project_length.lower() == pref2.preferred_project_length.lower()):
        common_preferences["preferred_project_length"] = pref1.preferred_project_length
    
    return common_preferences
  
  def get_recommendation_stats(self, user_id: int) -> Dict[str, Any]:
    """
    특정 유저의 추천 통계를 반환합니다.
    
    Args:
        user_id: 추천 통계를 조회할 유저 ID
        
    Returns:
        Dict: 추천 통계 결과
    """
    target_user = self.db.query(User).filter(User.id == user_id).first()
    
    if not target_user:
      raise HTTPException(status_code=404, detail="User not found")
    
    total_active_users = self.db.query(User).filter(User.status == "active").count()
    
    following_count = len(target_user.following)
    
    available_for_recommendation = total_active_users - 1 - following_count
    
    has_collaboration_preference = target_user.collaboration_preference is not None
    has_tech_stacks = len(target_user.tech_stacks) > 0
    has_interests = len(target_user.interests) > 0
    
    return {
      "user_id": user_id,
      "total_active_users": total_active_users,
      "following_count": following_count,
      "available_for_recommendation": available_for_recommendation,
      "profile_completeness": {
        "has_collaboration_preference": has_collaboration_preference,
        "has_tech_stacks": has_tech_stacks,
        "has_interests": has_interests,
        "completeness_score": sum([has_collaboration_preference, has_tech_stacks, has_interests]) / 3
      }
    }