"""
HR Domain Schemas
Dataclass-based request/response validation for Employee management.
"""

from dataclasses import dataclass
from typing import Optional
from datetime import date, datetime


# ============================================================================
# CALISAN (EMPLOYEE) SCHEMAS
# ============================================================================

@dataclass
class CalisanCreate:
    """Request schema for creating employee."""
    TC_No: str
    Adi: str
    Soyadi: str
    Sube_ID: int
    Hesap_No: Optional[str] = None
    IBAN: Optional[str] = None
    Net_Maas: Optional[float] = None
    Sigorta_Giris: Optional[str] = None  # ISO date
    Sigorta_Cikis: Optional[str] = None  # ISO date
    Aktif_Pasif: bool = True


@dataclass
class CalisanUpdate:
    """Request schema for updating employee."""
    Adi: Optional[str] = None
    Soyadi: Optional[str] = None
    Hesap_No: Optional[str] = None
    IBAN: Optional[str] = None
    Net_Maas: Optional[float] = None
    Sigorta_Cikis: Optional[str] = None  # ISO date
    Aktif_Pasif: Optional[bool] = None


@dataclass
class CalisanResponse:
    """Response schema for employee."""
    TC_No: str
    Adi: str
    Soyadi: str
    Hesap_No: Optional[str]
    IBAN: Optional[str]
    Net_Maas: Optional[str]  # Decimal as string
    Sigorta_Giris: Optional[str]  # ISO date
    Sigorta_Cikis: Optional[str]  # ISO date
    Aktif_Pasif: bool
    Sube_ID: int


# ============================================================================
# PUANTAJ SECIMI (ATTENDANCE TYPE) SCHEMAS
# ============================================================================

@dataclass
class PuantajSec imCreate:
    """Request schema for creating attendance type."""
    Secim: str
    Degeri: float
    Renk_Kodu: str
    Aktif_Pasif: bool = True


@dataclass
class PuantajSecimUpdate:
    """Request schema for updating attendance type."""
    Secim: Optional[str] = None
    Degeri: Optional[float] = None
    Renk_Kodu: Optional[str] = None
    Aktif_Pasif: Optional[bool] = None


@dataclass
class PuantajSecimResponse:
    """Response schema for attendance type."""
    Secim_ID: int
    Secim: str
    Degeri: str  # Decimal as string
    Renk_Kodu: str
    Aktif_Pasif: bool


# ============================================================================
# PUANTAJ (ATTENDANCE) SCHEMAS
# ============================================================================

@dataclass
class PuantajCreate:
    """Request schema for creating attendance record."""
    TC_No: str
    Secim_ID: int
    Sube_ID: int
    Tarih: Optional[str] = None  # ISO date
    Kayit_Tarihi: Optional[str] = None  # ISO datetime


@dataclass
class PuantajUpdate:
    """Request schema for updating attendance record."""
    Secim_ID: Optional[int] = None
    Tarih: Optional[str] = None  # ISO date


@dataclass
class PuantajResponse:
    """Response schema for attendance record."""
    Puantaj_ID: int
    Tarih: str  # ISO date
    TC_No: str
    Secim_ID: int
    Sube_ID: int
    Kayit_Tarihi: str  # ISO datetime


# ============================================================================
# AVANS ISTEK (ADVANCE REQUEST) SCHEMAS
# ============================================================================

@dataclass
class AvansIstekCreate:
    """Request schema for creating advance request."""
    TC_No: str
    Sube_ID: int
    Donem: int  # YYMM format
    Tutar: float
    Aciklama: Optional[str] = None
    Kayit_Tarihi: Optional[str] = None  # ISO datetime


@dataclass
class AvansIstekUpdate:
    """Request schema for updating advance request."""
    Tutar: Optional[float] = None
    Aciklama: Optional[str] = None


@dataclass
class AvansIstekResponse:
    """Response schema for advance request."""
    Avans_ID: int
    Donem: int
    TC_No: str
    Tutar: str  # Decimal as string
    Aciklama: Optional[str]
    Sube_ID: int
    Kayit_Tarihi: str  # ISO datetime


# ============================================================================
# CALISAN TALEP (EMPLOYEE REQUEST) SCHEMAS
# ============================================================================

@dataclass
class CalisanTalepCreate:
    """Request schema for creating employee request."""
    TC_No: str
    Adi: str
    Soyadi: str
    Ilk_Soyadi: str
    Sube_ID: int
    Talep: str = "İşe Giriş"
    Hesap_No: Optional[str] = None
    IBAN: Optional[str] = None
    Ogrenim_Durumu: Optional[str] = None
    Cinsiyet: str = "Erkek"
    Gorevi: Optional[str] = None
    Anne_Adi: Optional[str] = None
    Baba_Adi: Optional[str] = None
    Dogum_Yeri: Optional[str] = None
    Dogum_Tarihi: Optional[str] = None  # ISO date
    Medeni_Hali: str = "Bekar"
    Cep_No: Optional[str] = None
    Adres_Bilgileri: Optional[str] = None
    Gelir_Vergisi_Matrahi: Optional[float] = None
    SSK_Cikis_Nedeni: Optional[str] = None
    Net_Maas: Optional[float] = None
    Sigorta_Giris: Optional[str] = None  # ISO date
    Sigorta_Cikis: Optional[str] = None  # ISO date


@dataclass
class CalisanTalepUpdate:
    """Request schema for updating employee request."""
    Adi: Optional[str] = None
    Soyadi: Optional[str] = None
    Hesap_No: Optional[str] = None
    IBAN: Optional[str] = None
    Net_Maas: Optional[float] = None
    Sigorta_Cikis: Optional[str] = None  # ISO date


@dataclass
class CalisanTalepResponse:
    """Response schema for employee request."""
    Calisan_Talep_ID: int
    Talep: str
    TC_No: str
    Adi: str
    Soyadi: str
    Ilk_Soyadi: str
    Sube_ID: int
    Hesap_No: Optional[str]
    IBAN: Optional[str]
    Net_Maas: Optional[str]  # Decimal as string
    Sigorta_Giris: Optional[str]  # ISO date
    Sigorta_Cikis: Optional[str]  # ISO date
    Kayit_Tarih: str  # ISO datetime
