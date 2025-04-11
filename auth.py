from jose import JWTError, jwt
from datetime import datetime, timedelta, timezone
import os
from dotenv import load_dotenv
import bcrypt

load_dotenv()
SECRET_KEY = os.getenv("SECRET_KEY")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

def verify_password(plain_password: str, hashed_password: str) -> bool:
    try:
        # Convert the stored hash back to bytes
        hashed_bytes = hashed_password.encode('utf-8')
        # Check the password
        return bcrypt.checkpw(plain_password.encode('utf-8'), hashed_bytes)
    except Exception:
        return False

def get_password_hash(password: str) -> str:
    # Generate a salt and hash the password
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(password.encode('utf-8'), salt)
    # Return the hash as a string
    return hashed.decode('utf-8')

def create_access_token(data: dict):
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

def verify_token(token: str):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except JWTError:
        return None