"""
Inventory Domain Query Functions
CRUD operations for Stock, Stock Price, and Stock Count entities.
"""

from datetime import datetime, date
from decimal import Decimal
from typing import List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import select

from app.models import Stok, StokFiyat, StokSayim


# ============================================================================
# STOK (STOCK) QUERIES
# ============================================================================

def get_stoklar(
    db: Session, 
    skip: int = 0, 
    limit: int = 100,
    urun_grubu: Optional[str] = None,
    malzeme_kodu: Optional[str] = None,
    aktif_pasif: Optional[bool] = None
) -> List[Stok]:
    """
    Get all stock items with optional filtering.
    
    Args:
        db: Database session
        skip: Number of records to skip (pagination)
        limit: Maximum number of records to return (max 1000)
        urun_grubu: Filter by product group
        malzeme_kodu: Filter by material code
        aktif_pasif: Filter by active/passive status
    
    Returns:
        List of Stok records
    """
    limit = min(limit, 1000)
    stmt = select(Stok)
    
    if urun_grubu is not None:
        stmt = stmt.where(Stok.Urun_Grubu == urun_grubu)
    if malzeme_kodu is not None:
        stmt = stmt.where(Stok.Malzeme_Kodu == malzeme_kodu)
    if aktif_pasif is not None:
        stmt = stmt.where(Stok.Aktif_Pasif == aktif_pasif)
    
    return db.scalars(stmt.offset(skip).limit(limit)).all()


def get_stok_by_id(db: Session, stok_id: int) -> Optional[Stok]:
    """Get stock item by ID."""
    return db.query(Stok).filter(Stok.Stok_ID == stok_id).first()


def get_stok_by_malzeme_kodu(db: Session, malzeme_kodu: str) -> Optional[Stok]:
    """Get stock item by material code."""
    return db.query(Stok).filter(Stok.Malzeme_Kodu == malzeme_kodu).first()


def create_stok(
    db: Session,
    urun_grubu: str,
    malzeme_kodu: str,
    malzeme_aciklamasi: str,
    birimi: str,
    sinif: Optional[str] = None,
    aktif_pasif: bool = True
) -> Stok:
    """Create a new stock item."""
    new_stok = Stok(
        Urun_Grubu=urun_grubu,
        Malzeme_Kodu=malzeme_kodu,
        Malzeme_Aciklamasi=malzeme_aciklamasi,
        Birimi=birimi,
        Sinif=sinif,
        Aktif_Pasif=aktif_pasif
    )
    db.add(new_stok)
    db.commit()
    db.refresh(new_stok)
    return new_stok


def update_stok(
    db: Session,
    stok_id: int,
    urun_grubu: Optional[str] = None,
    malzeme_aciklamasi: Optional[str] = None,
    birimi: Optional[str] = None,
    sinif: Optional[str] = None,
    aktif_pasif: Optional[bool] = None
) -> Optional[Stok]:
    """Update stock item."""
    stok = get_stok_by_id(db, stok_id)
    if not stok:
        return None
    
    if urun_grubu is not None:
        stok.Urun_Grubu = urun_grubu
    if malzeme_aciklamasi is not None:
        stok.Malzeme_Aciklamasi = malzeme_aciklamasi
    if birimi is not None:
        stok.Birimi = birimi
    if sinif is not None:
        stok.Sinif = sinif
    if aktif_pasif is not None:
        stok.Aktif_Pasif = aktif_pasif
    
    db.commit()
    db.refresh(stok)
    return stok


def delete_stok(db: Session, stok_id: int) -> bool:
    """Delete stock item."""
    stok = get_stok_by_id(db, stok_id)
    if not stok:
        return False
    
    db.delete(stok)
    db.commit()
    return True


# ============================================================================
# STOK FIYAT (STOCK PRICE) QUERIES
# ============================================================================

def get_stok_fiyatlar(
    db: Session,
    skip: int = 0,
    limit: int = 100,
    malzeme_kodu: Optional[str] = None,
    sube_id: Optional[int] = None,
    aktif_pasif: Optional[bool] = None,
    baslangic_tarihinden: Optional[date] = None,
    baslangic_tarihine: Optional[date] = None
) -> List[StokFiyat]:
    """
    Get all stock prices with optional filtering.
    
    Args:
        db: Database session
        skip: Number of records to skip (pagination)
        limit: Maximum number of records to return (max 1000)
        malzeme_kodu: Filter by material code
        sube_id: Filter by branch
        aktif_pasif: Filter by active/passive status
        baslangic_tarihinden: Filter start date from
        baslangic_tarihine: Filter start date to
    
    Returns:
        List of StokFiyat records
    """
    limit = min(limit, 1000)
    stmt = select(StokFiyat)
    
    if malzeme_kodu is not None:
        stmt = stmt.where(StokFiyat.Malzeme_Kodu == malzeme_kodu)
    if sube_id is not None:
        stmt = stmt.where(StokFiyat.Sube_ID == sube_id)
    if aktif_pasif is not None:
        stmt = stmt.where(StokFiyat.Aktif_Pasif == aktif_pasif)
    if baslangic_tarihinden is not None:
        stmt = stmt.where(StokFiyat.Gecerlilik_Baslangic_Tarih >= baslangic_tarihinden)
    if baslangic_tarihine is not None:
        stmt = stmt.where(StokFiyat.Gecerlilik_Baslangic_Tarih <= baslangic_tarihine)
    
    return db.scalars(stmt.offset(skip).limit(limit)).all()


