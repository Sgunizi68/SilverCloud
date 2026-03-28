"""
SilverCloud Application Package
2-layer architecture: Application Layer + Database Layer
Organized by business domain, not technical layers.
"""

from flask import Flask
from flask_session import Session


def create_app(config_name: str = "development") -> Flask:
    """
    Application factory for creating Flask app instances.
    
    Args:
        config_name: Configuration environment ('development', 'testing', 'production')
    
    Returns:
        Configured Flask application instance
    """
    app = Flask(__name__, template_folder='templates')
    
    # Load configuration
    from app.config import get_config
    app.config.from_object(get_config(config_name))
    
    # Initialize database
    from app.common.database import db
    db.init_app(app)
    
    # Initialize Flask-Session for web-based session management
    Session(app)
    
    # Import models to register them with SQLAlchemy
    from app.models import (
        Sube, Kullanici, Rol, Yetki, KullaniciRol, RolYetki,
        Deger, UstKategori, Kategori,
        EFatura, B2BEkstre, DigerHarcama, Odeme, OdemeReferans, RobotposGelirReferans, RobotposGelir,
        Nakit, EFaturaReferans, POSHareketleri,
        Gelir, GelirEkstra,
        Stok, StokFiyat, StokSayim,
        Calisan, PuantajSecimi, Puantaj, AvansIstek, CalisanTalep,
        YemekCeki, Cari, Mutabakat,
    )
    
    # Create tables on app context
    with app.app_context():
        db.create_all()
    
    # Register blueprints (modules)   
    from app.modules.auth import auth_bp, web_auth_bp
    from app.modules.reference import reference_bp
    from app.modules.reference.web_routes import web_reference_bp
    from app.modules.invoicing import invoicing_bp
    from app.modules.invoicing.web_routes import web_invoicing_bp
    from app.modules.inventory import inventory_bp, web_inventory_bp
    from app.modules.hr import hr_bp, web_hr_bp
    from app.modules.reports import reports_bp
    
    app.register_blueprint(auth_bp)
    app.register_blueprint(web_auth_bp)
    app.register_blueprint(reference_bp)
    app.register_blueprint(web_reference_bp)
    app.register_blueprint(invoicing_bp)
    app.register_blueprint(web_invoicing_bp)
    app.register_blueprint(inventory_bp)
    app.register_blueprint(web_inventory_bp)
    app.register_blueprint(hr_bp)
    app.register_blueprint(web_hr_bp)
    app.register_blueprint(reports_bp)
    # Custom filters
    @app.template_filter('date_day_of_week')
    def date_day_of_week(val):
        """Returns 1-7 for day of week. Sunday is 0."""
        from datetime import date
        if isinstance(val, date):
            return (val.weekday() + 1) % 7
        if isinstance(val, tuple) and len(val) == 3:
            y, m, d = val
            return (date(y, m, d).weekday() + 1) % 7
        return 0

    @app.context_processor
    def inject_version():
        from app.config import get_app_version
        return dict(app_version=get_app_version())

    return app
