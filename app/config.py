"""
Application Configuration
Loads settings from environment variables via .env
"""

import os
from datetime import timedelta
from dotenv import load_dotenv

# Load .env file
load_dotenv()


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
