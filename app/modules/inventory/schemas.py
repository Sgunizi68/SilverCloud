"""
Inventory Domain Schemas
Dataclass-based request/response validation for Stock management.
"""

from dataclasses import dataclass, asdict
from typing import Optional
from datetime import date, datetime
from decimal import Decimal


# ============================================================================
# STOK (STOCK) SCHEMAS
# ============================================================================

@dataclass
class StokCreate:
    """Request schema for creating stock item."""
    Urun_Grubu: str
    Malzeme_Kodu: str
    Malzeme_Aciklamasi: str
    Birimi: str
    Sinif: Optional[str] = None
    Aktif_Pasif: bool = True


@dataclass
class StokUpdate:
    """Request schema for updating stock item."""
    Urun_Grubu: Optional[str] = None
    Malzeme_Aciklamasi: Optional[str] = None
    Birimi: Optional[str] = None
    Sinif: Optional[str] = None
    Aktif_Pasif: Optional[bool] = None


@dataclass
class StokResponse:
    """Response schema for stock item."""
    Stok_ID: int
    Urun_Grubu: str
    Malzeme_Kodu: str
    Malzeme_Aciklamasi: str
    Birimi: str
    Sinif: Optional[str]
    Aktif_Pasif: bool


# ============================================================================
# STOK FIYAT (STOCK PRICE) SCHEMAS
# ============================================================================

@dataclass
class StokFiyatCreate:
    """Request schema for creating stock price."""
    Malzeme_Kodu: str
    Fiyat: float
    Sube_ID: int
    Gecerlilik_Baslangic_Tarih: Optional[str] = None  # ISO date
    Aktif_Pasif: bool = True


@dataclass
class StokFiyatUpdate:
    """Request schema for updating stock price."""
    Fiyat: Optional[float] = None
    Aktif_Pasif: Optional[bool] = None


@dataclass
class StokFiyatResponse:
    """Response schema for stock price."""
    Fiyat_ID: int
    Malzeme_Kodu: str
    Gecerlilik_Baslangic_Tarih: str  # ISO date
    Fiyat: str  # Decimal as string
    Sube_ID: int
    Aktif_Pasif: bool


# ============================================================================
# STOK SAYIM (STOCK COUNT) SCHEMAS
# ============================================================================

@dataclass
class StokSayimCreate:
    """Request schema for creating stock count."""
    Malzeme_Kodu: str
    Donem: int  # YYMM format
    Miktar: float
    Sube_ID: int
    Kayit_Tarihi: Optional[str] = None  # ISO datetime


@dataclass
class StokSayimUpdate:
    """Request schema for updating stock count."""
    Miktar: Optional[float] = None


@dataclass
class StokSayimResponse:
    """Response schema for stock count."""
    Sayim_ID: int
    Malzeme_Kodu: str
    Donem: int
    Miktar: str  # Decimal as string
    Sube_ID: int
    Kayit_Tarihi: str  # ISO datetime
