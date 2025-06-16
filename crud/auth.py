import httpx
import os
from dotenv import load_dotenv

load_dotenv()

GITHUB_CLIENT_ID = os.getenv("GITHUB_CLIENT_ID")
GITHUB_CLIENT_SECRET = os.getenv("GITHUB_CLIENT_SECRET")
JWT_SECRET = os.getenv("SECRET_KEY")

async def get_github_access_token(code: str) -> str:
    async with httpx.AsyncClient() as client:
        token_res = await client.post(
            "https://github.com/login/oauth/access_token",
            headers={"Accept": "application/json"},
            data={
                "client_id": GITHUB_CLIENT_ID,
                "client_secret": GITHUB_CLIENT_SECRET,
                "code": code,
            },
        )
        token_res.raise_for_status()
        token_data = token_res.json()
        return token_data["access_token"]

async def get_github_user_info(code: str) -> dict:
    # 1. GitHub에 code를 보내서 access token을 받아옴
    access_token = await get_github_access_token(code)
    
    async with httpx.AsyncClient() as client:
        # 2. access token으로 유저 정보 요청
        user_res = await client.get(
            "https://api.github.com/user",
            headers={"Authorization": f"Bearer {access_token}"}
        )
        user_res.raise_for_status()
        user_data = user_res.json()
        
        if not user_data.get("email"):
            emails_res = await client.get(
                "https://api.github.com/user/emails",
                headers={"Authorization": f"Bearer {access_token}"}
            )
            emails = emails_res.json()
            if emails:
                primary_email = next((email["email"] for email in emails if email["primary"]), None)
                if not primary_email:
                    primary_email = emails[0]["email"] # Fallback to the first email
                user_data["email"] = primary_email

        return user_data