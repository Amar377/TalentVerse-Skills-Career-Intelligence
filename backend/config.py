"""Application configuration and environment settings."""
import os
from pathlib import Path

from dotenv import load_dotenv
from sqlalchemy.exc import ArgumentError
from sqlalchemy.engine import make_url

# Load .env from root directory
env_path = Path(__file__).resolve().parent.parent / ".env"
load_dotenv(dotenv_path=env_path, override=False)


def csv_env(name: str, default: str) -> list[str]:
    return [item.strip().lower() for item in os.getenv(name, default).split(",") if item.strip()]


def normalize_database_url(database_url: str) -> str:
    """Use psycopg 3 for standard PostgreSQL URLs while preserving other dialects."""
    try:
        url = make_url(database_url)
    except ArgumentError:
        raise ValueError("DATABASE_URL is not a valid SQLAlchemy URL.") from None
    if url.drivername in {"postgres", "postgresql", "postgresql+psycopg2"}:
        url = url.set(drivername="postgresql+psycopg")
    return url.render_as_string(hide_password=False)


_DEVELOPMENT_SECRET = "local-development-only-secret-change-before-deploy"


def validate_production_settings(
    app_env: str,
    secret_key: str,
    cors_origins: list[str],
    database_url: str,
) -> None:
    if app_env not in {"production", "prod"}:
        return
    if (
        len(secret_key) < 32
        or len(set(secret_key)) < 8
        or secret_key == _DEVELOPMENT_SECRET
    ):
        raise RuntimeError(
            "TALENTVERSE_SECRET_KEY must be a strong, randomly generated value "
            "of at least 32 characters in production."
        )
    if not cors_origins or "*" in cors_origins:
        raise RuntimeError(
            "CORS_ORIGINS must contain explicit origins and cannot include '*' in production."
        )
    if not database_url:
        raise RuntimeError("DATABASE_URL must be configured for PostgreSQL in production.")
    try:
        database_backend = make_url(database_url).get_backend_name()
    except ArgumentError:
        raise RuntimeError("DATABASE_URL is not a valid SQLAlchemy URL.") from None
    if database_backend != "postgresql":
        raise RuntimeError("DATABASE_URL must be configured for PostgreSQL in production.")


# AI Provider Configuration
AI_PROVIDER_ORDER = csv_env("AI_PROVIDER_ORDER", "groq,gemini,openai,mistral")
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
SECRET_KEY = _configured_secret or _DEVELOPMENT_SECRET
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24 * 7  # 7 days

_is_production = APP_ENV in {"production", "prod"}
CORS_ORIGINS = csv_env(
    "CORS_ORIGINS",
    "" if _is_production else "http://localhost:5173,http://127.0.0.1:5173",
)
_configured_database_url = os.getenv("DATABASE_URL", "").strip()
if not _configured_database_url and not _is_production:
    _configured_database_url = "sqlite:///./talentverse.db"
DB_URL = normalize_database_url(_configured_database_url) if _configured_database_url else ""
validate_production_settings(
    APP_ENV,
    _configured_secret,
    CORS_ORIGINS,
    DB_URL,
)

UPLOAD_DIR = Path(__file__).resolve().parent.parent / "uploads"
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
