import pytest
from sqlalchemy import create_engine
from sqlalchemy.engine import make_url

from backend.config import normalize_database_url, validate_production_settings


@pytest.mark.parametrize(
    ("database_url", "expected_driver"),
    [
        ("postgres://talentverse:example@db.example/neon?sslmode=require", "postgresql+psycopg"),
        ("postgresql://talentverse:example@db.example/neon?sslmode=require", "postgresql+psycopg"),
        ("postgresql+psycopg2://talentverse:example@db.example/neon", "postgresql+psycopg"),
        ("postgresql+psycopg://talentverse:example@db.example/neon", "postgresql+psycopg"),
    ],
)
def test_normalize_postgresql_urls_for_psycopg3(database_url, expected_driver):
    normalized = make_url(normalize_database_url(database_url))

    assert normalized.drivername == expected_driver
    assert normalized.username == "talentverse"
    assert normalized.password == "example"
    if normalized.query:
        assert normalized.query["sslmode"] == "require"


def test_sqlalchemy_creates_postgresql_engine_with_psycopg3():
    database_url = normalize_database_url("postgresql://user:example@db.example/neon")
    engine = create_engine(database_url)
    try:
        assert engine.dialect.name == "postgresql"
        assert engine.dialect.driver == "psycopg"
    finally:
        engine.dispose()


def test_normalize_database_url_preserves_sqlite():
    database_url = "sqlite:///./talentverse.db"

    assert normalize_database_url(database_url) == database_url


@pytest.mark.parametrize(
    "secret",
    [
        "short",
        "x" * 64,
        "local-development-only-secret-change-before-deploy",
    ],
)
def test_production_rejects_weak_jwt_secrets(secret):
    with pytest.raises(RuntimeError, match="TALENTVERSE_SECRET_KEY"):
        validate_production_settings(
            "production",
            secret,
            ["https://talentverse.example.com"],
            "postgresql+psycopg://user:pass@db.example/app",
        )


def test_production_rejects_wildcard_or_missing_cors_origins():
    secret = "9sC7nH2xP4bQ8vL1mR6tY3kW5dF0aZ2u"
    database_url = "postgresql+psycopg://user:pass@db.example/app"

    for origins in (["https://talentverse.example.com", "*"], []):
        with pytest.raises(RuntimeError, match="CORS_ORIGINS"):
            validate_production_settings("production", secret, origins, database_url)


def test_production_requires_postgresql_database():
    with pytest.raises(RuntimeError, match="DATABASE_URL"):
        validate_production_settings(
            "production",
            "9sC7nH2xP4bQ8vL1mR6tY3kW5dF0aZ2u",
            ["https://talentverse.example.com"],
            "sqlite:///./talentverse.db",
        )


def test_production_accepts_strong_secret_explicit_cors_and_postgresql():
    validate_production_settings(
        "production",
        "9sC7nH2xP4bQ8vL1mR6tY3kW5dF0aZ2u",
        ["https://talentverse.example.com"],
        "postgresql+psycopg://user:pass@db.example/app",
    )
