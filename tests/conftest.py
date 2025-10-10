"""
Pytest 설정 파일 (conftest.py)
테스트 실행을 위한 공통 설정 및 fixture들을 정의합니다.
"""
import pytest
import tempfile
import os
from typing import Generator
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from unittest.mock import Mock

# 테스트용 데이터베이스 설정
TEST_DATABASE_URL = "sqlite:///./test.db"

# 테스트용 엔진 생성
test_engine = create_engine(
    TEST_DATABASE_URL,
    connect_args={"check_same_thread": False}
)

# 테스트용 세션 팩토리
TestSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)


@pytest.fixture(scope="session")
def test_db():
    """테스트용 데이터베이스 fixture"""
    # 테스트 데이터베이스 생성
    from src.core.database.database import Base
    Base.metadata.create_all(bind=test_engine)
    yield test_engine
    # 테스트 후 정리
    Base.metadata.drop_all(bind=test_engine)
    os.remove("./test.db")


@pytest.fixture
def db_session(test_db) -> Generator[Session, None, None]:
    """데이터베이스 세션 fixture"""
    connection = test_engine.connect()
    transaction = connection.begin()
    session = TestSessionLocal(bind=connection)

    yield session

    session.close()
    transaction.rollback()
    connection.close()


@pytest.fixture
def client(db_session) -> TestClient:
    """FastAPI 테스트 클라이언트 fixture"""
    from main import app
    from src.core.database.database import get_db

    # 테스트용 설정 오버라이드
    test_app = app

    # 데이터베이스 의존성 오버라이드
    def override_get_db():
        try:
            yield db_session
        finally:
            pass

    test_app.dependency_overrides[get_db] = override_get_db

    return TestClient(test_app)


@pytest.fixture
def test_user(db_session, test_db):
    """테스트용 사용자 생성 fixture"""
    from src.api.v1.models.user.user import User

    # 이미 사용자가 존재하는지 확인
    existing_user = db_session.query(User).filter(User.id == 1).first()
    if existing_user:
        return existing_user

    # 테스트 사용자 생성
    try:
        test_user = User(
            name="테스트사용자",
            email="test@example.com",
            bio="테스트 사용자입니다",
            status="active",
            auth_provider="local"
        )
        db_session.add(test_user)
        db_session.commit()
        db_session.refresh(test_user)
        return test_user
    except Exception as e:
        # 사용자 생성 실패시 None 반환
        db_session.rollback()
        return None


@pytest.fixture
def mock_project():
    """모의 프로젝트 데이터 fixture"""
    return {
        "id": 1,
        "title": "테스트 프로젝트",
        "description": "테스트용 프로젝트입니다",
        "max_participants": 5,
        "current_participants": 1,
        "status": "active",
        "created_by": 1,
        "created_at": "2024-01-01T00:00:00"
    }


@pytest.fixture
def mock_community():
    """모의 커뮤니티 데이터 fixture"""
    return {
        "id": 1,
        "name": "테스트 커뮤니티",
        "description": "테스트용 커뮤니티입니다",
        "category": "technology",
        "is_private": False,
        "max_members": 100,
        "current_members": 1,
        "created_by": 1,
        "created_at": "2024-01-01T00:00:00"
    }


@pytest.fixture
def mock_mentor():
    """모의 멘토 데이터 fixture"""
    return {
        "id": 1,
        "user_id": 1,
        "expertise_areas": ["Python", "FastAPI"],
        "experience_years": 5,
        "introduction": "테스트 멘토입니다",
        "session_price": 50000,
        "rating": 4.5,
        "is_active": True,
        "created_at": "2024-01-01T00:00:00"
    }


@pytest.fixture
def mock_session_data():
    """모의 세션 데이터 fixture"""
    return {
        "id": 1,
        "mentor_id": 1,
        "mentee_id": 2,
        "scheduled_at": "2024-12-20T14:00:00",
        "duration_minutes": 60,
        "status": "scheduled",
        "topic": "FastAPI 프로젝트 리뷰",
        "created_at": "2024-01-01T00:00:00"
    }


@pytest.fixture
def auth_headers():
    """인증 헤더 fixture"""
    return {"Authorization": "Bearer test_token"}


@pytest.fixture
def mock_jwt_token():
    """모의 JWT 토큰 fixture"""
    return "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.test_token"


