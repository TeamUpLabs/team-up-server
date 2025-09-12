from pydantic_settings import BaseSettings
from datetime import datetime, timezone
from zoneinfo import ZoneInfo
from functools import cached_property
from pathlib import Path

BASE_DIR = Path(__file__).parent.parent

class Setting(BaseSettings):
  DEBUG: bool = False
  TITLE: str = "TeamUp API"
  SUMMARY: str = "TeamUp 프로젝트 관리를 위한 RESTful API"
  DESCRIPTION: str = (BASE_DIR / "README.md").read_text(encoding="utf-8")
  VERSION: str = "1.0.0"
  
  TIMEZONE: str = "Asia/Seoul"
  
  LOG_LEVEL: str = "INFO"
  INFO_LOG_PATH: Path = BASE_DIR / "logs" / "info.log"
  WARNING_LOG_PATH: Path = BASE_DIR / "logs" / "warning.log"
  ERROR_LOG_PATH: Path = BASE_DIR / "logs" / "error.log"
  
  @property
  def API_VERSION(self) -> str:
    return f"v{self.VERSION}"
  
  @property
  def API_TITLE(self) -> str:
    return f"{self.TITLE} {self.API_VERSION}"
  
  @cached_property
  def timezone(self) -> ZoneInfo:
    return ZoneInfo(self.TIMEZONE)
  
  @property
  def now(self) -> datetime:
    return datetime.now(tz=self.timezone)
  
  class Config:
    env_file = ".env"
    env_file_encoding = "utf-8"
    
setting = Setting()