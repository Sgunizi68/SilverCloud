"""
Authentication Web Routes (Server-Rendered)
Login, dashboard, and logout pages using Jinja2 templates.
"""

from flask import Blueprint, request, render_template, redirect, url_for, session
from app.common.database import get_db_session
from app.modules.auth import security, queries
from app.modules.reference import queries as ref_queries
from app.common.decorators import permission_required

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


@web_auth_bp.route("/forgot-password", methods=["GET", "POST"])
def forgot_password():
    """
    Şifre Sıfırlama:
    Kullanıcı adı veya e-posta girildiğinde yeni güvenli şifre üretir,
    kullanıcının şifresini günceller ve yeni şifreyi kullanıcının e-posta adresine gönderir.
    """
    error = None
    message = None
    
    if request.method == "POST":
        identifier = request.form.get("username_or_email", "").strip()
        if not identifier:
            error = "Lütfen kullanıcı adı veya e-posta adresinizi giriniz."
            return render_template("login.html", error=error, show_forgot_modal=True)
            
        db_session = get_db_session()
        user = queries.get_kullanici_by_username_or_email(db_session, identifier)
        
        if not user:
            db_session.close()
            error = "Bu kullanıcı adı veya e-posta adresine ait hesap bulunamadı."
            return render_template("login.html", error=error, show_forgot_modal=True)
            
        if not user.Email or "@" not in user.Email:
            db_session.close()
            error = f"'{user.Kullanici_Adi}' kullanıcısına tanımlı geçerli bir e-posta adresi bulunmuyor. Lütfen sistem yöneticiniz ile iletişime geçiniz."
            return render_template("login.html", error=error, show_forgot_modal=True)
            
        # Yeni rastgele şifre üret
        import secrets
        import string
        letters = string.ascii_letters
        digits = string.digits
        # 8 karakterlik güçlü şifre (harf ve rakam kombinasyonu)
        new_password = "".join(secrets.choice(letters + digits) for _ in range(8))
        new_hash = security.get_password_hash(new_password)
        
        # Veritabanında güncelle
        queries.update_user_password(db_session, user.Kullanici_ID, new_hash)
        recipient_email = user.Email
        user_name = user.Adi_Soyadi or user.Kullanici_Adi
        db_session.close()
        
        # E-posta içeriği
        from app.common.mail import send_email
        subject = "SilverCloud - Yeni Şifreniz"
        text_body = f"""Merhaba {user_name},

SilverCloud hesabınız için yeni şifreniz başarıyla oluşturuldu.

Kullanıcı Adı: {user.Kullanici_Adi}
Yeni Şifre: {new_password}

Güvenliğiniz için sisteme giriş yaptıktan sonra şifrenizi değiştirmenizi tavsiye ederiz.

Saygılarımızla,
SilverCloud Ekibi
"""
        html_body = f"""
        <div style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif; max-width: 500px; margin: 0 auto; border: 1px solid #e2e8f0; border-radius: 12px; overflow: hidden; background: #ffffff;">
            <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: #ffffff; padding: 25px 20px; text-align: center;">
                <h2 style="margin: 0; font-size: 22px;">SilverCloud</h2>
                <p style="margin: 6px 0 0; font-size: 14px; opacity: 0.9;">Şifre Sıfırlama Bildirimi</p>
            </div>
            <div style="padding: 25px 20px; color: #334155;">
                <p style="font-size: 15px; margin-top: 0;">Merhaba <strong>{user_name}</strong>,</p>
                <p style="font-size: 14px; line-height: 1.5;">Hesabınız için şifre sıfırlama talebinde bulunuldu. Yeni giriş bilgileriniz aşağıdadır:</p>
                <div style="background: #f8fafc; border: 1px solid #cbd5e1; border-radius: 8px; padding: 15px; margin: 20px 0; text-align: center;">
                    <div style="font-size: 12px; color: #64748b; margin-bottom: 4px;">KULLANICI ADI</div>
                    <div style="font-size: 16px; font-weight: bold; color: #1e293b; margin-bottom: 12px;">{user.Kullanici_Adi}</div>
                    <div style="font-size: 12px; color: #64748b; margin-bottom: 4px;">YENİ ŞİFRENİZ</div>
                    <div style="font-size: 22px; font-weight: 800; font-family: monospace; color: #4338ca; letter-spacing: 2px;">{new_password}</div>
                </div>
                <p style="font-size: 13px; color: #64748b; line-height: 1.5;">Giriş yaptıktan sonra şifrenizi hatırlayabileceğiniz yeni bir şifre ile güncellemenizi öneririz.</p>
            </div>
            <div style="background: #f1f5f9; padding: 12px; text-align: center; font-size: 12px; color: #94a3b8; border-top: 1px solid #e2e8f0;">
                SilverCloud &copy; Tüm Hakları Saklıdır.
            </div>
        </div>
        """
        
        email_sent = send_email(to=recipient_email, subject=subject, body=text_body, html=html_body)
        
        # Masked email for security display (e.g., a***n@domain.com)
        parts = recipient_email.split("@")
        masked_email = recipient_email
        if len(parts) == 2:
            name_part, domain_part = parts
            if len(name_part) > 2:
                masked_email = f"{name_part[0]}***{name_part[-1]}@{domain_part}"
            else:
                masked_email = f"{name_part[0]}*@{domain_part}"
                
        if email_sent:
            message = f"Yeni şifreniz '{masked_email}' adresine gönderildi. Lütfen e-postanızı kontrol ediniz."
            return render_template("login.html", message=message)
        else:
            error = f"Şifreniz güncellendi ancak '{masked_email}' adresine e-posta gönderilirken bir sorun oluştu. Lütfen SMTP ayarlarını kontrol ediniz."
            return render_template("login.html", error=error)
            
    return redirect(url_for('web_auth.login'))



