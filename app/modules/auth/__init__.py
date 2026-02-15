"""
Authentication Module
Handles user authentication, JWT token generation, and role-based access control.
"""

from app.modules.auth.routes import auth_bp, token_required, auth_required
from app.modules.auth.web_routes import web_auth_bp
from app.modules.auth.security import (
    create_access_token,
    decode_access_token,
    verify_password,
    get_password_hash,
    JWT_ALGORITHM,
)
from app.modules.auth import queries

__all__ = [
    "auth_bp",
    "web_auth_bp",
    "token_required",
    "auth_required",
    "create_access_token",
    "decode_access_token",
    "verify_password",
    "get_password_hash",
    "JWT_ALGORITHM",
    "queries",
]
