# OAuth Integration Documentation

## Overview

This document describes the OAuth integration that has been added to the user management system. The system now supports both traditional email/password authentication and OAuth-based authentication (currently GitHub, but extensible to other providers).

## Changes Made

### 1. Updated User Schema (`new_schemas/user.py`)

- **UserCreate**: Made password optional to support OAuth users who don't have passwords
- **Added OAuth fields**: `auth_provider`, `auth_provider_id`, `auth_provider_access_token`, `status`
- **Added OAuthLoginRequest**: New schema for OAuth login requests

### 2. Enhanced User CRUD (`new_crud/user.py`)

- **Updated create method**: Now handles OAuth users without passwords
- **Added authenticate_oauth**: Method for OAuth user authentication
- **Added get_or_create_oauth_user**: Method to handle OAuth user creation/retrieval

### 3. New API Endpoints (`new_routers/user_router.py`)

- **POST /api/users/oauth**: New endpoint for OAuth login and user creation

## API Usage

### OAuth Login

```http
POST /api/users/oauth
Content-Type: application/json

{
  "auth_provider": "github",
  "auth_provider_id": "lee-seokmin",
  "auth_provider_access_token": "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",
  "email": "dltjrals13@naver.com",
  "name": "이석민",
  "profile_image": "https://avatars.githubusercontent.com/u/68291436?v=4",
  "bio": "Freelancer Full Stack Developer @TeamUpLabs",
  "role": "developer",
  "status": "active",
  "languages": ["한국어"],
  "phone": "010-6683-2802",
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
  "interests": [
    {"interest_category": "Technology", "interest_name": "AI/ML"},
    {"interest_category": "Technology", "interest_name": "IoT"},
    {"interest_category": "Business", "interest_name": "Finance"}
  ],
  "social_links": [
    {"platform": "github", "url": "https://github.com/lee-seokmin"}
  ],
  "tech_stacks": [
    {"tech": "Next.js", "level": 1}
  ]
}
```

**Response:**
```json
{
  "access_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
  "token_type": "bearer",
  "user": {
    "id": 1,
    "name": "이석민",
    "profile_image": "https://avatars.githubusercontent.com/u/68291436?v=4",
    "role": "developer",
    "status": "active"
  }
}
```

### Regular User Creation (Still Supported)

```http
POST /api/users/
Content-Type: application/json

{
  "email": "user@example.com",
  "name": "John Doe",
  "password": "securepassword123",
  "role": "developer"
}
```

## GitHub OAuth Integration

### Setup

1. **Register your application with GitHub:**
   - Go to GitHub Settings > Developer settings > OAuth Apps
   - Create a new OAuth App
   - Set the Authorization callback URL to your frontend callback URL

2. **Get your credentials:**
   - Client ID
   - Client Secret

3. **Use the provided GitHub OAuth class:**
   - See `github_oauth_example.py` for complete implementation

### OAuth Flow

1. **Authorization:** User visits GitHub authorization URL
2. **Callback:** GitHub redirects to your app with an authorization code
3. **Token Exchange:** Exchange code for access token
4. **User Info:** Get user information from GitHub API
5. **Login/Create:** Use the `/api/users/oauth` endpoint to create/login user

## Testing

### Test Script

Run the test script to verify OAuth functionality:

```bash
python test_oauth_user.py
```

This will test both OAuth login and regular user creation.

### Manual Testing

You can test the OAuth endpoint with the provided test data:

```bash
curl -X POST http://localhost:8000/api/users/oauth \
  -H "Content-Type: application/json" \
  -d @test_data.json
```

## Security Considerations

1. **Access Token Storage:** OAuth access tokens are stored in the database. Consider implementing token refresh logic for long-lived tokens.

2. **Token Validation:** Always validate OAuth tokens with the provider before using them.

3. **User Permissions:** OAuth users should have the same permissions as regular users, but you may want to implement additional verification.

4. **Email Verification:** GitHub provides verified email addresses, but you may want to implement additional email verification for critical operations.

## Database Schema

The User model now includes these OAuth-related fields:

- `auth_provider`: The OAuth provider (e.g., "github", "google")
- `auth_provider_id`: The user's ID from the OAuth provider
- `auth_provider_access_token`: The access token from the OAuth provider
- `hashed_password`: Now nullable for OAuth users

## Extending to Other OAuth Providers

To add support for other OAuth providers (Google, Facebook, etc.):

1. **Create provider-specific classes** similar to `GitHubOAuth`
2. **Update the OAuth login endpoint** to handle different providers
3. **Add provider-specific data mapping** functions
4. **Update the User model** if additional provider-specific fields are needed

## Error Handling

The system handles various error scenarios:

- **Duplicate users:** If a user with the same email exists, the OAuth information is updated
- **Invalid tokens:** Proper error responses for invalid OAuth tokens
- **Missing data:** Graceful handling of missing optional fields

## Future Enhancements

1. **Token Refresh:** Implement automatic token refresh for expired OAuth tokens
2. **Multiple Providers:** Allow users to link multiple OAuth accounts
3. **Profile Sync:** Periodic synchronization of user profiles from OAuth providers
4. **Account Linking:** Allow users to link existing accounts with OAuth providers 