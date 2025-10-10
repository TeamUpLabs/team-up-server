# 🚀 TeamUp API

<div align="center">
  <h3>팀 프로젝트 협업과 멘토링을 위한 플랫폼</h3>
  <p><strong>FastAPI 기반의 현대적인 REST API 서비스</strong></p>

  ![Render Deploy](https://deploy-badge.vercel.app/?url=https%3A%2F%2Fteam-up-server.onrender.com%2F&logo=Render&name=Render)
  [![Python Version](https://img.shields.io/badge/python-3.8+-blue.svg)](https://python.org)
  [![FastAPI](https://img.shields.io/badge/FastAPI-0.115.12-green.svg)](https://fastapi.tiangolo.com)
  [![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](/LICENSE)
</div>

---

## 📋 목차

- [✨ 주요 기능](#-주요-기능)
- [🏗️ 프로젝트 구조](#️-프로젝트-구조)
- [🛠️ 기술 스택](#️-기술-스택)
- [🚀 빠른 시작](#-빠른-시작)
- [📚 API 문서](#-api-문서)
- [🔧 환경 설정](#-환경-설정)
- [🧪 테스트](#-테스트)
- [📖 사용 예시](#-사용-예시)
- [🤝 기여하기](#-기여하기)
- [📄 라이선스](#-라이선스)

## ✨ 주요 기능

### 👥 사용자 관리
- **🔐 인증 시스템**: JWT 토큰 기반 인증
- **🌐 소셜 로그인**: GitHub, Google OAuth 지원
- **👤 프로필 관리**: 사용자 정보, 기술스택, 관심분야 관리
- **📱 알림 설정**: 이메일, 푸시 알림 커스터마이징

### 📋 프로젝트 관리
- **🏗️ 프로젝트 생성 및 관리**: 다양한 프로젝트 타입 지원
- **👥 팀 멤버 관리**: 멤버 초대, 권한 설정
- **✅ 태스크 관리**: 칸반 보드 스타일 태스크 관리
- **🎯 마일스톤 설정**: 프로젝트 진행 상황 추적
- **📅 일정 관리**: 공유 캘린더 및 데드라인 관리

### 🌍 커뮤니티 기능
- **👥 팔로우 시스템**: 관심 사용자 팔로우
- **📝 게시물 및 댓글**: 지식 공유 및 토론
- **❤️ 좋아요 및 북마크**: 유용한 콘텐츠 저장
- **🔍 검색 및 추천**: 관련 콘텐츠 추천

### 🎓 멘토링 시스템
- **🤝 멘토-멘티 매칭**: 기술 기반 매칭 알고리즘
- **📚 학습 계획 관리**: 개인별 학습 로드맵
- **💬 1:1 멘토링 세션**: 실시간 화상/채팅 멘토링
- **📊 진행 상황 추적**: 멘토링 성과 측정

### 💬 실시간 커뮤니케이션
- **⚡ WebSocket 기반 채팅**: 실시간 메시징
- **📢 채널별 대화방**: 프로젝트별 커뮤니케이션
- **🔗 파일 공유**: 문서, 이미지 실시간 공유

### 🎨 협업 도구
- **📱 화이트보드**: 실시간 협업 드로잉
- **📎 파일 관리**: 프로젝트 문서 중앙화
- **🌍 위치 기반 매칭**: 지역별 협업자 찾기

## 🏗️ 프로젝트 구조

```
team-up-server/
├── 📁 src/
│   ├── 📁 api/v1/                 # API 버전 1
│   │   ├── 📁 models/             # 데이터베이스 모델
│   │   │   ├── 📁 user/           # 사용자 관련 모델
│   │   │   ├── 📁 project/        # 프로젝트 관련 모델
│   │   │   ├── 📁 community/      # 커뮤니티 관련 모델
│   │   │   └── 📁 mentoring/      # 멘토링 관련 모델
│   │   ├── 📁 routes/             # API 엔드포인트
│   │   ├── 📁 schemas/            # Pydantic 스키마
│   │   ├── 📁 services/           # 비즈니스 로직
│   │   └── 📁 repositories/       # 데이터 접근 계층
│   └── 📁 core/                   # 핵심 설정 및 유틸리티
│       ├── 📁 database/           # 데이터베이스 연결
│       ├── 📁 middleware/         # 커스텀 미들웨어
│       ├── 📁 security/           # 보안 관련 유틸리티
│       └── 📁 utils/              # 공통 유틸리티
├── 📁 .github/
│   └── 📁 ISSUE_TEMPLATE/         # GitHub 이슈 템플릿
├── 📄 main.py                     # 애플리케이션 진입점
├── 📄 requirements.txt            # Python 의존성
├── 📄 .env                        # 환경 변수 (예시)
└── 📄 README.md                   # 프로젝트 문서
```

## 🛠️ 기술 스택

### 백엔드
- **⚡ FastAPI** - 고성능 비동기 웹 프레임워크
- **🐍 Python 3.8+** - 현대적인 Python 버전 지원

### 데이터베이스
- **🐘 PostgreSQL** - 안정적인 관계형 데이터베이스
- **🔗 SQLAlchemy** - 강력한 ORM 도구
- **📦 Supabase** - 백엔드 서비스 (DB, 인증, 실시간)

### 캐싱 및 실시간
- **🔴 Redis** - 고성능 인메모리 데이터 저장소
- **⚡ WebSocket** - 실시간 양방향 통신

### 인증 및 보안
- **🔐 JWT** - stateless 토큰 인증
- **🔒 bcrypt** - 안전한 비밀번호 해싱
- **🛡️ OAuth** - 소셜 로그인 (GitHub, Google)

### 개발 도구
- **🧪 Pytest** - 강력한 테스트 프레임워크
- **🎨 Rich** - 아름다운 터미널 출력
- **📍 GeoIP2** - 위치 기반 서비스

### 배포
- **🚀 Uvicorn** - 고성능 ASGI 서버
- **🐎 Gunicorn** - WSGI HTTP 서버

## 🚀 빠른 시작

### 1️⃣ 사전 요구사항

```bash
# Python 3.8 이상이 설치되어 있어야 합니다
python --version

# Git이 설치되어 있어야 합니다
git --version
```

### 2️⃣ 프로젝트 클론

```bash
git clone https://github.com/your-username/team-up-server.git
cd team-up-server
```

### 3️⃣ 가상환경 설정

```bash
# 가상환경 생성 및 활성화
python -m venv .venv
source .venv/bin/activate  # macOS/Linux
# 또는
.venv\Scripts\activate     # Windows

# 의존성 설치
pip install -r requirements.txt
```

### 4️⃣ 환경 변수 설정

`.env` 파일을 생성하고 다음 내용을 추가하세요:

```env
# 데이터베이스 설정
POSTGRES_URL=postgresql://username:password@localhost:5432/teamup
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_KEY=your-supabase-anon-key

# JWT 설정
SECRET_KEY=your-secret-key-here
ACCESS_TOKEN_EXPIRE_MINUTES=30

# OAuth 설정 (선택사항)
GITHUB_CLIENT_ID=your-github-client-id
GITHUB_CLIENT_SECRET=your-github-client-secret
GOOGLE_CLIENT_ID=your-google-client-id
GOOGLE_CLIENT_SECRET=your-google-client-secret
```

### 5️⃣ 데이터베이스 초기화

```bash
# 데이터베이스 테이블 생성 (자동)
python main.py
```

### 6️⃣ 서버 실행

```bash
# 개발 모드 실행
uvicorn main:app --reload --host 0.0.0.0 --port 8000

# 또는 프로덕션 모드
gunicorn main:app -w 4 -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000
```

서버가 성공적으로 시작되면 `http://localhost:8000`에서 API 문서를 확인할 수 있습니다.

## 📚 API 문서

서버 실행 후 다음 URL에서 자동 생성된 API 문서를 확인하세요:

- **📖 Swagger UI**: http://localhost:8000/docs
- **🔍 ReDoc**: http://localhost:8000/redoc
- **🚀 OpenAPI 스펙**: http://localhost:8000/openapi.json

## 🔧 환경 설정

### 개발 환경

```bash
export DEBUG=True
export LOG_LEVEL=DEBUG
```

### 프로덕션 환경

```bash
export DEBUG=False
export LOG_LEVEL=INFO
export SECRET_KEY=your-production-secret-key
```

## 🧪 테스트

```bash
# 모든 테스트 실행
pytest

# 특정 테스트 파일 실행
pytest tests/test_user.py

# 커버리지 리포트 생성
pytest --cov=src --cov-report=html
```

## 📖 사용 예시

### 사용자 등록

```bash
curl -X POST "http://localhost:8000/api/v1/users/register" \
     -H "Content-Type: application/json" \
     -d '{
       "name": "홍길동",
       "email": "hong@example.com",
       "password": "securepassword"
     }'
```

### 프로젝트 생성

```bash
curl -X POST "http://localhost:8000/api/v1/projects" \
     -H "Content-Type: application/json" \
     -H "Authorization: Bearer YOUR_JWT_TOKEN" \
     -d '{
       "title": "새 프로젝트",
       "description": "프로젝트 설명",
       "team_size": 5,
       "project_type": "web"
     }'
```

### 실시간 채팅

```javascript
// WebSocket 연결
const ws = new WebSocket('ws://localhost:8000/api/v1/chat/ROOM_ID');

// 메시지 전송
ws.send(JSON.stringify({
  type: 'message',
  content: '안녕하세요!',
  user_id: 'user123'
}));
```

## 🤝 기여하기

프로젝트 발전에 관심이 있으시다면 언제든지 환영합니다! 🤗

### 기여 방법

1. **🍴 Fork** 프로젝트
2. **🌿 Feature 브랜치** 생성 (`git checkout -b feature/amazing-feature`)
3. **💾 변경사항** 커밋 (`git commit -m 'Add amazing feature'`)
4. **📤 브랜치** 푸시 (`git push origin feature/amazing-feature`)
5. **🔄 Pull Request** 생성

### 개발 가이드라인

- 📝 **이슈 템플릿 사용**: 새로운 기능이나 버그 리포트 시 제공된 템플릿 사용
- 🧪 **테스트 작성**: 새로운 기능에는 반드시 테스트 코드 작성
- 📚 **문서 업데이트**: API 변경 시 문서 업데이트
- 🔍 **코드 리뷰**: 모든 변경사항은 코드 리뷰를 거침

## 📧 연락처

**👨‍💻 개발자**: 이석민 (Seokmin Lee)
- 📧 Email: dltjrals13@naver.com
- 🐙 GitHub: [seokmin](https://github.com/lee-seokmin)

## 📄 라이선스

이 프로젝트는 **MIT 라이선스**를 따릅니다. 자세한 내용은 [LICENSE](LICENSE) 파일을 참조하세요.

---

<div align="center">
  <p><strong>Built with ❤️ by 이석민</strong></p>
  <p>
    <a href="#-주요-기능">기능 살펴보기</a> •
    <a href="#-빠른-시작">시작하기</a> •
    <a href="#-기술-스택">기술 스택</a> •
    <a href="#-기여하기">기여하기</a>
  </p>
</div>