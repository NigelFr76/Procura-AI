"""Unit tests for configuration and settings validation."""

from app.core.config import Settings, EnvironmentType


def test_default_settings():
    """Verify default configuration attributes."""
    s = Settings()
    assert s.PROJECT_NAME == "AI Procurement & Vendor Intelligence Platform"
    assert s.API_V1_STR == "/api/v1"
    assert s.POSTGRES_PORT == 5432
    assert s.POSTGRES_DB == "procure_db"
    assert s.REDIS_PORT == 6379


def test_database_urls():
    """Verify async and sync database URL generation."""
    s = Settings(
        POSTGRES_SERVER="dbhost",
        POSTGRES_PORT=5433,
        POSTGRES_USER="testuser",
        POSTGRES_PASSWORD="testpassword",
        POSTGRES_DB="testdb",
    )
    assert s.async_database_url == "postgresql+asyncpg://testuser:testpassword@dbhost:5433/testdb"
    assert s.sync_database_url == "postgresql://testuser:testpassword@dbhost:5433/testdb"


def test_redis_url():
    """Verify redis URL generation with and without password."""
    s_no_pass = Settings(REDIS_HOST="redishost", REDIS_PORT=6380, REDIS_DB=2, REDIS_PASSWORD=None)
    assert s_no_pass.redis_url == "redis://redishost:6380/2"

    s_pass = Settings(REDIS_HOST="redishost", REDIS_PORT=6380, REDIS_DB=2, REDIS_PASSWORD="secret")
    assert s_pass.redis_url == "redis://:secret@redishost:6380/2"


def test_cors_origins_parsing():
    """Verify parsing of list, JSON string, and comma-separated string for CORS origins."""
    # List format
    s1 = Settings(BACKEND_CORS_ORIGINS=["http://test.com", "http://another.com"])
    assert s1.BACKEND_CORS_ORIGINS == ["http://test.com", "http://another.com"]

    # JSON array string
    s2 = Settings(BACKEND_CORS_ORIGINS='["http://alpha.com", "http://beta.com"]')
    assert s2.BACKEND_CORS_ORIGINS == ["http://alpha.com", "http://beta.com"]

    # Comma-separated string
    s3 = Settings(BACKEND_CORS_ORIGINS="http://one.com, http://two.com")
    assert s3.BACKEND_CORS_ORIGINS == ["http://one.com", "http://two.com"]
