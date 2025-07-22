from pydantic import BaseModel

class LoginRequest(BaseModel):
    email: str
    password: str
    device_id: str
    session_id: str
    
class OauthRequest(BaseModel):
    provider: str
    code: str
    device_id: str
    session_id: str
    
class LogoutRequest(BaseModel):
    session_id: str