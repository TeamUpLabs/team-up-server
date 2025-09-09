from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field


class TechStackInfo(BaseModel):
  """기술 스택 정보"""
  tech: str
  level: int


class InterestInfo(BaseModel):
  """관심분야 정보"""
  category: str
  name: str


class WorkHoursInfo(BaseModel):
  """근무시간 정보"""
  start: Optional[int] = None
  end: Optional[int] = None


class CollaborationPreferenceInfo(BaseModel):
  """협업 선호도 정보"""
  collaboration_style: Optional[str] = None
  preferred_project_type: Optional[str] = None
  preferred_role: Optional[str] = None
  available_time_zone: Optional[str] = None
  work_hours: Optional[WorkHoursInfo] = None
  preferred_project_length: Optional[str] = None


class CommonTechStackInfo(BaseModel):
  """공통 기술 스택 정보"""
  tech: str
  user1_level: int
  user2_level: int
  level_difference: int


class CommonInterestInfo(BaseModel):
  """공통 관심분야 정보"""
  category: str
  name: str


class FollowRecommendationResponse(BaseModel):
  """팔로우 추천 응답"""
  user_id: int
  name: str
  email: str
  profile_image: Optional[str] = None
  bio: Optional[str] = None
  role: Optional[str] = None
  similarity_score: float = Field(..., description="유사도 점수 (0.0 ~ 1.0)")
  collaboration_preference: Optional[CollaborationPreferenceInfo] = None
  tech_stacks: List[TechStackInfo] = []
  interests: List[InterestInfo] = []
  common_tech_stacks: List[CommonTechStackInfo] = []
  common_interests: List[CommonInterestInfo] = []


class SimilarityBreakdownResponse(BaseModel):
  """유사도 분석 응답"""
  total_similarity: float = Field(..., description="전체 유사도 점수")
  breakdown: Dict[str, Dict[str, float]] = Field(..., description="구성요소별 유사도 분석")
  common_elements: Dict[str, Any] = Field(..., description="공통 요소들")


class RecommendationStatsResponse(BaseModel):
  """추천 통계 응답"""
  user_id: int
  total_active_users: int
  following_count: int
  available_for_recommendation: int
  profile_completeness: Dict[str, Any]


class RecommendationRequest(BaseModel):
  """추천 요청"""
  limit: Optional[int] = Field(10, ge=1, le=50, description="반환할 추천 수")
  min_similarity: Optional[float] = Field(0.1, ge=0.0, le=1.0, description="최소 유사도 임계값")


class SimilarityAnalysisRequest(BaseModel):
  """유사도 분석 요청"""
  target_user_id: int = Field(..., description="비교 대상 유저 ID")
