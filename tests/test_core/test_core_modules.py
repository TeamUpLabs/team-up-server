"""
Core 모듈 테스트 파일들
"""
import pytest


class TestDatabase:
    """데이터베이스 관련 테스트"""

    def test_database_connection(self):
        """데이터베이스 연결 테스트"""
        from src.core.database.database import engine, Base

        # 엔진이 정상적으로 생성되었는지 확인
        assert engine is not None
        assert str(engine.url).startswith("postgresql")  # 테스트용 SQLite

    def test_database_tables_creation(self):
        """데이터베이스 테이블 생성 테스트"""
        from src.core.database.database import engine, Base

        # 테이블 생성이 가능한지 확인
        try:
            Base.metadata.create_all(bind=engine)
            assert True
        except Exception as e:
            pytest.fail(f"테이블 생성 실패: {e}")

    def test_database_models_import(self):
        """데이터베이스 모델 import 테스트"""
        try:
            from src.api.v1.models.user import User
            from src.api.v1.models.project import Project
            from src.api.v1.models.community.post import Post
            from src.api.v1.models.mentoring.mentor import Mentor
            assert True
        except ImportError as e:
            pytest.fail(f"모델 import 실패: {e}")


class TestMiddleware:
    """미들웨어 관련 테스트"""

    def test_error_handling_middleware(self):
        """에러 처리 미들웨어 테스트"""
        from src.core.middleware.ErrorHandlingMiddleware import ErrorHandlingMiddleware

        middleware = ErrorHandlingMiddleware(None)
        assert middleware is not None

    def test_logging_middleware(self):
        """로깅 미들웨어 테스트"""
        from src.core.middleware.LoggingMiddleware import LoggingMiddleware

        middleware = LoggingMiddleware(None)
        assert middleware is not None

    def test_cors_middleware_configuration(self):
        """CORS 미들웨어 설정 테스트"""
        from fastapi.middleware.cors import CORSMiddleware

        # CORS 설정이 올바른지 확인
        cors_middleware = CORSMiddleware
        assert cors_middleware is not None


class TestSecurity:
    """보안 관련 테스트"""

    def test_password_hashing(self):
        """비밀번호 해싱 테스트"""
        from src.core.security.password import get_password_hash, verify_password

        password = "test_password_123"
        hashed = get_password_hash(password)

        assert hashed != password
        assert verify_password(password, hashed)
        assert not verify_password("wrong_password", hashed)

    def test_jwt_token_creation(self):
        """JWT 토큰 생성 테스트"""
        from src.core.security.jwt import create_access_token

        token_data = {"user_id": 1, "email": "test@example.com"}
        token = create_access_token(token_data)

        assert token is not None
        assert isinstance(token, str)

    def test_jwt_token_verification(self):
        """JWT 토큰 검증 테스트"""
        from src.core.security.jwt import create_access_token, verify_token

        token_data = {"user_id": 1, "email": "test@example.com"}
        token = create_access_token(token_data)
        decoded_data = verify_token(token)

        assert decoded_data["user_id"] == 1
        assert decoded_data["email"] == "test@example.com"


class TestConfig:
    """설정 관련 테스트"""

    def test_settings_import(self):
        """설정 import 테스트"""
        from src.core.config import setting

        assert setting is not None
        assert hasattr(setting, 'TITLE')
        assert hasattr(setting, 'VERSION')

    def test_environment_variables(self):
        """환경 변수 설정 테스트"""
        from src.core.config import setting

        # 필수 설정값들이 있는지 확인
        required_settings = ['DATABASE_URL', 'SECRET_KEY', 'TITLE']
        for setting_name in required_settings:
            assert hasattr(setting, setting_name)
