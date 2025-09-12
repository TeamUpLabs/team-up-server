import os
from dotenv import load_dotenv
from jose import JWTError, jwt

load_dotenv()

ALGORITHM = "HS256"
SECRET_KEY = os.getenv("SECRET_KEY")

def serialize_data(data):
    """Recursively convert non-serializable objects to dictionaries."""
    if data is None or isinstance(data, (str, int, float, bool)):
        return data
    elif isinstance(data, list):
        return [serialize_data(item) for item in data]
    elif isinstance(data, dict):
        return {key: serialize_data(value) for key, value in data.items()}
    elif hasattr(data, 'dict') and callable(getattr(data, 'dict', None)):
        return data.dict()  # Convert Pydantic models to dict
    elif hasattr(data, '__dict__'):
        # Handle SQLAlchemy models and other objects with __dict__
        return {k: serialize_data(v) for k, v in data.__dict__.items() if not k.startswith('_')}
    return str(data)  # Fallback to string representation

def create_access_token(data: dict):
  to_encode = data.copy()
  to_encode = serialize_data(to_encode)
  
  return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

def verify_token(token: str):
  try:
    payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    return payload
  except JWTError:
    raise ValueError("Invalid token")