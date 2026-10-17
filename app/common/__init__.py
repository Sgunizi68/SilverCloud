"""Common utilities and shared components"""

from app.common.database import db, get_db_session
from app.common.mail import send_email

__all__ = ["db", "get_db_session", "send_email"]

