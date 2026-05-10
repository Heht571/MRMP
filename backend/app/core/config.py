from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Optional, List
import secrets


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        case_sensitive=True,
        extra="ignore"
    )
    
    PROJECT_NAME: str = "MRMP - 元资源管理平台"
    VERSION: str = "1.0.0"
    DESCRIPTION: str = "模型驱动的元资源管理平台"
    DEBUG: bool = False
    
    # Database
    DATABASE_URL: str = "postgresql+asyncpg://armp:armp@localhost:5432/armp_db"
    DATABASE_URL_SYNC: str = "postgresql://armp:armp@localhost:5432/armp_db"
    
    # Security - Must be set via environment variable in production
    SECRET_KEY: str = ""
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        if not self.SECRET_KEY:
            self.SECRET_KEY = secrets.token_urlsafe(32)
    
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24
    
    # API
    API_V1_STR: str = "/api/v1"

    # CORS
    BACKEND_CORS_ORIGINS: List[str] = ["http://localhost", "http://localhost:80", "http://localhost:5173"]
    
    # Import/Export
    MAX_IMPORT_ROWS: int = 50000
    MAX_EXPORT_ROWS: int = 50000


settings = Settings()
