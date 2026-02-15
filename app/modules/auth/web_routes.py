"""
Authentication Web Routes (Server-Rendered)
Login, dashboard, and logout pages using Jinja2 templates.
"""

from flask import Blueprint, request, render_template, redirect, url_for, session
from app.common.database import get_db_session
from app.modules.auth import security, queries
from app.modules.reference import queries as ref_queries

web_auth_bp = Blueprint("web_auth", __name__)


def login_required(f):
    """Decorator to require session-based login."""
    from functools import wraps
    
    @wraps(f)
    def decorated(*args, **kwargs):
        if 'user_id' not in session:
            return redirect(url_for('web_auth.login'))
        return f(*args, **kwargs)
    
    return decorated


@web_auth_bp.route("/login", methods=["GET", "POST"])
def login():
    """
    Login page and authentication.
    GET: Show login form
    POST: Authenticate user
    """
    error = None
    
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "").strip()
        
        if not username or not password:
            error = "Kullanıcı adı ve şifre gereklidir."
            return render_template("login.html", error=error)
        
        # Authenticate user
        db_session = get_db_session()
        user = queries.authenticate_user(db_session, username, password)
        db_session.close()
        
        if not user:
            error = "Geçersiz kullanıcı adı veya şifre."
            return render_template("login.html", error=error)
        
        # Create session - explicitly set values
        session['user_id'] = user.Kullanici_ID
        session['username'] = user.Kullanici_Adi
        session['user_name'] = user.Adi_Soyadi
        session['user_email'] = user.Email
        session.permanent = request.form.get("remember") == "on"
        session.modified = True  # Ensure session is saved
        
        return redirect(url_for('web_auth.dashboard'))
    
    return render_template("login.html", error=error)


@web_auth_bp.route("/dashboard")
@login_required
def dashboard():
    """
    Dashboard/menu page.
    Shows system statistics and navigation menu.
    """
    db_session = get_db_session()
    
    # Get current user
    user = queries.get_kullanici_by_id(db_session, session['user_id'])
    
    if not user:
        db_session.close()
        return redirect(url_for('web_auth.login'))
    
    # Get statistics
    try:
        kategoriler = ref_queries.get_kategoriler(db_session, limit=1000, aktif_only=False)
        suber = ref_queries.get_suber(db_session, limit=1000)
        kullanicilar = ref_queries.get_kullanicilar(db_session, limit=1000, aktif_only=False)
        degerler = ref_queries.get_degerler(db_session, limit=1000)
        
        stats = {
            'kategori_count': len(kategoriler),
            'sube_count': len(suber),
            'kullanici_count': len(kullanicilar),
            'deger_count': len(degerler),
        }
    except Exception as e:
        stats = {
            'kategori_count': 0,
            'sube_count': 0,
            'kullanici_count': 0,
            'deger_count': 0,
        }
    
    db_session.close()
    
    return render_template(
        "dashboard.html",
        user=user,
        stats=stats,
        suber=suber
    )


@web_auth_bp.route("/logout", methods=["GET", "POST"])
def logout():
    """
    Logout - clear session and redirect to login.
    Supports both GET and POST methods.
    """
    session.clear()
    return redirect(url_for('web_auth.login'))


@web_auth_bp.route("/")
def index():
    """
    Root route - redirect to dashboard if logged in, else login.
    """
    if 'user_id' in session:
        return redirect(url_for('web_auth.dashboard'))
    return redirect(url_for('web_auth.login'))
