from pydantic import BaseModel

class OauthRequest(BaseModel):
  provider: str
  code: str
  device_id: str
  session_id: str