@web_auth_bp.route("/dashboard")
@login_required
@permission_required("Dashboard Ekranı Görüntüleme")
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
        # Branch authorization logic
        is_admin = False
        if user.Kullanici_Adi and user.Kullanici_Adi.lower() == 'admin':
            is_admin = True
        else:
            roles = queries.get_user_roles(db_session, user.Kullanici_ID)
            if 'admin' in [r.lower() for r in roles]:
                is_admin = True

        # Determine if user can view Gizli (hidden) categories
        has_gizli_permission = is_admin  # Admins always see everything
        if not is_admin:
            has_gizli_permission = queries.has_permission(
                db_session, user.Kullanici_ID, "Gizli Kategori Veri Erişimi"
            )

        kategoriler = ref_queries.get_kategoriler(
            db_session, limit=1000, aktif_only=False, can_view_gizli=has_gizli_permission
        )
        all_suber = ref_queries.get_suber(db_session, limit=1000)
        kullanicilar = ref_queries.get_kullanicilar(db_session, limit=1000, aktif_only=False)
        degerler = ref_queries.get_degerler(db_session, limit=1000)
        
        if is_admin:
            subeler = all_suber
        else:
            authorized_branch_ids = queries.get_user_branches(db_session, user.Kullanici_ID)
            subeler = [s for s in all_suber if s.Sube_ID in authorized_branch_ids]

        stats = {
            'kategori_count': len(kategoriler),
            'sube_count': len(subeler), # Should use filtered count or all branches? Used filtered.
            'kullanici_count': len(kullanicilar),
            'deger_count': len(degerler),
        }
    except Exception as e:
        subeler = []
        stats = {
            'kategori_count': 0,
            'sube_count': 0,
            'kullanici_count': 0,
            'deger_count': 0,
        }
    
    # Determine if user can view Gizli (hidden) categories
    has_gizli_permission = is_admin  # Admins always see everything
    if not is_admin:
        has_gizli_permission = queries.has_permission(
            db_session, user.Kullanici_ID, "Gizli Kategori Veri Erişimi"
        )
    db_session.close()
    
    return render_template(
        "dashboard.html",
        user=user,
        stats=stats,
        subeler=subeler,
        has_gizli_permission=has_gizli_permission
    )


@web_auth_bp.route("/logout", methods=["GET", "POST"])
def logout():
    """
    Logout - clear session and redirect to login.
    Supports both GET and POST methods.
    """
    session.clear()
    return redirect(url_for('web_auth.login'))


@web_auth_bp.route("/change-password", methods=["POST"])
@login_required
def change_password():
    """
    Şifre Değiştirme Endpoint'i:
    Kullanıcının mevcut şifresini doğrular, yeni şifreyi bcrypt ile hash'leyip günceller.
    """
    from flask import jsonify
    
    current_password = request.form.get("current_password", "").strip()
    new_password = request.form.get("new_password", "").strip()
    confirm_password = request.form.get("confirm_password", "").strip()
    
    if not current_password or not new_password or not confirm_password:
        return jsonify({"success": False, "message": "Lütfen tüm alanları doldurunuz."}), 400
        
    if new_password != confirm_password:
        return jsonify({"success": False, "message": "Yeni şifreler birbiriyle eşleşmiyor."}), 400
        
    if len(new_password) < 4:
        return jsonify({"success": False, "message": "Yeni şifre en az 4 karakter olmalıdır."}), 400
        
    db_session = get_db_session()
    user = queries.get_kullanici_by_id(db_session, session['user_id'])
    
    if not user:
        db_session.close()
        return jsonify({"success": False, "message": "Kullanıcı bulunamadı."}), 404
        
    # Mevcut şifreyi kontrol et
    if not security.verify_password(current_password, user.Password):
        db_session.close()
        return jsonify({"success": False, "message": "Mevcut şifreniz hatalı."}), 400
        
    # Yeni şifreyi hash'le ve kaydet
    new_hash = security.get_password_hash(new_password)
    queries.update_user_password(db_session, user.Kullanici_ID, new_hash)
    db_session.close()
    
    return jsonify({"success": True, "message": "Şifreniz başarıyla değiştirildi."})


@web_auth_bp.route("/")
def index():
    """
    Root route - redirect to dashboard if logged in, else login.
    """
    if 'user_id' in session:
        return redirect(url_for('web_auth.dashboard'))
    return redirect(url_for('web_auth.login'))

