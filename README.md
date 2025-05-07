# Team-Up Server

## 설치 방법

필요한 패키지를 설치합니다:

```bash
pip install -r requirements.txt
```

## 개발 환경에서 실행하기

다음 명령어로 개발 서버를 실행할 수 있습니다:

```bash
# Uvicorn을 사용한 직접 실행
uvicorn main:app --reload --host 0.0.0.0 --port 8000

# 또는 wsgi.py 사용
python wsgi.py
```

## 프로덕션 환경에서 실행하기

Gunicorn을 사용하여 WSGI 방식으로 실행합니다:

```bash
gunicorn -c gunicorn_config.py wsgi:application
```

## 서버 접속 정보

- API 문서: http://서버주소:8000/docs
- 대체 API 문서: http://서버주소:8000/redoc

## 외부 접속 설정

### 1. 방화벽 설정
- 사용 중인 포트(기본: 8000)를 외부에서 접근 가능하도록 설정해야 합니다.

### 2. 프록시 서버 사용 (권장)
- Nginx와 같은 웹 서버를 프록시로 사용하여 보안 및 성능을 향상시킬 수 있습니다.

### Nginx 설정 예시

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

## 기술 스택

- FastAPI: 고성능 웹 프레임워크
- Uvicorn/Gunicorn: ASGI/WSGI 서버
- SQLAlchemy: ORM (객체 관계형 매핑)
- Pydantic: 데이터 유효성 검사 및 설정 관리

## 프로젝트 구조

```
team-up-server/
├── app/            # 애플리케이션 코드
├── config/         # 설정 파일
├── migrations/     # 데이터베이스 마이그레이션
├── tests/          # 테스트 코드
├── main.py         # 애플리케이션 진입점
├── wsgi.py         # WSGI 애플리케이션
├── gunicorn_config.py  # Gunicorn 설정
└── requirements.txt    # 의존성 패키지 목록
``` 