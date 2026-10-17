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


@auth_bp.route("/mail/recipients", methods=["GET"])
@auth_required
def get_mail_recipients():
    """
    Get last used email recipients for the logged-in user.
    """
    try:
        user = request.user
        db_session = get_db_session()
        db_user = queries.get_kullanici_by_id(db_session, user.Kullanici_ID)
        recipients_str = db_user.Son_Mail_Alicilari if db_user else ""
        db_session.close()

        recipients = [r.strip() for r in (recipients_str or "").split(",") if r.strip()]
        return jsonify({
            "recipients": recipients,
            "raw": recipients_str or ""
        }), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@auth_bp.route("/mail/send-report", methods=["POST"])
@auth_required
def send_report_mail():
    """
    Send report email with HTML print body and Excel attachment.
    Enforces authorization: Admin or Permission ID 74 ("Mail Gönder").
    Validates recipients and subject.
    Saves last-used recipients on success.
    """
    import base64
    import re
    from app.common.mail import send_email
    from app.models.models import Kullanici, RolYetki, KullaniciRol

    try:
        user = request.user
        db_session = get_db_session()

        # 1. Authorization check: Admin OR Permission ID 74 ("Mail Gönder")
        is_admin = False
        if getattr(user, "Kullanici_Adi", "") and user.Kullanici_Adi.lower() == "admin":
            is_admin = True
        else:
            user_roles = queries.get_user_roles(db_session, user.Kullanici_ID)
            if "admin" in [r.lower() for r in user_roles]:
                is_admin = True

        has_perm_74 = False
        if not is_admin:
            # Query KullaniciRol within active db_session
            user_roles = db_session.query(KullaniciRol).filter_by(
                Kullanici_ID=user.Kullanici_ID,
                Aktif_Pasif=True
            ).all()
            role_ids = [kr.Rol_ID for kr in user_roles]

            if role_ids:
                matched_perm = db_session.query(RolYetki).filter(
                    RolYetki.Rol_ID.in_(role_ids),
                    RolYetki.Yetki_ID == 74,
                    RolYetki.Aktif_Pasif == True
                ).first()
                if matched_perm:
                    has_perm_74 = True

        if not is_admin and not has_perm_74:
            db_session.close()
            return jsonify({
                "error": "Bu işlem için yetkiniz bulunmamaktadır (Yetki: Mail Gönder)."
            }), 403

        # 2. Parse and validate request payload
        data = request.get_json(silent=True) or {}
        recipients_input = data.get("recipients", "")
        subject = (data.get("subject") or "").strip()
        html_body = data.get("html_body") or ""
        note = (data.get("note") or "").strip()
        excel_base64 = data.get("excel_base64")
        filename = (data.get("filename") or "Rapor.xlsx").strip()

        if not subject:
            db_session.close()
            return jsonify({"error": "E-posta konusu boş olamaz."}), 400

        # Parse recipients (support list or comma/semicolon delimited string)
        if isinstance(recipients_input, list):
            raw_recipients = recipients_input
        else:
            raw_recipients = re.split(r"[,;]+", str(recipients_input))

        recipients = [r.strip() for r in raw_recipients if r.strip()]
        if not recipients:
            db_session.close()
            return jsonify({"error": "Lütfen en az bir geçerli alıcı e-posta adresi girin."}), 400

        email_regex = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
        invalid_emails = [r for r in recipients if not email_regex.match(r)]
        if invalid_emails:
            db_session.close()
            return jsonify({
                "error": f"Geçersiz e-posta adresi tespit edildi: {', '.join(invalid_emails)}"
            }), 400

        # Prepend note to html_body if present
        if note:
            escaped_note = note.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;").replace("\n", "<br>")
            note_html = (
                f'<div style="margin-bottom: 20px; padding: 14px 18px; background: #f0fdf4; '
                f'border-left: 4px solid #10b981; border-radius: 6px; font-size: 14px; '
                f'color: #166534; line-height: 1.6; font-family: sans-serif;">'
                f'<strong style="display: block; margin-bottom: 4px; color: #14532d; font-size: 13px; text-transform: uppercase; letter-spacing: 0.5px;">Not:</strong>'
                f'{escaped_note}'
                f'</div>'
            )
            if html_body:
                # If wrapped in our standard container div, insert inside or at top
                html_body = f'<div style="font-family: -apple-system, BlinkMacSystemFont, \'Segoe UI\', Roboto, Helvetica, Arial, sans-serif; padding: 20px;">{note_html}</div>' + html_body
            else:
                html_body = note_html

        # 3. Prepare attachments
        attachments = []
        if excel_base64:
            try:
                # Remove data URL prefix if present
                if "," in excel_base64:
                    excel_base64 = excel_base64.split(",", 1)[1]
                excel_bytes = base64.b64decode(excel_base64)

                # Clean filename with timestamp fallback
                clean_filename = re.sub(r'[\\/*?:"<>|]', "", filename).strip()
                if not clean_filename or clean_filename == ".xlsx":
                    from datetime import datetime
                    clean_filename = f"Rapor_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
                elif not clean_filename.lower().endswith(".xlsx"):
                    clean_filename += ".xlsx"

                attachments.append({
                    "filename": clean_filename,
                    "content": excel_bytes,
                    "content_type": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                })
            except Exception as e:
                db_session.close()
                return jsonify({"error": f"Excel eki işlenirken hata oluştu: {str(e)}"}), 400

        # Plain text fallback
        note_prefix = f"Not:\n{note}\n\n" if note else ""
        plain_body = f"{note_prefix}{subject}\n\nDetaylar ekteki rapor ve HTML gövdesinde sunulmuştur."

        # 4. Send email via existing mail utility
        success = send_email(
            to=recipients,
            subject=subject,
            body=plain_body,
            html=html_body,
            attachments=attachments if attachments else None
        )

        if not success:
            db_session.close()
            return jsonify({
                "error": "E-posta gönderimi başarısız oldu. Lütfen SMTP ayarlarını ve alıcı adreslerini kontrol edin."
            }), 500

        # 5. On successful delivery, save last used recipients for this user
        try:
            db_user = db_session.query(Kullanici).filter_by(Kullanici_ID=user.Kullanici_ID).first()
            if db_user:
                db_user.Son_Mail_Alicilari = ", ".join(recipients)
                db_session.commit()
        except Exception as e:
            # Non-blocking for client, but logged
            db_session.rollback()

        db_session.close()
        return jsonify({
            "message": "E-posta başarıyla gönderildi.",
            "recipients": recipients
        }), 200

    except Exception as e:
        return jsonify({"error": f"Beklenmeyen bir hata oluştu: {str(e)}"}), 500

