"""
Reference Domain Database Queries
CRUD operations for Kategoriler, Degerler, Sube, UstKategori, and Kullanici.
Uses SQLAlchemy 2.0 style with pagination.
"""

from typing import Optional, List
from datetime import date
from sqlalchemy import select
from sqlalchemy.orm import Session
from app.models import (
    Kategori, UstKategori, Deger, Sube, Kullanici, KullaniciRol
)


# ============================================================================
# SUBE (BRANCHES) QUERIES
# ============================================================================

def get_suber(db: Session, skip: int = 0, limit: int = 100) -> List[Sube]:
    """Get all branches with pagination."""
    stmt = select(Sube).offset(skip).limit(limit)
    return db.scalars(stmt).all()


def get_sube_by_id(db: Session, sube_id: int) -> Optional[Sube]:
    """Get a branch by ID."""
    return db.get(Sube, sube_id)


def get_sube_by_name(db: Session, sube_adi: str) -> Optional[Sube]:
    """Get a branch by name."""
    stmt = select(Sube).where(Sube.Sube_Adi == sube_adi)
    return db.scalars(stmt).first()


def create_sube(db: Session, sube_adi: str, aciklama: Optional[str] = None) -> Sube:
    """Create a new branch."""
    new_sube = Sube(
        Sube_Adi=sube_adi,
        Aciklama=aciklama,
        Aktif_Pasif=True
    )
    db.add(new_sube)
    db.commit()
    db.refresh(new_sube)
    return new_sube


def update_sube(
    db: Session,
    sube_id: int,
    sube_adi: Optional[str] = None,
    aciklama: Optional[str] = None,
    aktif_pasif: Optional[bool] = None
) -> Optional[Sube]:
    """Update a branch."""
    sube = get_sube_by_id(db, sube_id)
    if not sube:
        return None
    
    if sube_adi is not None:
        sube.Sube_Adi = sube_adi
    if aciklama is not None:
        sube.Aciklama = aciklama
    if aktif_pasif is not None:
        sube.Aktif_Pasif = aktif_pasif
    
    db.commit()
    db.refresh(sube)
    return sube


def delete_sube(db: Session, sube_id: int) -> bool:
    """Delete a branch."""
    sube = get_sube_by_id(db, sube_id)
    if not sube:
        return False
    
    db.delete(sube)
    db.commit()
    return True


# ============================================================================
# UST KATEGORI (PARENT CATEGORIES) QUERIES
# ============================================================================

def get_ust_kategoriler(db: Session, skip: int = 0, limit: int = 100) -> List[UstKategori]:
    """Get all parent categories with pagination."""
    stmt = select(UstKategori).offset(skip).limit(limit)
    return db.scalars(stmt).all()


def get_ust_kategori_by_id(db: Session, ust_kategori_id: int) -> Optional[UstKategori]:
    """Get a parent category by ID."""
    return db.get(UstKategori, ust_kategori_id)


def get_ust_kategori_by_name(db: Session, adi: str) -> Optional[UstKategori]:
    """Get a parent category by name."""
    stmt = select(UstKategori).where(UstKategori.UstKategori_Adi == adi)
    return db.scalars(stmt).first()


def create_ust_kategori(db: Session, adi: str) -> UstKategori:
    """Create a new parent category."""
    new_ust_kategori = UstKategori(
        UstKategori_Adi=adi,
        Aktif_Pasif=True
    )
    db.add(new_ust_kategori)
    db.commit()
    db.refresh(new_ust_kategori)
    return new_ust_kategori


def update_ust_kategori(
    db: Session,
    ust_kategori_id: int,
    adi: Optional[str] = None,
    aktif_pasif: Optional[bool] = None
) -> Optional[UstKategori]:
    """Update a parent category."""
    ust_kategori = get_ust_kategori_by_id(db, ust_kategori_id)
    if not ust_kategori:
        return None
    
    if adi is not None:
        ust_kategori.UstKategori_Adi = adi
    if aktif_pasif is not None:
        ust_kategori.Aktif_Pasif = aktif_pasif
    
    db.commit()
    db.refresh(ust_kategori)
    return ust_kategori


def delete_ust_kategori(db: Session, ust_kategori_id: int) -> bool:
    """Delete a parent category."""
    ust_kategori = get_ust_kategori_by_id(db, ust_kategori_id)
    if not ust_kategori:
        return False
    
    db.delete(ust_kategori)
    db.commit()
    return True


# ============================================================================
# KATEGORI (CATEGORIES) QUERIES
# ============================================================================

