"""
Application Configuration
Loads settings from environment variables via .env
"""

import os
import subprocess
from datetime import datetime, timedelta
from dotenv import load_dotenv

# Load .env file
load_dotenv()

# ---------------------------------------------------------------------------
# Application Version
# ---------------------------------------------------------------------------
# The base semantic version. Increment this on each meaningful release.
APP_VERSION = "2.0"


def get_app_version() -> str:
    """
    Return the application version string.

    Tries to enrich the base APP_VERSION with the short git commit hash and
    commit date so each deployment is uniquely identifiable.
    Falls back gracefully to APP_VERSION + today's date when git is not
    available (e.g. production servers without git installed).

    Example output:  "v2.0 (a1b2c3d · 2026-03-25)"
    """
    try:
        short_hash = subprocess.check_output(
            ["git", "rev-parse", "--short", "HEAD"],
            stderr=subprocess.DEVNULL,
            timeout=2,
        ).decode().strip()

        commit_date = subprocess.check_output(
            ["git", "log", "-1", "--format=%cd", "--date=short"],
            stderr=subprocess.DEVNULL,
            timeout=2,
        ).decode().strip()

        return f"v{APP_VERSION} ({short_hash} · {commit_date})"
    except Exception:
        today = datetime.now().strftime("%Y-%m-%d")
        return f"v{APP_VERSION} ({today})"


class Config:
    """Base configuration"""
    
    # Flask
    FLASK_DEBUG = os.getenv("FLASK_DEBUG", "0") == "1"
    SECRET_KEY = os.getenv("SECRET_KEY", "dev-secret-key-change-in-production")
    
    # SQLAlchemy settings
    SQLALCHEMY_ECHO = False
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ENGINE_OPTIONS = {
        "pool_size": 20,
        "max_overflow": 10,
        "pool_recycle": 3600,
        "echo": False,
    }
    
    # Flask-Session
    SESSION_TYPE = "filesystem"  # Store sessions in filesystem (default)
    PERMANENT_SESSION_LIFETIME = timedelta(days=7)
    SESSION_PERMANENT = False
    
    # JWT/Session
    JWT_ALGORITHM = "HS256"
    JWT_EXPIRATION_MINUTES = 30
    
    # Pagination
    DEFAULT_PAGE_SIZE = 100
    MAX_PAGE_SIZE = 1000


class DevelopmentConfig(Config):
    """Development configuration"""
    
    DEBUG = True
    TESTING = False
    
    # Build MySQL connection string from environment variables
    db_user = os.getenv("DB_USER", "root")
    db_password = os.getenv("DB_PASSWORD", "")
    db_host = os.getenv("DB_HOST", "localhost")
    db_port = os.getenv("DB_PORT", "3306")
    db_name = os.getenv("DB_NAME", "SilverCloud")
    
    SQLALCHEMY_DATABASE_URI = (
        f"mysql+mysqlconnector://{db_user}:{db_password}@"
        f"{db_host}:{db_port}/{db_name}"
    )
    SQLALCHEMY_ECHO = True


class TestingConfig(Config):
    """Testing configuration"""
    
    DEBUG = True
    TESTING = True
    
    # Use test database
    db_user = os.getenv("DB_USER", "root")
    db_password = os.getenv("DB_PASSWORD", "")
    db_host = os.getenv("DB_HOST", "localhost")
    db_port = os.getenv("DB_PORT", "3306")
    db_test_name = os.getenv("DB_TEST_NAME", "SilverCloud_test")
    
    SQLALCHEMY_DATABASE_URI = (
        f"mysql+mysqlconnector://{db_user}:{db_password}@"
        f"{db_host}:{db_port}/{db_test_name}"
    )


class ProductionConfig(Config):
    """Production configuration"""
    
    DEBUG = False
    TESTING = False
    
    db_user = os.getenv("DB_USER")
    db_password = os.getenv("DB_PASSWORD")
    db_host = os.getenv("DB_HOST")
    db_port = os.getenv("DB_PORT", "3306")
    db_name = os.getenv("DB_NAME")
    
    SQLALCHEMY_DATABASE_URI = (
        f"mysql+mysqlconnector://{db_user}:{db_password}@"
        f"{db_host}:{db_port}/{db_name}?ssl_disabled=False"
    )


def get_config(config_name: str = "development") -> type:
    """
    Get configuration class by name.
    
    Args:
        config_name: Configuration name ('development', 'testing', 'production')
    
    Returns:
        Configuration class
    """
    configs = {
        "development": DevelopmentConfig,
        "testing": TestingConfig,
        "production": ProductionConfig,
    }
    return configs.get(config_name, DevelopmentConfig)