# 환경 변수 설정 fixture
@pytest.fixture(autouse=True)
def set_test_env():
    """테스트 환경 변수 설정"""
    os.environ["TESTING"] = "true"
    os.environ["DATABASE_URL"] = TEST_DATABASE_URL
    os.environ["POSTGRES_URL"] = TEST_DATABASE_URL  # 테스트용 SQLite 데이터베이스
    os.environ["SECRET_KEY"] = "test-secret-key-for-jwt-tokens"
    os.environ["GITHUB_CLIENT_ID"] = "test-github-client-id"
    os.environ["GITHUB_CLIENT_SECRET"] = "test-github-client-secret"
    os.environ["GOOGLE_CLIENT_ID"] = "test-google-client-id"
    os.environ["GOOGLE_CLIENT_SECRET"] = "test-google-client-secret"
    os.environ["GOOGLE_REDIRECT_URI"] = "http://localhost:8000/auth/google/callback"
    yield
    # 테스트 후 환경 변수 정리
    if "TESTING" in os.environ:
        del os.environ["TESTING"]
    if "DATABASE_URL" in os.environ:
        del os.environ["DATABASE_URL"]
    if "POSTGRES_URL" in os.environ:
        del os.environ["POSTGRES_URL"]
    if "SECRET_KEY" in os.environ:
        del os.environ["SECRET_KEY"]
    if "GITHUB_CLIENT_ID" in os.environ:
        del os.environ["GITHUB_CLIENT_ID"]
    if "GITHUB_CLIENT_SECRET" in os.environ:
        del os.environ["GITHUB_CLIENT_SECRET"]
    if "GOOGLE_CLIENT_ID" in os.environ:
        del os.environ["GOOGLE_CLIENT_ID"]
    if "GOOGLE_CLIENT_SECRET" in os.environ:
        del os.environ["GOOGLE_CLIENT_SECRET"]
    if "GOOGLE_REDIRECT_URI" in os.environ:
        del os.environ["GOOGLE_REDIRECT_URI"]


# 테스트 데이터 정리 fixture
@pytest.fixture(autouse=True)
def cleanup():
    """테스트 후 정리"""
    yield
    # 각 테스트 후 실행할 정리 작업들
    pass


# 비동기 테스트 지원을 위한 이벤트 루프 fixture
@pytest.fixture(scope="session")
def event_loop():
    """이벤트 루프 fixture"""
    import asyncio
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


# 파일 업로드 테스트용 임시 파일 fixture
@pytest.fixture
def temp_file():
    """임시 파일 fixture"""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
        f.write("테스트 파일 내용입니다")
        temp_file_path = f.name

    yield temp_file_path

    # 테스트 후 파일 정리
    if os.path.exists(temp_file_path):
        os.unlink(temp_file_path)


# API 응답 검증 헬퍼 함수들
def assert_success_response(response, expected_status: int = 200):
    """성공 응답 검증 헬퍼"""
    assert response.status_code == expected_status
    assert "detail" not in response.json() or response.json().get("detail") != "Not found"


def assert_error_response(response, expected_status: int, expected_detail: str = None):
    """에러 응답 검증 헬퍼"""
    assert response.status_code == expected_status
    if expected_detail:
        assert response.json().get("detail") == expected_detail


# 데이터베이스 의존성 오버라이드 헬퍼
def override_get_db():
    """데이터베이스 의존성 오버라이드 헬퍼"""
    try:
        db = TestSessionLocal()
        yield db
    finally:
        db.close()


# 모의 객체 생성 헬퍼 함수들
def create_mock_user_service():
    """모의 사용자 서비스 생성"""
    mock_service = Mock()
    mock_service.get_user.return_value = {
        "id": 1,
        "email": "test@example.com",
        "nickname": "테스트사용자"
    }
    return mock_service


def create_mock_project_service():
    """모의 프로젝트 서비스 생성"""
    mock_service = Mock()
    mock_service.get_project.return_value = {
        "id": 1,
        "title": "테스트 프로젝트",
        "description": "테스트용 프로젝트입니다"
    }
    return mock_service


def create_mock_community_service():
    """모의 커뮤니티 서비스 생성"""
    mock_service = Mock()
    mock_service.get_community.return_value = {
        "id": 1,
        "name": "테스트 커뮤니티",
        "description": "테스트용 커뮤니티입니다"
    }
    return mock_service


def create_mock_mentoring_service():
    """모의 멘토링 서비스 생성"""
    mock_service = Mock()
    mock_service.get_mentor.return_value = {
        "id": 1,
        "expertise_areas": ["Python", "FastAPI"],
        "session_price": 50000
    }
    return mock_service
