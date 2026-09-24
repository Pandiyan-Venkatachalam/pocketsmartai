import os
from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict

BASE_DIR = Path(__file__).resolve().parent.parent.parent

class Settings(BaseSettings):
    APP_NAME: str = "PocketSmart AI"
    APP_ENV: str = "development"
    DEBUG: bool = True
    HOST: str = "127.0.0.1"
    PORT: int = 8080

    # JWT Authentication
    JWT_SECRET_KEY: str = "pocketsmart-ai-super-secret-dev-key-789123456"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 1440  # 24 hours

    # Database
    DATABASE_URL: str = "sqlite:///./pocketsmart.db"

    # Google Gemini AI
    GEMINI_API_KEY: str = ""
    GEMINI_MODEL: str = "gemini-3.6-flash"
    MOCK_AI_MODE: str = "auto"  # "auto" (falls back to mock if no key), "force_mock", "live"

    # Cloudinary Configuration
    CLOUDINARY_CLOUD_NAME: str = "dqr1zbyeb"
    CLOUDINARY_API_KEY: str = "273174792865529"
    CLOUDINARY_API_SECRET: str = "jF_wQ3z_92GCh6kCk_YxmN1G4r0"

    # Paths
    BASE_DIR: Path = BASE_DIR
    DATA_DIR: Path = BASE_DIR / "data"
    MOCK_PRODUCTS_PATH: Path = BASE_DIR / "data" / "mock_products.json"
    UPLOAD_DIR: Path = BASE_DIR / "app" / "static" / "uploads"

    model_config = SettingsConfigDict(
        env_file=str(BASE_DIR / ".env"),
        env_file_encoding="utf-8",
        extra="ignore"
    )

settings = Settings()

# Ensure upload directory exists
try:
    os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
except Exception:
    pass
