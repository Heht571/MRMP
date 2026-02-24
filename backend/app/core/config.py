from pydantic_settings import BaseSettings
from typing import Optional, List


class Settings(BaseSettings):
    PROJECT_NAME: str = "MRMP - 元资源管理平台"
    VERSION: str = "1.0.0"
    DESCRIPTION: str = "模型驱动的元资源管理平台"
    DEBUG: bool = False
    
    # Database
    DATABASE_URL: str = "postgresql+asyncpg://armp:armp@localhost:5432/armp_db"
    DATABASE_URL_SYNC: str = "postgresql://armp:armp@localhost:5432/armp_db"
    
    # Security
    SECRET_KEY: str = "your-secret-key-change-in-production"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24
    
    # API
    API_V1_STR: str = "/api/v1"

    # CORS
    BACKEND_CORS_ORIGINS: List[str] = ["http://localhost", "http://localhost:80", "http://localhost:5173"]
    
    # Import/Export
    MAX_IMPORT_ROWS: int = 50000
    MAX_EXPORT_ROWS: int = 50000
    
    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()
