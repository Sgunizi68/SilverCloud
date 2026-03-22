"""
Shared decorators for web routes.
Provides login_required and permission_required decorators that
enforce server-side access control on all page routes.
"""
from functools import wraps
from flask import session, redirect, url_for, request, render_template
from app.modules.auth import queries as auth_queries
from app.common.database import get_db_session


def login_required(f):
    """Redirect to login if user is not authenticated."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return redirect(url_for('web_auth.login', next=request.url))
        return f(*args, **kwargs)
    return decorated_function


def permission_required(permission_name: str):
    """
    Enforce that the logged-in user has the specified permission.

    Admins (by username or role) bypass the check.
    All others are checked against their assigned permissions.
    If access is denied, renders a 403 error page.
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if 'user_id' not in session:
                return redirect(url_for('web_auth.login', next=request.url))

            db = get_db_session()
            try:
                user = auth_queries.get_kullanici_by_id(db, session['user_id'])
                if not user:
                    return redirect(url_for('web_auth.login'))

                # Admins always have access
                is_admin = (user.Kullanici_Adi and user.Kullanici_Adi.lower() == 'admin')
                if not is_admin:
                    roles = auth_queries.get_user_roles(db, user.Kullanici_ID)
                    is_admin = 'admin' in [r.lower() for r in roles]

                if is_admin:
                    return f(*args, **kwargs)

                # Check specific permission
                has_perm = auth_queries.has_permission(db, user.Kullanici_ID, permission_name)
                if not has_perm:
                    return render_template(
                        '403.html',
                        user=user,
                        required_permission=permission_name
                    ), 403

                return f(*args, **kwargs)
            finally:
                db.close()

        return decorated_function
    return decorator
