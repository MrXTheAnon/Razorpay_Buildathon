import os
from pathlib import Path
from pydantic import BaseSettings

# Locate infra/.env relative to this file
BASE_DIR = Path(__file__).resolve().parent.parent.parent
ENV_PATH = BASE_DIR / "infra" / ".env"
if not ENV_PATH.exists():
    ENV_PATH = BASE_DIR / ".env"

class Settings(BaseSettings):
    PROJECT_NAME: str = "RazorLoop AI Revenue Recovery"
    VERSION: str = "1.0.0"
    API_V1_STR: str = "/api/v1"

    # Razorpay credentials
    RAZORPAY_KEY_ID: str = ""
    RAZORPAY_KEY_SECRET: str = ""
    RAZORPAY_WEBHOOK_SECRET: str = "whsec_xxx"

    # Telegram configuration
    TELEGRAM_BOT_TOKEN: str = ""
    TELEGRAM_DEMO_CHAT_ID: str = ""

    # Database
    DATABASE_URL: str = "sqlite+aiosqlite:///./dev.db"

    # OpenAI / LLM
    OPENAI_API_KEY: str = ""

    # OmniRoute Multi-Model Gateway
    OMNIROUTE_BASE_URL: str = "http://127.0.0.1:20128/v1"
    OMNIROUTE_API_KEY: str = ""
    OMNIROUTE_MODEL: str = "github/gpt-4o-mini"
    OMNIROUTE_COMBO: str = ""
    APP_HOST_URL: str = "http://192.168.1.37:8000"

    class Config:
        env_file = str(ENV_PATH)
        env_file_encoding = "utf-8"
        case_sensitive = True

settings = Settings()

# Normalize database URL for async SQLite if needed
if settings.DATABASE_URL.startswith("postgresql://"):
    # If user wants asyncpg or fallback to SQLite
    # For zero-setup fallback, we check if postgres is reachable, otherwise default to sqlite
    pass
elif not settings.DATABASE_URL.startswith("sqlite+aiosqlite://") and settings.DATABASE_URL.startswith("sqlite://"):
    settings.DATABASE_URL = settings.DATABASE_URL.replace("sqlite://", "sqlite+aiosqlite://")
