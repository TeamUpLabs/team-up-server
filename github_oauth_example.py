#!/usr/bin/env python3
"""
GitHub OAuth Integration Example
This shows how to integrate GitHub OAuth with the user creation system
"""

import requests
import json
from typing import Optional, Dict, Any

class GitHubOAuth:
    def __init__(self, client_id: str, client_secret: str, redirect_uri: str):
        self.client_id = client_id
        self.client_secret = client_secret
        self.redirect_uri = redirect_uri
        self.api_base_url = "https://api.github.com"
        self.auth_base_url = "https://github.com"
    
    def get_authorization_url(self, state: Optional[str] = None) -> str:
        """Generate GitHub OAuth authorization URL"""
        params = {
            "client_id": self.client_id,
            "redirect_uri": self.redirect_uri,
            "scope": "user:email",
            "response_type": "code"
        }
        if state:
            params["state"] = state
            
        query_string = "&".join([f"{k}={v}" for k, v in params.items()])
        return f"{self.auth_base_url}/login/oauth/authorize?{query_string}"
    
    def exchange_code_for_token(self, code: str) -> Optional[str]:
        """Exchange authorization code for access token"""
        url = f"{self.auth_base_url}/login/oauth/access_token"
        data = {
            "client_id": self.client_id,
            "client_secret": self.client_secret,
            "code": code,
            "redirect_uri": self.redirect_uri
        }
        headers = {"Accept": "application/json"}
        
        try:
            response = requests.post(url, data=data, headers=headers)
            response.raise_for_status()
            result = response.json()
            return result.get("access_token")
        except requests.exceptions.RequestException as e:
            print(f"Error exchanging code for token: {e}")
            return None
    
    def get_user_info(self, access_token: str) -> Optional[Dict[str, Any]]:
        """Get user information from GitHub"""
        url = f"{self.api_base_url}/user"
        headers = {
            "Authorization": f"token {access_token}",
            "Accept": "application/vnd.github.v3+json"
        }
        
        try:
            response = requests.get(url, headers=headers)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"Error getting user info: {e}")
            return None
    
    def get_user_emails(self, access_token: str) -> list:
        """Get user emails from GitHub"""
        url = f"{self.api_base_url}/user/emails"
        headers = {
            "Authorization": f"token {access_token}",
            "Accept": "application/vnd.github.v3+json"
        }
        
        try:
            response = requests.get(url, headers=headers)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"Error getting user emails: {e}")
            return []

def create_user_from_github_data(github_user: Dict[str, Any], access_token: str) -> Dict[str, Any]:
    """Convert GitHub user data to our user format"""
    
    # Get primary email
    emails = github_user.get("emails", [])
    primary_email = None
    for email in emails:
        if email.get("primary") and email.get("verified"):
            primary_email = email.get("email")
            break
    
    if not primary_email:
        # Fallback to the first verified email
        for email in emails:
            if email.get("verified"):
                primary_email = email.get("email")
                break
    
    # If still no email, use the one from github_user (might not be verified)
    if not primary_email:
        primary_email = github_user.get("email")
    
    user_data = {
        "auth_provider": "github",
        "auth_provider_id": str(github_user.get("id")),
        "auth_provider_access_token": access_token,
        "email": primary_email,
        "name": github_user.get("name") or github_user.get("login"),
        "profile_image": github_user.get("avatar_url"),
        "bio": github_user.get("bio"),
        "role": "developer",  # Default role
        "status": "active",
        "languages": ["한국어"],  # Default language
        "social_links": [
            {
                "platform": "github",
                "url": github_user.get("html_url")
            }
        ]
    }
    
    return user_data

def login_with_github(api_base_url: str, user_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """Login with GitHub user data to our API"""
    url = f"{api_base_url}/api/users/oauth"
    
    try:
        response = requests.post(url, json=user_data)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Error logging in with GitHub: {e}")
        return None

# Example usage
def example_github_oauth_flow():
    """Example of complete GitHub OAuth flow"""
    
    # Configuration (replace with your actual values)
    GITHUB_CLIENT_ID = "your_github_client_id"
    GITHUB_CLIENT_SECRET = "your_github_client_secret"
    REDIRECT_URI = "http://localhost:3000/auth/github/callback"
    API_BASE_URL = "http://localhost:8000"
    
    # Initialize GitHub OAuth
    github_oauth = GitHubOAuth(GITHUB_CLIENT_ID, GITHUB_CLIENT_SECRET, REDIRECT_URI)
    
    # Step 1: Generate authorization URL
    auth_url = github_oauth.get_authorization_url(state="random_state_string")
    print(f"Authorization URL: {auth_url}")
    print("User should visit this URL to authorize the application")
    
    # Step 2: After user authorizes, you'll receive a code
    # This is typically handled in your frontend callback
    code = "received_authorization_code"  # This comes from the callback
    
    # Step 3: Exchange code for access token
    access_token = github_oauth.exchange_code_for_token(code)
    if not access_token:
        print("Failed to get access token")
        return
    
    # Step 4: Get user information from GitHub
    github_user = github_oauth.get_user_info(access_token)
    if not github_user:
        print("Failed to get user info from GitHub")
        return
    
    # Step 5: Convert GitHub data to our format
    user_data = create_user_from_github_data(github_user, access_token)
    
    # Step 6: Login/Create user in our system
    result = login_with_github(API_BASE_URL, user_data)
    if result:
        print("✅ Successfully logged in with GitHub!")
        print(f"Access Token: {result.get('access_token')}")
        print(f"User: {result.get('user')}")
    else:
        print("❌ Failed to login with GitHub")

if __name__ == "__main__":
    print("GitHub OAuth Integration Example")
    print("=" * 50)
    print("This is an example of how to integrate GitHub OAuth with your user system.")
    print("You'll need to:")
    print("1. Register your application with GitHub")
    print("2. Get your client ID and client secret")
    print("3. Set up your redirect URI")
    print("4. Implement the OAuth flow in your frontend")
    print("=" * 50)
    
    # Uncomment the line below to run the example
    # example_github_oauth_flow() 