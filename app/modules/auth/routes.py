"""
Authentication Routes
Login, token validation, and user info endpoints.
Uses Flask blueprints for modular routing.
"""

from datetime import timedelta
from functools import wraps
from flask import Blueprint, request, jsonify, session, render_template, redirect, url_for
from sqlalchemy.orm import Session
from flask import current_app

from app.common.database import db, get_db_session
from app.modules.auth import security, queries
from app.modules.auth.schemas import TokenRequest, LoginResponse, UserInfo, UserPermissions

auth_bp = Blueprint("auth", __name__, url_prefix="/api/v1")


def token_required(f):
    """
    Decorator to require valid JWT token in Authorization header.
    Validates token and adds user_id to request context.
    """
    @wraps(f)
    def decorated(*args, **kwargs):
        token = None
        
        # Check for token in Authorization header
        if "Authorization" in request.headers:
            auth_header = request.headers["Authorization"]
            try:
                token = auth_header.split(" ")[1]
            except IndexError:
                return jsonify({"error": "Invalid authorization header"}), 401
        
        if not token:
            return jsonify({"error": "Missing authorization token"}), 401
        
        # Validate token
        payload = security.decode_access_token(
            token,
            current_app.config["SECRET_KEY"]
        )
        
        if not payload:
            return jsonify({"error": "Invalid or expired token"}), 401
        
        # Get username from token
        username = payload.get("sub")
        if not username:
            return jsonify({"error": "Invalid token payload"}), 401
        
        # Get user from database
        db_session = get_db_session()
        user = queries.get_kullanici_by_username(db_session, username)
        db_session.close()
        
        if not user:
            return jsonify({"error": "User not found"}), 404
        
        # Add user to request context
        request.user = user
        return f(*args, **kwargs)
    
    return decorated


def auth_required(f):
    """
    Decorator to require authentication via either:
    1. JWT token in Authorization header (for API calls)
    2. Session cookie (for web-rendered dashboard)
    
    Validates auth and adds user to request context.
    """
    @wraps(f)
    def decorated(*args, **kwargs):
        user = None
        db_session = get_db_session()
        
        # Try JWT token first
        token = None
        if "Authorization" in request.headers:
            auth_header = request.headers["Authorization"]
            try:
                token = auth_header.split(" ")[1]
            except IndexError:
                pass
        
        if token:
            # Validate JWT token
            payload = security.decode_access_token(
                token,
                current_app.config["SECRET_KEY"]
            )
            
            if payload:
                username = payload.get("sub")
                if username:
                    user = queries.get_kullanici_by_username(db_session, username)
        
        # Try session if token auth failed
        if not user and 'user_id' in session:
            user = queries.get_kullanici_by_id(db_session, session['user_id'])
        
        db_session.close()
        
        if not user:
            return jsonify({"error": "Authentication required"}), 401
        
        # Add user to request context
        request.user = user
        return f(*args, **kwargs)
    
    return decorated