def get_kategoriler(
    db: Session,
    skip: int = 0,
    limit: int = 100,
    ust_kategori_id: Optional[int] = None,
    tip: Optional[str] = None,
    aktif_only: bool = True
) -> List[Kategori]:
    """
    Get categories with optional filtering.
    
    Args:
        db: Database session
        skip: Pagination offset
        limit: Pagination limit
        ust_kategori_id: Filter by parent category
        tip: Filter by type (Gelir, Gider, Bilgi, Ödeme, Giden Fatura)
        aktif_only: Only return active categories
    
    Returns:
        List of Kategori objects
    """
    stmt = select(Kategori)
    
    if aktif_only:
        stmt = stmt.where(Kategori.Aktif_Pasif == True)
    
    if ust_kategori_id is not None:
        stmt = stmt.where(Kategori.Ust_Kategori_ID == ust_kategori_id)
    
    if tip is not None:
        stmt = stmt.where(Kategori.Tip == tip)
    
    stmt = stmt.offset(skip).limit(limit)
    return db.scalars(stmt).all()


def get_kategori_by_id(db: Session, kategori_id: int) -> Optional[Kategori]:
    """Get a category by ID."""
    return db.get(Kategori, kategori_id)


def get_kategori_by_name(db: Session, adi: str) -> Optional[Kategori]:
    """Get a category by name."""
    stmt = select(Kategori).where(Kategori.Kategori_Adi == adi)
    return db.scalars(stmt).first()


def create_kategori(
    db: Session,
    kategori_adi: str,
    tip: str,
    ust_kategori_id: Optional[int] = None,
    gizli: bool = False
) -> Kategori:
    """Create a new category."""
    new_kategori = Kategori(
        Kategori_Adi=kategori_adi,
        Tip=tip,
        Ust_Kategori_ID=ust_kategori_id,
        Aktif_Pasif=True,
        Gizli=gizli
    )
    db.add(new_kategori)
    db.commit()
    db.refresh(new_kategori)
    return new_kategori


def update_kategori(
    db: Session,
    kategori_id: int,
    kategori_adi: Optional[str] = None,
    tip: Optional[str] = None,
    ust_kategori_id: Optional[int] = None,
    aktif_pasif: Optional[bool] = None,
    gizli: Optional[bool] = None
) -> Optional[Kategori]:
    """Update a category."""
    kategori = get_kategori_by_id(db, kategori_id)
    if not kategori:
        return None
    
    if kategori_adi is not None:
        kategori.Kategori_Adi = kategori_adi
    if tip is not None:
        kategori.Tip = tip
    if ust_kategori_id is not None:
        kategori.Ust_Kategori_ID = ust_kategori_id
    if aktif_pasif is not None:
        kategori.Aktif_Pasif = aktif_pasif
    if gizli is not None:
        kategori.Gizli = gizli
    
    db.commit()
    db.refresh(kategori)
    return kategori


def delete_kategori(db: Session, kategori_id: int) -> bool:
    """Delete a category."""
    kategori = get_kategori_by_id(db, kategori_id)
    if not kategori:
        return False
    
    db.delete(kategori)
    db.commit()
    return True


# ============================================================================
# DEGER (VALUES) QUERIES
# ============================================================================

def get_degerler(
    db: Session,
    skip: int = 0,
    limit: int = 100,
    deger_adi: Optional[str] = None,
    gecerli_tarih: Optional[date] = None
) -> List[Deger]:
    """
    Get values with optional filtering.
    
    Args:
        db: Database session
        skip: Pagination offset
        limit: Pagination limit
        deger_adi: Filter by name
        gecerli_tarih: Filter values valid on this date
    
    Returns:
        List of Deger objects
    """
    stmt = select(Deger)
    
    if deger_adi is not None:
        stmt = stmt.where(Deger.Deger_Adi == deger_adi)
    
    if gecerli_tarih is not None:
        stmt = stmt.where(
            (Deger.Gecerli_Baslangic_Tarih <= gecerli_tarih) &
            (Deger.Gecerli_Bitis_Tarih >= gecerli_tarih)
        )
    
    stmt = stmt.offset(skip).limit(limit)
    return db.scalars(stmt).all()


def get_deger_by_id(db: Session, deger_id: int) -> Optional[Deger]:
    """Get a value by ID."""
    return db.get(Deger, deger_id)


