#!/usr/bin/env python3
"""
Test script for OAuth user creation
"""

import requests
import json

# Test data based on the provided structure
test_user_data = {
    "auth_provider": "github",
    "auth_provider_access_token": "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",
    "auth_provider_id": "lee-seokmin",
    "bio": "Freelancer Full Stack Developer @TeamUpLabs ",
    "birth_date": "2025-07-16",
    "collaboration_preference": {
        "available_time_zone": "Asia/Seoul",
        "collaboration_style": "active",
        "preferred_project_length": "medium",
        "preferred_project_type": "web",
        "preferred_role": "fullstack_developer",
        "work_hours_end": 1800,
        "work_hours_start": 900
    },
    "email": "dltjrals13@naver.com",
    "interests": [
        {"interest_category": "Technology", "interest_name": "AI/ML"},
        {"interest_category": "Technology", "interest_name": "IoT"},
        {"interest_category": "Business", "interest_name": "Finance"}
    ],
    "languages": ["한국어"],
    "last_login": "",
    "name": "이석민",
    "phone": "010-6683-2802",
    "profile_image": "https://avatars.githubusercontent.com/u/68291436?v=4",
    "role": "developer",
    "social_links": [
        {"platform": "github", "url": "https://github.com/lee-seokmin"}
    ],
    "status": "inactive",
    "tech_stacks": [
        {"tech": "Next.js", "level": 1}
    ]
}

def test_oauth_login():
    """Test OAuth login endpoint"""
    url = "http://localhost:8000/api/users/oauth"
    
    try:
        response = requests.post(url, json=test_user_data)
        print(f"Status Code: {response.status_code}")
        print(f"Response: {json.dumps(response.json(), indent=2, ensure_ascii=False)}")
        
        if response.status_code == 200:
            print("✅ OAuth login successful!")
            return response.json()
        else:
            print("❌ OAuth login failed!")
            return None
            
    except requests.exceptions.RequestException as e:
        print(f"❌ Request failed: {e}")
        return None

def test_regular_user_creation():
    """Test regular user creation endpoint"""
    url = "http://localhost:8000/api/users/"
    
    regular_user_data = {
        "email": "test@example.com",
        "name": "Test User",
        "password": "testpassword123",
        "role": "developer",
        "bio": "Test user for development"
    }
    
    try:
        response = requests.post(url, json=regular_user_data)
        print(f"Status Code: {response.status_code}")
        print(f"Response: {json.dumps(response.json(), indent=2, ensure_ascii=False)}")
        
        if response.status_code == 201:
            print("✅ Regular user creation successful!")
            return response.json()
        else:
            print("❌ Regular user creation failed!")
            return None
            
    except requests.exceptions.RequestException as e:
        print(f"❌ Request failed: {e}")
        return None

if __name__ == "__main__":
    print("Testing OAuth User Creation...")
    print("=" * 50)
    
    # Test OAuth login
    oauth_result = test_oauth_login()
    
    print("\n" + "=" * 50)
    print("Testing Regular User Creation...")
    print("=" * 50)
    
    # Test regular user creation
    regular_result = test_regular_user_creation()
    
    print("\n" + "=" * 50)
    print("Test Summary:")
    print(f"OAuth Login: {'✅ Success' if oauth_result else '❌ Failed'}")
    print(f"Regular User Creation: {'✅ Success' if regular_result else '❌ Failed'}") 