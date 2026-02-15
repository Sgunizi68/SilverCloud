"""
SQLAlchemy ORM Models
Organized by business domain.
All models cleaned up from GumusBulut and optimized for SQLAlchemy 2.0.
"""

from app.common.database import db
from app.models.models import (
    Sube, Kullanici, Rol, Yetki, KullaniciRol, RolYetki,
    Deger, UstKategori, Kategori,
    EFatura, B2BEkstre, DigerHarcama, Odeme, OdemeReferans,
    Nakit, EFaturaReferans, POSHareketleri,
    Gelir, GelirEkstra,
    Stok, StokFiyat, StokSayim,
    Calisan, PuantajSecimi, Puantaj, AvansIstek, CalisanTalep,
    YemekCeki, Cari, Mutabakat,
)

__all__ = [
    "db",
    "Sube", "Kullanici", "Rol", "Yetki", "KullaniciRol", "RolYetki",
    "Deger", "UstKategori", "Kategori",
    "EFatura", "B2BEkstre", "DigerHarcama", "Odeme", "OdemeReferans",
    "Nakit", "EFaturaReferans", "POSHareketleri",
    "Gelir", "GelirEkstra",
    "Stok", "StokFiyat", "StokSayim",
    "Calisan", "PuantajSecimi", "Puantaj", "AvansIstek", "CalisanTalep",
    "YemekCeki", "Cari", "Mutabakat",
]
