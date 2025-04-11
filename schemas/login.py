from pydantic import BaseModel, EmailStr

class LoginForm(BaseModel):
    userEmail: EmailStr
    password: str

class Token(BaseModel):
    access_token: str
    token_type: str
    user_id: int
    user_name: str
    user_email: str