def get_deger_by_name(
    db: Session,
    deger_adi: str,
    gecerli_tarih: Optional[date] = None
) -> Optional[Deger]:
    """
    Get a value by name, optionally filtered by date.
    
    Args:
        db: Database session
        deger_adi: Value name
        gecerli_tarih: Filter by valid date
    
    Returns:
        Deger object or None
    """
    stmt = select(Deger).where(Deger.Deger_Adi == deger_adi)
    
    if gecerli_tarih is not None:
        stmt = stmt.where(
            (Deger.Gecerli_Baslangic_Tarih <= gecerli_tarih) &
            (Deger.Gecerli_Bitis_Tarih >= gecerli_tarih)
        )
    else:
        # Default to today
        from datetime import datetime
        today = datetime.now().date()
        stmt = stmt.where(
            (Deger.Gecerli_Baslangic_Tarih <= today) &
            (Deger.Gecerli_Bitis_Tarih >= today)
        )
    
    return db.scalars(stmt).first()


def create_deger(
    db: Session,
    deger_adi: str,
    baslangic_tarih: date,
    deger_value: float,
    bitis_tarih: Optional[date] = None,
    aciklama: Optional[str] = None
) -> Deger:
    """Create a new value."""
    if bitis_tarih is None:
        bitis_tarih = date(2100, 1, 1)
    
    new_deger = Deger(
        Deger_Adi=deger_adi,
        Gecerli_Baslangic_Tarih=baslangic_tarih,
        Gecerli_Bitis_Tarih=bitis_tarih,
        Deger_Aciklama=aciklama,
        Deger=deger_value
    )
    db.add(new_deger)
    db.commit()
    db.refresh(new_deger)
    return new_deger


def update_deger(
    db: Session,
    deger_id: int,
    deger_adi: Optional[str] = None,
    baslangic_tarih: Optional[date] = None,
    bitis_tarih: Optional[date] = None,
    deger_value: Optional[float] = None,
    aciklama: Optional[str] = None
) -> Optional[Deger]:
    """Update a value."""
    deger_obj = get_deger_by_id(db, deger_id)
    if not deger_obj:
        return None
    
    if deger_adi is not None:
        deger_obj.Deger_Adi = deger_adi
    if baslangic_tarih is not None:
        deger_obj.Gecerli_Baslangic_Tarih = baslangic_tarih
    if bitis_tarih is not None:
        deger_obj.Gecerli_Bitis_Tarih = bitis_tarih
    if deger_value is not None:
        deger_obj.Deger = deger_value
    if aciklama is not None:
        deger_obj.Deger_Aciklama = aciklama
    
    db.commit()
    db.refresh(deger_obj)
    return deger_obj


def delete_deger(db: Session, deger_id: int) -> bool:
    """Delete a value."""
    deger_obj = get_deger_by_id(db, deger_id)
    if not deger_obj:
        return False
    
    db.delete(deger_obj)
    db.commit()
    return True


# ============================================================================
# KULLANICI (USERS) QUERIES
# ============================================================================

def get_kullanicilar(
    db: Session,
    skip: int = 0,
    limit: int = 100,
    aktif_only: bool = True
) -> List[Kullanici]:
    """
    Get users with pagination.
    
    Args:
        db: Database session
        skip: Pagination offset
        limit: Pagination limit
        aktif_only: Only return active users
    
    Returns:
        List of Kullanici objects
    """
    stmt = select(Kullanici)
    
    if aktif_only:
        stmt = stmt.where(Kullanici.Aktif_Pasif == True)
    
    stmt = stmt.offset(skip).limit(limit)
    return db.scalars(stmt).all()


def get_kullanici_by_id(db: Session, kullanici_id: int) -> Optional[Kullanici]:
    """Get a user by ID."""
    return db.get(Kullanici, kullanici_id)


def get_kullanici_by_username(db: Session, kullanici_adi: str) -> Optional[Kullanici]:
    """Get a user by username."""
    stmt = select(Kullanici).where(Kullanici.Kullanici_Adi == kullanici_adi)
    return db.scalars(stmt).first()


def get_kullanicilar_by_sube(
    db: Session,
    sube_id: int,
    skip: int = 0,
    limit: int = 100
) -> List[Kullanici]:
    """Get all users in a branch."""
    stmt = (
        select(Kullanici)
        .join(KullaniciRol, Kullanici.Kullanici_ID == KullaniciRol.Kullanici_ID)
        .where(KullaniciRol.Sube_ID == sube_id)
        .offset(skip)
        .limit(limit)
    )
    return db.scalars(stmt).unique().all()


def count_kullanicilar(db: Session, aktif_only: bool = True) -> int:
    """Count users in the system."""
    stmt = select(Kullanici)
    if aktif_only:
        stmt = stmt.where(Kullanici.Aktif_Pasif == True)
    
    from sqlalchemy import func
    count_stmt = select(func.count(Kullanici.Kullanici_ID)).select_from(stmt.subquery())
    return db.scalars(count_stmt).first() or 0
