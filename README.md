# Team-Up Server

팀 프로젝트 관리를 위한 백엔드 서버입니다.

## 목차
- [설치](#설치)
- [환경 변수 설정](#환경-변수-설정)
- [Supabase 설정](#supabase-설정)
- [개발 환경](#개발-환경)
- [프로덕션 환경](#프로덕션-환경)
- [API 문서](#api-문서)
- [외부 접속 설정](#외부-접속-설정)

## 설치

### 요구사항
- Python 3.8 이상
- pip

### 패키지 설치

```bash
pip install -r requirements.txt
```

## 환경 변수 설정

프로젝트 루트에 `.env` 파일을 생성하고 다음과 같이 설정합니다:

```
SECRET_KEY=your_secure_random_string_here
ACCESS_TOKEN_EXPIRE_MINUTES=30

# Supabase 설정
SUPABASE_URL=your_supabase_url
SUPABASE_KEY=your_supabase_anon_key
SUPABASE_SERVICE_KEY=your_supabase_service_role_key
```

### SECRET_KEY 생성 방법

보안을 위해 안전한 랜덤 문자열을 SECRET_KEY로 사용해야 합니다. Python을 사용하여 안전한 키를 생성할 수 있습니다:

```bash
python -c "import secrets; print(secrets.token_hex(32))"
```

생성된 키를 복사하여 `.env` 파일의 SECRET_KEY 값으로 사용하세요.

## Supabase 설정

### Supabase란?

Supabase는 Firebase의 오픈 소스 대안으로, PostgreSQL 데이터베이스를 기반으로 하는 백엔드 서비스입니다. 인증, 실시간 구독, 스토리지 등 다양한 기능을 제공합니다.

### Supabase 프로젝트 생성 방법

1. [Supabase 웹사이트](https://supabase.com/)에서 계정을 생성합니다.
2. 새 프로젝트를 생성합니다.
3. 프로젝트가 준비되면 설정에서 프로젝트 URL과 API 키를 확인할 수 있습니다.

### 필요한 환경 변수

`.env` 파일에 다음 Supabase 관련 변수를 추가하세요:

- `SUPABASE_URL`: Supabase 프로젝트 URL (예: `https://xxxxxxxxxxxx.supabase.co`)
- `SUPABASE_KEY`: Anon 키 (공개 키)
- `SUPABASE_SERVICE_KEY`: Service Role 키 (비공개 키, 서버 측 작업용)
- `POSTGRES_URL`: Supabase의 PostgreSQL 데이터베이스 URL (예: `postgresql://<username>:<password>@<host>:<port>/<database>`)

### 데이터베이스 마이그레이션

기존 데이터를 Supabase로 마이그레이션하려면:

```bash
# SQL 덤프 파일 생성 (기존 DB에서)
pg_dump -U username -d database_name > dump.sql

# SQL 파일 편집 (필요한 경우)
# Supabase SQL 편집기에서 실행하거나 아래 명령어로 복원
psql -h database.supabase.co -U postgres -d postgres -f dump.sql
```

### Supabase 클라이언트 사용 예시

```python
from supabase import create_client, Client
import os
from dotenv import load_dotenv

load_dotenv()

supabase: Client = create_client(
    os.environ.get("SUPABASE_URL"),
    os.environ.get("SUPABASE_KEY")
)

# 데이터 조회 예시
response = supabase.table('projects').select('*').execute()
projects = response.data
```

## 개발 환경

개발 환경에서 서버를 실행하는 방법:

```bash
# 데이터베이스 마이그레이션 (새로운 채널/채팅 기능 사용 시)
python new_scripts/migrate_channel_chat.py

# Uvicorn을 사용한 직접 실행 (자동 리로드)
uvicorn new_main:app --reload --host 0.0.0.0 --port 8000

# 또는 wsgi.py 사용
python wsgi.py
```

## 프로덕션 환경

프로덕션 환경에서 서버를 실행하는 방법:

```bash
# Gunicorn을 사용하여 WSGI 방식으로 실행
gunicorn -c gunicorn_config.py wsgi:application
```

## API 문서

서버 실행 후 다음 URL에서 API 문서를 확인할 수 있습니다:

- Swagger UI: `http://서버주소:8000/docs`
- ReDoc: `http://서버주소:8000/redoc`

### 주요 API 엔드포인트

#### 채널 관리
- `POST /channels/` - 새 채널 생성
- `GET /channels/{channel_id}` - 채널 정보 조회
- `GET /channels/{channel_id}/with-members` - 채널 정보와 멤버 목록 조회
- `GET /channels/project/{project_id}` - 프로젝트의 채널 목록 조회
- `GET /channels/user/{user_id}` - 사용자가 참여 중인 채널 목록 조회
- `PUT /channels/{channel_id}` - 채널 정보 업데이트
- `POST /channels/{channel_id}/members` - 채널에 멤버 추가
- `DELETE /channels/{channel_id}/members/{user_id}` - 채널에서 멤버 제거
- `GET /channels/{channel_id}/members` - 채널의 멤버 목록 조회
- `DELETE /channels/{channel_id}` - 채널 삭제

#### 채팅 관리
- `POST /chats/` - 새 채팅 메시지 생성
- `GET /chats/{chat_id}` - 채팅 메시지 조회
- `GET /chats/channel/{channel_id}` - 채널의 채팅 메시지 조회
- `GET /chats/project/{project_id}` - 프로젝트의 모든 채팅 메시지 조회
- `GET /chats/user/{user_id}` - 사용자가 작성한 채팅 메시지 조회
- `POST /chats/channel/{channel_id}/search` - 채널에서 메시지 검색
- `POST /chats/channel/{channel_id}/date-range` - 특정 기간의 채팅 메시지 조회
- `PUT /chats/{chat_id}` - 채팅 메시지 수정
- `DELETE /chats/{chat_id}` - 채팅 메시지 삭제

## 외부 접속 설정

### 방화벽 설정
- 사용 중인 포트(기본: 8000)를 외부에서 접근 가능하도록 설정

### 프록시 서버 설정 (권장)
보안 및 성능 향상을 위해 Nginx와 같은 웹 서버를 프록시로 사용하는 것을 권장합니다.

#### Nginx 설정 예시

```nginx
server {
    listen 80;
    server_name your_domain.com;

    location / {
        proxy_pass http://localhost:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

## 기여 방법

1. 이 저장소를 포크합니다
2. 새 기능 브랜치를 생성합니다 (`git checkout -b feature/amazing-feature`)
3. 변경사항을 커밋합니다 (`git commit -m 'Add some amazing feature'`)
4. 브랜치에 푸시합니다 (`git push origin feature/amazing-feature`)
5. Pull Request를 생성합니다 

## 📄 라이선스

[MIT License](./LICENSE)