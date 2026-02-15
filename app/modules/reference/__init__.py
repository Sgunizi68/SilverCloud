"""
Reference Domain Module
Handles CRUD operations for reference data (Kategoriler, Degerler, Sube, Kullanici, etc.)
"""

from app.modules.reference.routes import reference_bp

__all__ = ["reference_bp"]