@auth_bp.route("/token", methods=["POST"])
def login():
    """
    Login endpoint - exchange username/password for JWT token.
    
    Request body:
        {
            "username": "string",
            "password": "string"
        }
    
    Response:
        {
            "access_token": "eyJ...",
            "token_type": "bearer",
            "user": {
                "Kullanici_ID": 1,
                "Adi_Soyadi": "John Doe",
                "Kullanici_Adi": "john",
                "Email": "john@example.com",
                "Aktif_Pasif": true,
                "branches": [1, 2]
            },
            "permissions": ["view_reports", "create_invoice"]
        }
    """
    try:
        # Parse request - accept both JSON and form-encoded data
        if request.is_json:
            data = request.get_json()
        else:
            # Accept form-encoded data (application/x-www-form-urlencoded)
            data = request.form or request.values
        
        if not data:
            return jsonify({"error": "Request body required"}), 400
        
        username = data.get("username")
        password = data.get("password")
        
        if not username or not password:
            return jsonify({"error": "Username and password required"}), 400
        
        # Authenticate user
        db_session = get_db_session()
        user = queries.authenticate_user(db_session, username, password)
        
        if not user:
            db_session.close()
            return jsonify({"error": "Invalid credentials"}), 401
        
        if not user.Aktif_Pasif:
            db_session.close()
            return jsonify({"error": "User account is inactive"}), 403
        
        # Get user permissions and branches
        permissions = queries.get_user_permissions(db_session, user.Kullanici_ID)
        branches = queries.get_user_branches(db_session, user.Kullanici_ID)
        db_session.close()
        
        # Create JWT token
        access_token_expires = timedelta(
            minutes=current_app.config.get("JWT_EXPIRATION_MINUTES", 30)
        )
        access_token = security.create_access_token(
            data={"sub": user.Kullanici_Adi},
            secret_key=current_app.config["SECRET_KEY"],
            expires_delta=access_token_expires
        )
        
        # Build response
        user_info = UserInfo(
            Kullanici_ID=user.Kullanici_ID,
            Adi_Soyadi=user.Adi_Soyadi,
            Kullanici_Adi=user.Kullanici_Adi,
            Email=user.Email,
            Aktif_Pasif=user.Aktif_Pasif,
            branches=branches
        )
        
        response = LoginResponse(
            access_token=access_token,
            token_type="bearer",
            user=user_info.to_dict(),
            permissions=permissions
        )
        
        return jsonify(response.to_dict()), 200
    
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@auth_bp.route("/me", methods=["GET"])
@auth_required
def get_current_user():
    """
    Get current authenticated user info.
    Requires valid Authorization header with Bearer token.
    
    Response:
        {
            "Kullanici_ID": 1,
            "Adi_Soyadi": "John Doe",
            "Kullanici_Adi": "john",
            "Email": "john@example.com",
            "Aktif_Pasif": true,
            "branches": [1, 2]
        }
    """
    try:
        user = request.user
        db_session = get_db_session()
        branches = queries.get_user_branches(db_session, user.Kullanici_ID)
        db_session.close()
        
        user_info = UserInfo(
            Kullanici_ID=user.Kullanici_ID,
            Adi_Soyadi=user.Adi_Soyadi,
            Kullanici_Adi=user.Kullanici_Adi,
            Email=user.Email,
            Aktif_Pasif=user.Aktif_Pasif,
            branches=branches
        )
        
        return jsonify(user_info.to_dict()), 200
    
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@auth_bp.route("/permissions", methods=["GET"])
@auth_required
def get_user_permissions():
    """
    Get current user's permissions and roles.
    Optional query parameter: sube_id (filter permissions by branch).
    
    Query params:
        ?sube_id=1  (optional, filter by branch)
    
    Response:
        {
            "Kullanici_ID": 1,
            "Kullanici_Adi": "john",
            "permissions": ["view_reports", "create_invoice"],
            "roles": ["Manager", "Accountant"],
            "branches": [1, 2]
        }
    """
    try:
        user = request.user
        sube_id = request.args.get("sube_id", type=int)
        
        db_session = get_db_session()
        permissions = queries.get_user_permissions(db_session, user.Kullanici_ID, sube_id)
        roles = queries.get_user_roles(db_session, user.Kullanici_ID, sube_id)
        branches = queries.get_user_branches(db_session, user.Kullanici_ID)
        db_session.close()
        
        result = UserPermissions(
            Kullanici_ID=user.Kullanici_ID,
            Kullanici_Adi=user.Kullanici_Adi,
            permissions=permissions,
            roles=roles,
            branches=branches
        )
        
        return jsonify(result.to_dict()), 200
    
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@auth_bp.route("/health", methods=["GET"])
def health():
    """
    Health check endpoint - does not require authentication.
    
    Response:
        {
            "status": "ok"
        }
    """
    return jsonify({"status": "ok"}), 200
