"""
Invoicing Domain Request/Response Schemas
Dataclass-based validation for invoicing operations
"""

from dataclasses import dataclass, asdict
from typing import Optional
from datetime import date


# ============================================================================
# EFATURA (E-INVOICES) SCHEMAS
# ============================================================================

@dataclass
class EFaturaCreate:
    """Request schema for creating an e-invoice."""
    Sube_ID: int
    Kategori_ID: int
    Fatura_No: str
    Fatura_Tutari: float
    Kayit_Tarihi: Optional[str] = None  # ISO date string
    Aciklama: Optional[str] = None

    def to_dict(self):
        return asdict(self)


@dataclass
class EFaturaUpdate:
    """Request schema for updating an e-invoice."""
    Fatura_No: Optional[str] = None
    Fatura_Tutari: Optional[float] = None
    Durum: Optional[str] = None
    Aciklama: Optional[str] = None

    def to_dict(self):
        return {k: v for k, v in asdict(self).items() if v is not None}


@dataclass
class EFaturaResponse:
    """Response schema for e-invoice."""
    EFatura_ID: int
    Sube_ID: int
    Kategori_ID: int
    Fatura_No: str
    Fatura_Tutari: float
    Kayit_Tarihi: str
    Durum: str
    Aciklama: Optional[str]

    def to_dict(self):
        return asdict(self)


# ============================================================================
# ODEME (PAYMENTS) SCHEMAS
# ============================================================================

@dataclass
class OdemeCreate:
    """Request schema for creating a payment."""
    Sube_ID: int
    Kategori_ID: int
    Odeme_Tutari: float
    Odeme_Tarihi: Optional[str] = None  # ISO date string
    Odeme_Sekli: str = "Nakit"
    Aciklama: Optional[str] = None

    def to_dict(self):
        return asdict(self)


@dataclass
class OdemeUpdate:
    """Request schema for updating a payment."""
    Odeme_Tutari: Optional[float] = None
    Odeme_Sekli: Optional[str] = None
    Durum: Optional[str] = None
    Aciklama: Optional[str] = None

    def to_dict(self):
        return {k: v for k, v in asdict(self).items() if v is not None}


@dataclass
class OdemeResponse:
    """Response schema for payment."""
    Odeme_ID: int
    Sube_ID: int
    Kategori_ID: int
    Odeme_Tutari: float
    Odeme_Tarihi: str
    Odeme_Sekli: str
    Durum: str
    Aciklama: Optional[str]

    def to_dict(self):
        return asdict(self)


# ============================================================================
# NAKIT (CASH) SCHEMAS
# ============================================================================

@dataclass
class NakitCreate:
    """Request schema for creating a cash transaction."""
    Sube_ID: int
    Kategori_ID: int
    Islem_Tutari: float
    Islem_Sekli: str
    Islem_Tarihi: Optional[str] = None  # ISO date string
    Aciklama: Optional[str] = None

    def to_dict(self):
        return asdict(self)


@dataclass
class NakitUpdate:
    """Request schema for updating a cash transaction."""
    Islem_Tutari: Optional[float] = None
    Islem_Sekli: Optional[str] = None
    Aciklama: Optional[str] = None

    def to_dict(self):
        return {k: v for k, v in asdict(self).items() if v is not None}


@dataclass
class NakitResponse:
    """Response schema for cash transaction."""
    Nakit_ID: int
    Sube_ID: int
    Kategori_ID: int
    Islem_Tutari: float
    Islem_Sekli: str
    Islem_Tarihi: str
    Aciklama: Optional[str]

    def to_dict(self):
        return asdict(self)


# ============================================================================
# GELIR (INCOME) SCHEMAS
# ============================================================================

@dataclass
class GelirCreate:
    """Request schema for creating income."""
    Sube_ID: int
    Kategori_ID: int
    Gelir_Tutari: float
    Kayit_Tarihi: Optional[str] = None  # ISO date string
    Aciklama: Optional[str] = None

    def to_dict(self):
        return asdict(self)


@dataclass
class GelirUpdate:
    """Request schema for updating income."""
    Gelir_Tutari: Optional[float] = None
    Aciklama: Optional[str] = None

    def to_dict(self):
        return {k: v for k, v in asdict(self).items() if v is not None}


@dataclass
class GelirResponse:
    """Response schema for income."""
    Gelir_ID: int
    Sube_ID: int
    Kategori_ID: int
    Gelir_Tutari: float
    Kayit_Tarihi: str
    Aciklama: Optional[str]

    def to_dict(self):
        return asdict(self)


# ============================================================================
# DIGER HARCAMA (OTHER EXPENSES) SCHEMAS
# ============================================================================

@dataclass
class DigerHarcamaCreate:
    """Request schema for creating other expense."""
    Sube_ID: int
    Harcama_Adi: str
    Harcama_Tutari: float
    Kayit_Tarihi: Optional[str] = None  # ISO date string
    Aciklama: Optional[str] = None

    def to_dict(self):
        return asdict(self)


@dataclass
class DigerHarcamaUpdate:
    """Request schema for updating other expense."""
    Harcama_Adi: Optional[str] = None
    Harcama_Tutari: Optional[float] = None
    Aciklama: Optional[str] = None

    def to_dict(self):
        return {k: v for k, v in asdict(self).items() if v is not None}


@dataclass
class DigerHarcamaResponse:
    """Response schema for other expense."""
    DigerHarcama_ID: int
    Sube_ID: int
    Harcama_Adi: str
    Harcama_Tutari: float
    Kayit_Tarihi: str
    Aciklama: Optional[str]

    def to_dict(self):
        return asdict(self)


# ============================================================================
# POSHAREKETLERİ (POS TRANSACTIONS) SCHEMAS
# ============================================================================

@dataclass
class POSHareketiCreate:
    """Request schema for creating POS transaction."""
    Sube_ID: int
    Islem_Tutari: float
    Pos_Adi: str
    Islem_Tarihi: Optional[str] = None  # ISO date string
    Aciklama: Optional[str] = None

    def to_dict(self):
        return asdict(self)


@dataclass
class POSHareketiUpdate:
    """Request schema for updating POS transaction."""
    Islem_Tutari: Optional[float] = None
    Pos_Adi: Optional[str] = None
    Aciklama: Optional[str] = None

    def to_dict(self):
        return {k: v for k, v in asdict(self).items() if v is not None}


@dataclass
class POSHareketiResponse:
    """Response schema for POS transaction."""
    POSHareketleri_ID: int
    Sube_ID: int
    Islem_Tutari: float
    Pos_Adi: str
    Islem_Tarihi: str
    Aciklama: Optional[str]

    def to_dict(self):
        return asdict(self)
