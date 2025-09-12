import httpx
import os
import logging
from fastapi import HTTPException
from dotenv import load_dotenv
import requests

load_dotenv()

GITHUB_CLIENT_ID = os.getenv("GITHUB_CLIENT_ID")
GITHUB_CLIENT_SECRET = os.getenv("GITHUB_CLIENT_SECRET")
JWT_SECRET = os.getenv("SECRET_KEY")

async def get_github_access_token(code: str) -> str:
  if not all([GITHUB_CLIENT_ID, GITHUB_CLIENT_SECRET, code]):
    error_msg = "Missing required GitHub OAuth configuration"
    logging.error(error_msg)
    raise HTTPException(status_code=500, detail=error_msg)
    
  try:
    async with httpx.AsyncClient() as client:
      token_res = await client.post(
        "https://github.com/login/oauth/access_token",
        headers={
          "Accept": "application/json",
          "Content-Type": "application/x-www-form-urlencoded"
        },
        data={
          "client_id": GITHUB_CLIENT_ID,
          "client_secret": GITHUB_CLIENT_SECRET,
          "code": code,
        },
        timeout=10.0
      )
        
      token_res.raise_for_status()
      token_data = token_res.json()
        
      if "error" in token_data:
        error_msg = f"GitHub OAuth error: {token_data.get('error_description', token_data['error'])}"
        logging.error(error_msg)
        raise HTTPException(status_code=400, detail=error_msg)
            
      if "access_token" not in token_data:
        error_msg = "No access token in GitHub response"
        logging.error(f"{error_msg}: {token_data}")
        raise HTTPException(status_code=400, detail=error_msg)
            
      return token_data["access_token"]
            
  except httpx.HTTPStatusError as e:
    error_msg = f"GitHub OAuth error: {e.response.status_code} - {e.response.text}"
    logging.error(error_msg)
    raise HTTPException(status_code=400, detail=error_msg)
  except httpx.RequestError as e:
    error_msg = f"Failed to connect to GitHub OAuth service: {str(e)}"
    logging.error(error_msg)
    raise HTTPException(status_code=503, detail=error_msg)
  except Exception as e:
    error_msg = f"Unexpected error in get_github_access_token: {str(e)}"
    logging.error(error_msg)
    raise HTTPException(status_code=500, detail=error_msg)

async def get_github_user_info(code: str) -> tuple:
  try:
    access_token = await get_github_access_token(code)
    if not access_token:
      raise ValueError("Failed to obtain access token from GitHub")
    
    async with httpx.AsyncClient() as client:
      # Get user info
      user_res = await client.get(
        "https://api.github.com/user",
        headers={
          "Authorization": f"Bearer {access_token}",
          "Accept": "application/vnd.github+json"
        },
        timeout=10.0
      )
      user_res.raise_for_status()
      user_data = user_res.json()
        
      if not user_data.get("email"):
        # If email is not in the initial response, fetch it from the emails endpoint
        emails_res = await client.get(
          "https://api.github.com/user/emails",
          headers={
            "Authorization": f"Bearer {access_token}",
            "Accept": "application/vnd.github+json"
          },
          timeout=10.0
        )
        emails_res.raise_for_status()
        emails = emails_res.json()
            
        if emails and isinstance(emails, list):
          primary_email = next(
            (email["email"] for email in emails 
              if isinstance(email, dict) and email.get("primary") and email.get("verified")),
            None
          )
          if not primary_email and emails:
            primary_email = emails[0].get("email") if isinstance(emails[0], dict) else None
                
          if primary_email:
            user_data["email"] = primary_email
            
          if not user_data.get("email"):
            raise ValueError("No verified email found in GitHub account")
        
        github_username = user_data.get("login")
        if not github_username:
          raise ValueError("GitHub username not found in response")
            
        return access_token, user_data, github_username
          
  except httpx.HTTPStatusError as e:
    error_msg = f"GitHub API error: {e.response.status_code} - {e.response.text}"
    logging.error(error_msg)
    raise HTTPException(status_code=400, detail=error_msg)
  except httpx.RequestError as e:
    error_msg = f"Failed to connect to GitHub API: {str(e)}"
    logging.error(error_msg)
    raise HTTPException(status_code=503, detail=error_msg)
  except Exception as e:
    error_msg = f"Unexpected error in get_github_user_info: {str(e)}"
    logging.error(error_msg)
    raise HTTPException(status_code=500, detail=error_msg)
      
async def get_google_access_token(code: str) -> str:
  try:
    url = "https://www.googleapis.com/oauth2/v3/token"
    payload={
      'code': code,
      'client_id': os.getenv('GOOGLE_CLIENT_ID'),
      'client_secret': os.getenv('GOOGLE_CLIENT_SECRET'),
      'redirect_uri': os.getenv('GOOGLE_REDIRECT_URI'),
      'grant_type': 'authorization_code'
    }
    headers = {}
    response = requests.request("POST", url, headers=headers, data=payload)
    return response.json()['access_token']
  except Exception as e:
    error_msg = f"Unexpected error in get_google_access_token: {str(e)}"
    logging.error(error_msg)
    raise HTTPException(status_code=500, detail=error_msg)
      
async def get_google_user_info(code: str) -> tuple:
  try:
    access_token = await get_google_access_token(code)
    if not access_token:
      raise ValueError("Failed to obtain access token from Google")
      
    url = "https://www.googleapis.com/oauth2/v3/userinfo"
    headers = {'Authorization': f'Bearer {access_token}'}
    response = requests.request("GET", url, headers=headers)
      
    return access_token, response.json()
    
    
        
  except Exception as e:
    error_msg = f"Unexpected error in get_google_user_info: {str(e)}"
    logging.error(error_msg)
    raise HTTPException(status_code=500, detail=error_msg)