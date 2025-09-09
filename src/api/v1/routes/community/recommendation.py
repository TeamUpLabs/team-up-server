from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from api.v1.services.community.recommendation_service import RecommendationService
from api.v1.schemas.community.recommendation_schema import FollowRecommendationResponse, RecommendationRequest, SimilarityBreakdownResponse, SimilarityAnalysisRequest, RecommendationStatsResponse
from typing import List
from core.security.auth import get_current_user
from core.database.database import get_db

router = APIRouter(prefix="/api/v1/community/recommendation", tags=["recommendation"])

@router.get("/follow-recommendations", response_model=List[FollowRecommendationResponse])
async def get_follow_recommendations(
  limit: int = 10,
  min_similarity: float = 0.2,
  db: Session = Depends(get_db),
  current_user: dict = Depends(get_current_user)
):
  try:
    if not current_user:
      raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Unauthorized")
    
    service = RecommendationService(db)
    return service.get_follow_recommendations(
      user_id=current_user.id,
      limit=limit,
      min_similarity=min_similarity
    )
  except Exception as e:
    raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))
  
@router.post("/follow-recommendations", response_model=List[FollowRecommendationResponse])
async def get_follow_recommendations_with_request(
  request: RecommendationRequest,
  db: Session = Depends(get_db),
  current_user: dict = Depends(get_current_user)
):
  try:
    if not current_user:
      raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Unauthorized")
    
    service = RecommendationService(db)
    return service.get_follow_recommendations(
      user_id=current_user.id,
      limit=request.limit,
      min_similarity=request.min_similarity
    )
  except Exception as e:
    raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

@router.get("/similarity-analysis/{target_user_id}", response_model=SimilarityBreakdownResponse)
async def get_similarity_analysis(
  target_user_id: int,
  db: Session = Depends(get_db),
  current_user: dict = Depends(get_current_user)
):
  try:
    if not current_user:
      raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Unauthorized")
    
    service = RecommendationService(db)
    return service.get_similarity_analysis(
      user_id=current_user.id,
      target_user_id=target_user_id
    )
  except Exception as e:
    raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

@router.post("/similarity-analysis", response_model=SimilarityBreakdownResponse)
async def get_similarity_analysis_with_request(
  request: SimilarityAnalysisRequest,
  db: Session = Depends(get_db),
  current_user: dict = Depends(get_current_user)
):
  try:
    if not current_user:
      raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Unauthorized")
    
    service = RecommendationService(db)
    return service.get_similarity_analysis(
      user_id=current_user.id,
      target_user_id=request.target_user_id
    )
  except Exception as e:
    raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

@router.get("/stats", response_model=RecommendationStatsResponse)
async def get_recommendation_stats(
  db: Session = Depends(get_db),
  current_user: dict = Depends(get_current_user)
):
  try:
    if not current_user:
      raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Unauthorized")
    
    service = RecommendationService(db)
    return service.get_recommendation_stats(
      user_id=current_user.id
    )
  except Exception as e:
    raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

@router.get("/health")
async def health_check():
  return {
    "status": "healthy",
    "service": "recommendation",
    "message": "추천 시스템이 정상적으로 작동 중입니다."
  }
