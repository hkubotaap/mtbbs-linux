"""
Application configuration
"""
from pydantic_settings import BaseSettings
from typing import List


class Settings(BaseSettings):
    """Application settings"""

    # App
    APP_NAME: str = "MTBBS Linux"
    APP_VERSION: str = "4.0.0"
    DEBUG: bool = True

    # Server
    HOST: str = "0.0.0.0"
    PORT: int = 8000

    # Telnet Server
    TELNET_HOST: str = "0.0.0.0"
    TELNET_PORT: int = 23
    TELNET_MAX_CONNECTIONS: int = 100
    TELNET_IDLE_TIMEOUT: int = 1800  # 30 minutes

    # Database
    DATABASE_URL: str = "sqlite+aiosqlite:///./mtbbs.db"

    # Redis
    REDIS_URL: str = "redis://localhost:6379"
    REDIS_SESSION_PREFIX: str = "session:"
    REDIS_SESSION_EXPIRE: int = 3600  # 1 hour

    # Security
    SECRET_KEY: str = "your-secret-key-change-this-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30

    # CORS
    ALLOWED_ORIGINS: List[str] = ["http://localhost:3000", "http://localhost"]

    # File Storage
    FILE_STORAGE_PATH: str = "./storage"
    MAX_FILE_SIZE: int = 10 * 1024 * 1024  # 10MB

    # BBS Settings
    MAX_SAME_IP: int = 3
    GUEST_USER_ID: str = "guest"
    DEFAULT_USER_LEVEL: int = 1
    SYSOP_LEVEL: int = 9

    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()
