from typing import List, Union
from pydantic import AnyHttpUrl, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict
import os

class Settings(BaseSettings):
    PROJECT_NAME: str = "UFPSO Horarios & Gestión Académica API"
    ENVIRONMENT: str = "development"
    DEBUG: bool = True
    
    # Neon PostgreSQL connection string
    DATABASE_URL: str = "postgresql+asyncpg://neondb_owner:npg_skoR7UDEq9Tj@ep-lingering-queen-b44qykzn-pooler.c-6.us-east-2.aws.neon.tech/neondb?ssl=require"
    
    # JWT Auth
    SECRET_KEY: str = "ufpso_super_secret_jwt_key_ocana_norte_de_santander"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 30  # 30 days
    
    # CORS
    CORS_ORIGINS: List[str] = ["*"]

    @field_validator("DATABASE_URL", mode="before")
    @classmethod
    def assemble_db_connection(cls, v: str) -> str:
        if isinstance(v, str):
            # If standard postgresql:// is provided, adapt for asyncpg
            if v.startswith("postgresql://"):
                v = v.replace("postgresql://", "postgresql+asyncpg://", 1)
            # Ensure ssl parameter for asyncpg
            if "sslmode=require" in v and "ssl=require" not in v:
                v = v.replace("sslmode=require", "ssl=require")
            elif "ssl=require" not in v and "sslmode" not in v:
                separator = "&" if "?" in v else "?"
                v = f"{v}{separator}ssl=require"
            # asyncpg doesn't accept channel_binding param
            if "channel_binding=require" in v:
                v = v.replace("&channel_binding=require", "").replace("?channel_binding=require&", "?").replace("?channel_binding=require", "")
        return v

    model_config = SettingsConfigDict(
        env_file=os.path.join(os.path.dirname(os.path.dirname(__file__)), ".env"),
        env_file_encoding="utf-8",
        extra="ignore"
    )

settings = Settings()
