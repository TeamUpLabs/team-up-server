# Team-Up Server

## 설치 방법

필요한 패키지를 설치합니다:

```bash
pip install -r requirements.txt
```

## 개발 환경에서 실행하기

```bash
# Uvicorn을 사용한 직접 실행
uvicorn main:app --reload --host 0.0.0.0 --port 8000

# 또는 wsgi.py 사용
python wsgi.py
```

## 프로덕션 환경에서 실행하기

Gunicorn을 사용하여 WSGI 방식으로 실행:

```bash
gunicorn -c gunicorn_config.py wsgi:application
```

## 서버 접속 정보

- API 문서: http://서버주소:8000/docs
- 대체 API 문서: http://서버주소:8000/redoc

## 외부 접속 설정

1. 방화벽 설정
   - 사용 중인 포트(기본: 8000)를 외부에서 접근 가능하도록 설정

2. 프록시 서버 사용 (권장)
   - Nginx와 같은 웹 서버를 프록시로 사용하여 보안 및 성능 향상

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