def get_stok_fiyat_by_id(db: Session, fiyat_id: int) -> Optional[StokFiyat]:
    """Get stock price by ID."""
    return db.query(StokFiyat).filter(StokFiyat.Fiyat_ID == fiyat_id).first()


def create_stok_fiyat(
    db: Session,
    malzeme_kodu: str,
    gecerlilik_baslangic_tarih: Optional[date] = None,
    fiyat: float = 0.0,
    sube_id: int = 0,
    aktif_pasif: bool = True
) -> StokFiyat:
    """Create a new stock price."""
    if gecerlilik_baslangic_tarih is None:
        gecerlilik_baslangic_tarih = datetime.now().date()
    
    new_fiyat = StokFiyat(
        Malzeme_Kodu=malzeme_kodu,
        Gecerlilik_Baslangic_Tarih=gecerlilik_baslangic_tarih,
        Fiyat=Decimal(str(fiyat)),
        Sube_ID=sube_id,
        Aktif_Pasif=aktif_pasif
    )
    db.add(new_fiyat)
    db.commit()
    db.refresh(new_fiyat)
    return new_fiyat


def update_stok_fiyat(
    db: Session,
    fiyat_id: int,
    fiyat: Optional[float] = None,
    aktif_pasif: Optional[bool] = None
) -> Optional[StokFiyat]:
    """Update stock price."""
    stok_fiyat = get_stok_fiyat_by_id(db, fiyat_id)
    if not stok_fiyat:
        return None
    
    if fiyat is not None:
        stok_fiyat.Fiyat = Decimal(str(fiyat))
    if aktif_pasif is not None:
        stok_fiyat.Aktif_Pasif = aktif_pasif
    
    db.commit()
    db.refresh(stok_fiyat)
    return stok_fiyat


def delete_stok_fiyat(db: Session, fiyat_id: int) -> bool:
    """Delete stock price."""
    stok_fiyat = get_stok_fiyat_by_id(db, fiyat_id)
    if not stok_fiyat:
        return False
    
    db.delete(stok_fiyat)
    db.commit()
    return True


# ============================================================================
# STOK SAYIM (STOCK COUNT) QUERIES
# ============================================================================

def get_stok_sayimlar(
    db: Session,
    skip: int = 0,
    limit: int = 100,
    malzeme_kodu: Optional[str] = None,
    sube_id: Optional[int] = None,
    donem: Optional[int] = None,
    donemden: Optional[int] = None,
    doneme: Optional[int] = None
) -> List[StokSayim]:
    """
    Get all stock counts with optional filtering.
    
    Args:
        db: Database session
        skip: Number of records to skip (pagination)
        limit: Maximum number of records to return (max 1000)
        malzeme_kodu: Filter by material code
        sube_id: Filter by branch
        donem: Filter by specific period (YYMM format)
        donemden: Filter period from
        doneme: Filter period to
    
    Returns:
        List of StokSayim records
    """
    limit = min(limit, 1000)
    stmt = select(StokSayim)
    
    if malzeme_kodu is not None:
        stmt = stmt.where(StokSayim.Malzeme_Kodu == malzeme_kodu)
    if sube_id is not None:
        stmt = stmt.where(StokSayim.Sube_ID == sube_id)
    if donem is not None:
        stmt = stmt.where(StokSayim.Donem == donem)
    if donemden is not None:
        stmt = stmt.where(StokSayim.Donem >= donemden)
    if doneme is not None:
        stmt = stmt.where(StokSayim.Donem <= doneme)
    
    return db.scalars(stmt.offset(skip).limit(limit)).all()


def get_stok_sayim_by_id(db: Session, sayim_id: int) -> Optional[StokSayim]:
    """Get stock count by ID."""
    return db.query(StokSayim).filter(StokSayim.Sayim_ID == sayim_id).first()


def create_stok_sayim(
    db: Session,
    malzeme_kodu: str,
    donem: int,
    miktar: float,
    sube_id: int,
    kayit_tarihi: Optional[datetime] = None
) -> StokSayim:
    """Create a new stock count."""
    if kayit_tarihi is None:
        kayit_tarihi = datetime.now()
    
    new_sayim = StokSayim(
        Malzeme_Kodu=malzeme_kodu,
        Donem=donem,
        Miktar=Decimal(str(miktar)),
        Sube_ID=sube_id,
        Kayit_Tarihi=kayit_tarihi
    )
    db.add(new_sayim)
    db.commit()
    db.refresh(new_sayim)
    return new_sayim


def update_stok_sayim(
    db: Session,
    sayim_id: int,
    miktar: Optional[float] = None
) -> Optional[StokSayim]:
    """Update stock count."""
    stok_sayim = get_stok_sayim_by_id(db, sayim_id)
    if not stok_sayim:
        return None
    
    if miktar is not None:
        stok_sayim.Miktar = Decimal(str(miktar))
    
    db.commit()
    db.refresh(stok_sayim)
    return stok_sayim


def delete_stok_sayim(db: Session, sayim_id: int) -> bool:
    """Delete stock count."""
    stok_sayim = get_stok_sayim_by_id(db, sayim_id)
    if not stok_sayim:
        return False
    
    db.delete(stok_sayim)
    db.commit()
    return True
