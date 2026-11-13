"""Application configuration and environment settings."""
import os
from pathlib import Path
from dotenv import load_dotenv

# Load .env from root directory
env_path = Path(__file__).resolve().parent.parent / ".env"
load_dotenv(dotenv_path=env_path, override=False)

def csv_env(name: str, default: str) -> list[str]:
    return [item.strip().lower() for item in os.getenv(name, default).split(",") if item.strip()]

# AI Provider Configuration
AI_PROVIDER_ORDER = csv_env("AI_PROVIDER_ORDER", "gemini,groq,openai,mistral")
PROVIDER_MODELS = {
    "gemini": os.getenv("GEMINI_MODEL", "gemini-3.8-flash"),
    "groq": os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile"),
    "openai": os.getenv("OPENAI_MODEL", "gpt-4o-mini"),
    "mistral": os.getenv("MISTRAL_MODEL", "mistral-small-latest"),
}
PROVIDER_ENV_KEYS = {
    "gemini": "GOOGLE_API_KEY",
    "groq": "GROQ_API_KEY",
    "openai": "OPENAI_API_KEY",
    "mistral": "MISTRAL_API_KEY",
}

# Quotas and Rate Limits
SESSION_DAILY_LIMIT = max(1, int(os.getenv("TALENTVERSE_SESSION_DAILY_LIMIT", "20")))
GLOBAL_DAILY_LIMIT = max(1, int(os.getenv("TALENTVERSE_GLOBAL_DAILY_LIMIT", "200")))
DUPLICATE_COOLDOWN_SECONDS = max(3, int(os.getenv("TALENTVERSE_DUPLICATE_COOLDOWN_SECONDS", "10")))

# Security & Database
APP_ENV = os.getenv("TALENTVERSE_ENV", "development").strip().lower()
_configured_secret = os.getenv("TALENTVERSE_SECRET_KEY", "").strip()
if APP_ENV in {"production", "prod"} and len(_configured_secret) < 32:
    raise RuntimeError("TALENTVERSE_SECRET_KEY must contain at least 32 characters in production.")
SECRET_KEY = _configured_secret or "local-development-only-secret-change-before-deploy"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24 * 7  # 7 days

# CORS is open only to local development origins by default. Configure deployed origins explicitly.
CORS_ORIGINS = csv_env(
    "CORS_ORIGINS",
    "http://localhost:5173,http://127.0.0.1:5173",
)
if APP_ENV in {"production", "prod"} and "*" in CORS_ORIGINS:
    raise RuntimeError("CORS_ORIGINS must list explicit origins in production.")

DB_URL = os.getenv("DATABASE_URL", "sqlite:///./talentverse.db")
UPLOAD_DIR = Path(__file__).resolve().parent.parent / "uploads"
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
