# Team-Up Server

팀 프로젝트 관리를 위한 백엔드 서버입니다.

## 목차
- [설치](#설치)
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

## 개발 환경

개발 환경에서 서버를 실행하는 방법:

```bash
# Uvicorn을 사용한 직접 실행 (자동 리로드)
uvicorn main:app --reload --host 0.0.0.0 --port 8000

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