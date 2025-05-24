import redis
import os
from dotenv import load_dotenv

load_dotenv()

try:
    redis_client = redis.Redis(
        host=os.getenv("REDIS_HOST"),
        port=os.getenv("REDIS_PORT"),
        password=os.getenv("REDIS_PASSWORD"),
        decode_responses=True
    )
    redis_client.ping()
    print("✅ Redis 연결 성공!")
except Exception as e:
    print("❌ Redis 연결 실패:", e)