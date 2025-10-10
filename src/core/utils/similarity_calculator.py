"""
유저 유사도 계산 유틸리티
collaboration preference, tech_stacks, interests를 기반으로 유사도를 계산합니다.
"""

from typing import List, Tuple
from src.api.v1.models.user.user import User


class UserSimilarityCalculator:
    """유저 유사도 계산 클래스"""
    
    # 가중치 설정
    COLLABORATION_WEIGHT = 0.40
    TECH_STACK_WEIGHT = 0.35
    INTERESTS_WEIGHT = 0.25
    
    def __init__(self):
        pass
    
    def calculate_similarity(self, user1: User, user2: User) -> float:
        """
        두 유저 간의 전체 유사도를 계산합니다.
        
        Args:
            user1: 첫 번째 유저
            user2: 두 번째 유저
            
        Returns:
            float: 0.0 ~ 1.0 사이의 유사도 점수
        """
        # 각 구성요소별 유사도 계산
        collaboration_sim = self._calculate_collaboration_similarity(user1, user2)
        tech_stack_sim = self._calculate_tech_stack_similarity(user1, user2)
        interests_sim = self._calculate_interests_similarity(user1, user2)
        
        # 가중 평균으로 전체 유사도 계산
        total_similarity = (
            collaboration_sim * self.COLLABORATION_WEIGHT +
            tech_stack_sim * self.TECH_STACK_WEIGHT +
            interests_sim * self.INTERESTS_WEIGHT
        )
        
        return round(total_similarity, 4)
    
    def _calculate_collaboration_similarity(self, user1: User, user2: User) -> float:
        """협업 선호도 유사도 계산"""
        pref1 = user1.collaboration_preference
        pref2 = user2.collaboration_preference
        
        # 둘 중 하나라도 협업 선호도가 없으면 0 반환
        if not pref1 or not pref2:
            return 0.0
        
        similarities = []
        
        # collaboration_style 유사도
        if pref1.collaboration_style and pref2.collaboration_style:
            similarities.append(self._string_similarity(pref1.collaboration_style, pref2.collaboration_style))
        
        # preferred_project_type 유사도
        if pref1.preferred_project_type and pref2.preferred_project_type:
            similarities.append(self._string_similarity(pref1.preferred_project_type, pref2.preferred_project_type))
        
        # preferred_role 유사도
        if pref1.preferred_role and pref2.preferred_role:
            similarities.append(self._string_similarity(pref1.preferred_role, pref2.preferred_role))
        
        # available_time_zone 유사도
        if pref1.available_time_zone and pref2.available_time_zone:
            similarities.append(self._timezone_similarity(pref1.available_time_zone, pref2.available_time_zone))
        
        # work_hours 유사도
        if (pref1.work_hours_start is not None and pref1.work_hours_end is not None and
            pref2.work_hours_start is not None and pref2.work_hours_end is not None):
            similarities.append(self._work_hours_similarity(
                pref1.work_hours_start, pref1.work_hours_end,
                pref2.work_hours_start, pref2.work_hours_end
            ))
        
        # preferred_project_length 유사도
        if pref1.preferred_project_length and pref2.preferred_project_length:
            similarities.append(self._string_similarity(pref1.preferred_project_length, pref2.preferred_project_length))
        
        # 유사도가 계산된 항목이 없으면 0 반환
        if not similarities:
            return 0.0
        
        return sum(similarities) / len(similarities)
    
    def _calculate_tech_stack_similarity(self, user1: User, user2: User) -> float:
        """기술 스택 유사도 계산"""
        tech1 = {stack.tech: stack.level for stack in user1.tech_stacks}
        tech2 = {stack.tech: stack.level for stack in user2.tech_stacks}
        
        # 둘 중 하나라도 기술 스택이 없으면 0 반환
        if not tech1 or not tech2:
            return 0.0
        
        # 공통 기술 스택 찾기
        common_techs = set(tech1.keys()) & set(tech2.keys())
        
        if not common_techs:
            return 0.0
        
        # Jaccard 유사도 계산
        union_techs = set(tech1.keys()) | set(tech2.keys())
        jaccard_similarity = len(common_techs) / len(union_techs)
        
        # 숙련도 가중치 계산
        level_similarity = 0.0
        for tech in common_techs:
            level_diff = abs(tech1[tech] - tech2[tech])
            # 레벨 차이가 적을수록 높은 점수 (최대 차이 2를 기준으로 정규화)
            level_sim = max(0, 1 - (level_diff / 2))
            level_similarity += level_sim
        
        level_similarity /= len(common_techs)
        
        # Jaccard 유사도와 레벨 유사도의 평균
        return (jaccard_similarity + level_similarity) / 2
    
    def _calculate_interests_similarity(self, user1: User, user2: User) -> float:
        """관심분야 유사도 계산"""
        interests1 = {(interest.interest_category, interest.interest_name) for interest in user1.interests}
        interests2 = {(interest.interest_category, interest.interest_name) for interest in user2.interests}
        
        # 둘 중 하나라도 관심분야가 없으면 0 반환
        if not interests1 or not interests2:
            return 0.0
        
        # 교집합과 합집합 계산
        intersection = interests1 & interests2
        union = interests1 | interests2
        
        # Jaccard 유사도 계산
        return len(intersection) / len(union) if union else 0.0
    
    def _string_similarity(self, str1: str, str2: str) -> float:
        """문자열 유사도 계산 (간단한 정확 일치/부분 일치)"""
        str1_lower = str1.lower().strip()
        str2_lower = str2.lower().strip()
        
        if str1_lower == str2_lower:
            return 1.0
        
        # 부분 일치 체크 (한 문자열이 다른 문자열에 포함되는 경우)
        if str1_lower in str2_lower or str2_lower in str1_lower:
            return 0.5
        
        return 0.0
    
    def _timezone_similarity(self, tz1: str, tz2: str) -> float:
        """시간대 유사도 계산"""
        if tz1 == tz2:
            return 1.0
        
        # 주요 시간대 그룹 정의
        timezone_groups = {
            'Asia': ['Asia/Seoul', 'Asia/Tokyo', 'Asia/Shanghai', 'Asia/Hong_Kong'],
            'Europe': ['Europe/London', 'Europe/Paris', 'Europe/Berlin', 'Europe/Rome'],
            'America_East': ['America/New_York', 'America/Toronto', 'America/Montreal'],
            'America_West': ['America/Los_Angeles', 'America/Vancouver', 'America/Seattle'],
            'UTC': ['UTC']
        }
        
        # 각 시간대가 속한 그룹 찾기
        group1 = None
        group2 = None
        
        for group, timezones in timezone_groups.items():
            if tz1 in timezones:
                group1 = group
            if tz2 in timezones:
                group2 = group
        
        # 같은 그룹이면 0.7, 다른 그룹이면 0.3
        if group1 == group2:
            return 0.7
        else:
            return 0.3
    
    def _work_hours_similarity(self, start1: int, end1: int, start2: int, end2: int) -> float:
        """근무시간 유사도 계산"""
        # 근무시간 겹치는 부분 계산
        overlap_start = max(start1, start2)
        overlap_end = min(end1, end2)
        
        if overlap_start >= overlap_end:
            return 0.0
        
        overlap_hours = overlap_end - overlap_start
        
        # 각 유저의 총 근무시간
        total_hours1 = end1 - start1
        total_hours2 = end2 - start2
        
        # 겹치는 시간의 비율 계산
        overlap_ratio1 = overlap_hours / total_hours1 if total_hours1 > 0 else 0
        overlap_ratio2 = overlap_hours / total_hours2 if total_hours2 > 0 else 0
        
        # 두 비율의 평균
        return (overlap_ratio1 + overlap_ratio2) / 2
    
    def get_top_similar_users(self, target_user: User, all_users: List[User], 
                            exclude_following: bool = True, limit: int = 10) -> List[Tuple[User, float]]:
        """
        특정 유저와 가장 유사한 유저들을 반환합니다.
        
        Args:
            target_user: 기준이 되는 유저
            all_users: 비교할 모든 유저 리스트
            exclude_following: 이미 팔로우 중인 유저 제외 여부
            limit: 반환할 유저 수
            
        Returns:
            List[Tuple[User, float]]: (유저, 유사도) 튜플 리스트
        """
        similarities = []
        
        # 이미 팔로우 중인 유저 ID 집합
        following_ids = {user.id for user in target_user.following} if exclude_following else set()
        
        for user in all_users:
            # 자기 자신 제외
            if user.id == target_user.id:
                continue
            
            # 이미 팔로우 중인 유저 제외 (옵션)
            if exclude_following and user.id in following_ids:
                continue
            
            # 유사도 계산
            similarity = self.calculate_similarity(target_user, user)
            
            # 유사도가 0보다 큰 경우만 추가
            if similarity > 0:
                similarities.append((user, similarity))
        
        # 유사도 기준으로 정렬하고 상위 N개 반환
        similarities.sort(key=lambda x: x[1], reverse=True)
        return similarities[:limit]


# 전역 인스턴스 생성
similarity_calculator = UserSimilarityCalculator()
