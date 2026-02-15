"""
SQLAlchemy 2.0 Database Setup
Provides ORM context and connection pooling configuration.
"""

from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import Session, sessionmaker
from flask import current_app


# Initialize SQLAlchemy with Flask-SQLAlchemy for Flask integration
db = SQLAlchemy()


def get_db_session() -> Session:
    """
    Get a database session for the current app context.
    
    Returns:
        SQLAlchemy Session object
    """
    engine = db.engine
    SessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False)
    return SessionLocal()


def init_db():
    """Initialize database tables."""
    db.create_all()


def drop_db():
    """Drop all database tables (use with caution)."""
    db.drop_all()
