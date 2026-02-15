"""
Reference Domain Request/Response Schemas
Dataclass-based validation (avoiding Pydantic dependency)
"""

from dataclasses import dataclass, asdict
from typing import Optional, List
from datetime import date


# ============================================================================
# SUBE (BRANCHES) SCHEMAS
# ============================================================================

@dataclass
class SubeCreate:
    """Request schema for creating a branch."""
    Sube_Adi: str
    Aciklama: Optional[str] = None

    def to_dict(self):
        return asdict(self)


@dataclass
class SubeUpdate:
    """Request schema for updating a branch."""
    Sube_Adi: Optional[str] = None
    Aciklama: Optional[str] = None
    Aktif_Pasif: Optional[bool] = None

    def to_dict(self):
        return {k: v for k, v in asdict(self).items() if v is not None}


@dataclass
class SubeResponse:
    """Response schema for branch."""
    Sube_ID: int
    Sube_Adi: str
    Aciklama: Optional[str]
    Aktif_Pasif: bool

    def to_dict(self):
        return asdict(self)


# ============================================================================
# KATEGORI (CATEGORIES) SCHEMAS
# ============================================================================

@dataclass
class KategoriCreate:
    """Request schema for creating a category."""
    Kategori_Adi: str
    Tip: str
    Ust_Kategori_ID: Optional[int] = None
    Gizli: bool = False

    def to_dict(self):
        return asdict(self)


@dataclass
class KategoriUpdate:
    """Request schema for updating a category."""
    Kategori_Adi: Optional[str] = None
    Tip: Optional[str] = None
    Ust_Kategori_ID: Optional[int] = None
    Aktif_Pasif: Optional[bool] = None
    Gizli: Optional[bool] = None

    def to_dict(self):
        return {k: v for k, v in asdict(self).items() if v is not None}


@dataclass
class KategoriResponse:
    """Response schema for category."""
    Kategori_ID: int
    Kategori_Adi: str
    Ust_Kategori_ID: Optional[int]
    Tip: str
    Aktif_Pasif: bool
    Gizli: bool

    def to_dict(self):
        return asdict(self)


# ============================================================================
# UST KATEGORI (PARENT CATEGORIES) SCHEMAS
# ============================================================================

@dataclass
class UstKategoriCreate:
    """Request schema for creating a parent category."""
    UstKategori_Adi: str

    def to_dict(self):
        return asdict(self)


@dataclass
class UstKategoriUpdate:
    """Request schema for updating a parent category."""
    UstKategori_Adi: Optional[str] = None
    Aktif_Pasif: Optional[bool] = None

    def to_dict(self):
        return {k: v for k, v in asdict(self).items() if v is not None}


@dataclass
class UstKategoriResponse:
    """Response schema for parent category."""
    UstKategori_ID: int
    UstKategori_Adi: str
    Aktif_Pasif: bool

    def to_dict(self):
        return asdict(self)


# ============================================================================
# DEGER (VALUES) SCHEMAS
# ============================================================================

@dataclass
class DegerCreate:
    """Request schema for creating a value."""
    Deger_Adi: str
    Gecerli_Baslangic_Tarih: str  # ISO date string
    Deger: float
    Gecerli_Bitis_Tarih: Optional[str] = None  # ISO date string
    Deger_Aciklama: Optional[str] = None

    def to_dict(self):
        return asdict(self)


@dataclass
class DegerUpdate:
    """Request schema for updating a value."""
    Deger_Adi: Optional[str] = None
    Gecerli_Baslangic_Tarih: Optional[str] = None
    Gecerli_Bitis_Tarih: Optional[str] = None
    Deger: Optional[float] = None
    Deger_Aciklama: Optional[str] = None

    def to_dict(self):
        return {k: v for k, v in asdict(self).items() if v is not None}


@dataclass
class DegerResponse:
    """Response schema for value."""
    Deger_ID: int
    Deger_Adi: str
    Gecerli_Baslangic_Tarih: str
    Gecerli_Bitis_Tarih: str
    Deger_Aciklama: Optional[str]
    Deger: float

    def to_dict(self):
        return asdict(self)


# ============================================================================
# KULLANICI (USERS) SCHEMAS
# ============================================================================

@dataclass
class KullaniciResponse:
    """Response schema for user."""
    Kullanici_ID: int
    Adi_Soyadi: str
    Kullanici_Adi: str
    Email: str
    Expire_Date: Optional[str]
    Aktif_Pasif: bool

    def to_dict(self):
        return asdict(self)
