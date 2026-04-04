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
    Kategori, UstKategori, Deger, Sube, Kullanici, KullaniciRol, Rol, Yetki, EFaturaReferans, OdemeReferans, Cari,
    RobotposGelir, RobotposGelirReferans
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
    aktif_only: bool = True,
    can_view_gizli: bool = False
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
        can_view_gizli: If False, hide categories where Gizli=1
    
    Returns:
        List of Kategori objects
    """
    stmt = select(Kategori)
    
    if aktif_only:
        stmt = stmt.where(Kategori.Aktif_Pasif == True)
    
    if not can_view_gizli:
        stmt = stmt.where(Kategori.Gizli == False)
        
    if ust_kategori_id is not None:
        stmt = stmt.where(Kategori.Ust_Kategori_ID == ust_kategori_id)
    
    if tip is not None:
        if isinstance(tip, list):
            stmt = stmt.where(Kategori.Tip.in_(tip))
        else:
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


# ============================================================================
# ROL (ROLES) QUERIES
# ============================================================================

def get_roller(db: Session, skip: int = 0, limit: int = 100,
                 rol_adi: Optional[str] = None, aktif_only: bool = False) -> List[Rol]:
    query = select(Rol)
    
    if rol_adi:
        query = query.filter(Rol.Rol_Adi.ilike(f"%{rol_adi}%"))
        
    if aktif_only:
        query = query.filter(Rol.Aktif_Pasif == True)
        
    query = query.offset(skip).limit(limit)
    return db.scalars(query).all()

def get_rol_by_id(db: Session, rol_id: int) -> Optional[Rol]:
    return db.get(Rol, rol_id)

def create_rol(db: Session, rol_adi: str, aciklama: Optional[str] = None, aktif_pasif: bool = True) -> Rol:
    db_rol = Rol(
        Rol_Adi=rol_adi,
        Aciklama=aciklama,
        Aktif_Pasif=aktif_pasif
    )
    db.add(db_rol)
    db.commit()
    db.refresh(db_rol)
    return db_rol

def update_rol(db: Session, db_rol: Rol, rol_adi: Optional[str] = None,
                 aciklama: Optional[str] = None, aktif_pasif: Optional[bool] = None) -> Rol:
    if rol_adi is not None:
        db_rol.Rol_Adi = rol_adi
    if aciklama is not None:
        db_rol.Aciklama = aciklama
    if aktif_pasif is not None:
        db_rol.Aktif_Pasif = aktif_pasif
        
    db.commit()
    db.refresh(db_rol)
    return db_rol

def delete_rol(db: Session, db_rol: Rol) -> bool:
    db.delete(db_rol)
    db.commit()
    return True


# ============================================================================
# YETKİ (PERMISSIONS) QUERIES
# ============================================================================

def get_yetkiler(db: Session, skip: int = 0, limit: int = 100,
                 yetki_adi: Optional[str] = None, aktif_only: bool = False) -> List[Yetki]:
    query = select(Yetki)
    
    if yetki_adi:
        query = query.filter(Yetki.Yetki_Adi.ilike(f"%{yetki_adi}%"))
        
    if aktif_only:
        query = query.filter(Yetki.Aktif_Pasif == True)
        
    query = query.offset(skip).limit(limit)
    return db.scalars(query).all()

def get_yetki_by_id(db: Session, yetki_id: int) -> Optional[Yetki]:
    return db.get(Yetki, yetki_id)

def create_yetki(db: Session, yetki_adi: str, aciklama: Optional[str] = None, tip: Optional[str] = None, aktif_pasif: bool = True) -> Yetki:
    db_yetki = Yetki(
        Yetki_Adi=yetki_adi,
        Aciklama=aciklama,
        Tip=tip,
        Aktif_Pasif=aktif_pasif
    )
    db.add(db_yetki)
    db.commit()
    db.refresh(db_yetki)
    return db_yetki

def update_yetki(db: Session, db_yetki: Yetki, yetki_adi: Optional[str] = None,
                 aciklama: Optional[str] = None, tip: Optional[str] = None, aktif_pasif: Optional[bool] = None) -> Yetki:
    if yetki_adi is not None:
        db_yetki.Yetki_Adi = yetki_adi
    if aciklama is not None:
        db_yetki.Aciklama = aciklama
    if tip is not None:
        db_yetki.Tip = tip
    if aktif_pasif is not None:
        db_yetki.Aktif_Pasif = aktif_pasif
        
    db.commit()
    db.refresh(db_yetki)
    return db_yetki

def delete_yetki(db: Session, db_yetki: Yetki) -> bool:
    db.delete(db_yetki)
    db.commit()
    return True

# ============================================================================
# KULLANICI-ROL ATAMA QUERIES
# ============================================================================

from sqlalchemy.orm import joinedload

def get_kullanici_rolleri(db: Session, skip: int = 0, limit: int = 100,
                          kullanici_id: Optional[int] = None) -> List[KullaniciRol]:
    query = select(KullaniciRol).options(
        joinedload(KullaniciRol.kullanici),
        joinedload(KullaniciRol.rol),
        joinedload(KullaniciRol.sube)
    )
    
    if kullanici_id is not None:
        query = query.filter(KullaniciRol.Kullanici_ID == kullanici_id)
        
    query = query.offset(skip).limit(limit)
    return db.scalars(query).all()

# ============================================================================
# E-FATURA REFERANS QUERIES
# ============================================================================

def get_efatura_referanslar(db: Session, skip: int = 0, limit: int = 100, search: Optional[str] = None) -> List[EFaturaReferans]:
    query = select(EFaturaReferans).options(joinedload(EFaturaReferans.kategori))
    if search:
        query = query.filter(EFaturaReferans.Alici_Unvani.ilike(f"%{search}%"))
    query = query.offset(skip).limit(limit)
    return db.scalars(query).all()

def get_efatura_referans_by_unvan(db: Session, alici_unvani: str) -> Optional[EFaturaReferans]:
    return db.get(EFaturaReferans, alici_unvani)

def create_efatura_referans(db: Session, alici_unvani: str, kategori_id: int, referans_kodu: str = "TANIMSIZ", aciklama: Optional[str] = None, aktif_pasif: bool = True) -> EFaturaReferans:
    db_ref = EFaturaReferans(
        Alici_Unvani=alici_unvani,
        Referans_Kodu=referans_kodu,
        Kategori_ID=kategori_id,
        Aciklama=aciklama,
        Aktif_Pasif=aktif_pasif
    )
    db.add(db_ref)
    db.commit()
    db.refresh(db_ref)
    return db_ref

def update_efatura_referans(db: Session, db_ref: EFaturaReferans, kategori_id: Optional[int] = None, aktif_pasif: Optional[bool] = None) -> EFaturaReferans:
    if kategori_id is not None:
        db_ref.Kategori_ID = kategori_id
    if aktif_pasif is not None:
        db_ref.Aktif_Pasif = aktif_pasif
        
    db.commit()
    db.refresh(db_ref)
    return db_ref

def delete_efatura_referans(db: Session, db_ref: EFaturaReferans) -> bool:
    db.delete(db_ref)
    db.commit()
    return True

# ============================================================================
# ÖDEME REFERANS QUERIES
# ============================================================================

def get_odeme_referanslar(db: Session, skip: int = 0, limit: int = 100, search: Optional[str] = None) -> List[OdemeReferans]:
    query = select(OdemeReferans).options(joinedload(OdemeReferans.kategori))
    if search:
        query = query.filter(OdemeReferans.Referans_Metin.ilike(f"%{search}%"))
    query = query.offset(skip).limit(limit)
    return db.scalars(query).all()

def get_odeme_referans_by_metin(db: Session, referans_metin: str) -> Optional[OdemeReferans]:
    stmt = select(OdemeReferans).where(OdemeReferans.Referans_Metin == referans_metin)
    return db.scalars(stmt).first()

def get_odeme_referans_by_id(db: Session, referans_id: int) -> Optional[OdemeReferans]:
    return db.get(OdemeReferans, referans_id)

def create_odeme_referans(db: Session, referans_metin: str, kategori_id: int, aktif_pasif: bool = True) -> OdemeReferans:
    db_ref = OdemeReferans(
        Referans_Metin=referans_metin,
        Kategori_ID=kategori_id,
        Aktif_Pasif=aktif_pasif
    )
    db.add(db_ref)
    db.commit()
    db.refresh(db_ref)
    return db_ref

def update_odeme_referans(db: Session, db_ref: OdemeReferans, kategori_id: Optional[int] = None, aktif_pasif: Optional[bool] = None) -> OdemeReferans:
    if kategori_id is not None:
        db_ref.Kategori_ID = kategori_id
    if aktif_pasif is not None:
        db_ref.Aktif_Pasif = aktif_pasif
        
    db.commit()
    db.refresh(db_ref)
    return db_ref

def delete_odeme_referans(db: Session, db_ref: OdemeReferans) -> bool:
    db.delete(db_ref)
    db.commit()
    return True

# ============================================================================
# GELİR REFERANS QUERIES (RobotposGelirReferans)
# ============================================================================

from app.models import RobotposGelirReferans

def get_gelir_referanslar(db: Session, skip: int = 0, limit: int = 100, search: Optional[str] = None) -> List[RobotposGelirReferans]:
    query = select(RobotposGelirReferans).options(joinedload(RobotposGelirReferans.kategori))
    if search:
        query = query.filter(RobotposGelirReferans.Odeme_Tipi.ilike(f"%{search}%"))
    query = query.offset(skip).limit(limit)
    return db.scalars(query).all()

def get_gelir_referans_by_id(db: Session, referans_id: int) -> Optional[RobotposGelirReferans]:
    return db.get(RobotposGelirReferans, referans_id)

def get_gelir_referans_by_tip(db: Session, odeme_tipi: str) -> Optional[RobotposGelirReferans]:
    stmt = select(RobotposGelirReferans).where(RobotposGelirReferans.Odeme_Tipi == odeme_tipi)
    return db.scalars(stmt).first()

def create_gelir_referans(db: Session, odeme_tipi: str, kategori_id: int, aktif_pasif: bool = True) -> RobotposGelirReferans:
    db_ref = RobotposGelirReferans(
        Odeme_Tipi=odeme_tipi,
        Kategori_ID=kategori_id,
        Aktif_Pasif=aktif_pasif
    )
    db.add(db_ref)
    db.commit()
    db.refresh(db_ref)
    return db_ref

def update_gelir_referans(db: Session, db_ref: RobotposGelirReferans, odeme_tipi: Optional[str] = None, kategori_id: Optional[int] = None, aktif_pasif: Optional[bool] = None) -> RobotposGelirReferans:
    if odeme_tipi is not None:
        db_ref.Odeme_Tipi = odeme_tipi
    if kategori_id is not None:
        db_ref.Kategori_ID = kategori_id
    if aktif_pasif is not None:
        db_ref.Aktif_Pasif = aktif_pasif
        
    db.commit()
    db.refresh(db_ref)
    return db_ref

def delete_gelir_referans(db: Session, db_ref: RobotposGelirReferans) -> bool:
    db.delete(db_ref)
    db.commit()
    return True

def get_kullanici_rol(db: Session, kullanici_id: int, rol_id: int, sube_id: int) -> Optional[KullaniciRol]:
    return db.get(KullaniciRol, (kullanici_id, rol_id, sube_id))

def create_kullanici_rol(db: Session, kullanici_id: int, rol_id: int, sube_id: int, aktif_pasif: bool = True) -> KullaniciRol:
    db_krol = KullaniciRol(
        Kullanici_ID=kullanici_id,
        Rol_ID=rol_id,
        Sube_ID=sube_id,
        Aktif_Pasif=aktif_pasif
    )
    db.add(db_krol)
    db.commit()
    db.refresh(db_krol)
    return db_krol

def update_kullanici_rol(db: Session, db_krol: KullaniciRol, aktif_pasif: bool) -> KullaniciRol:
    db_krol.Aktif_Pasif = aktif_pasif
    db.commit()
    db.refresh(db_krol)
    return db_krol

def delete_kullanici_rol(db: Session, db_krol: KullaniciRol) -> bool:
    db.delete(db_krol)
    db.commit()
    return True


# ============================================================================
# ROL-YETKİ ATAMA QUERIES
# ============================================================================

from app.models import RolYetki

def get_rol_yetkileri(db: Session, skip: int = 0, limit: int = 100,
                      rol_id: Optional[int] = None) -> List[RolYetki]:
    query = select(RolYetki).options(
        joinedload(RolYetki.rol),
        joinedload(RolYetki.yetki)
    )
    
    if rol_id is not None:
        query = query.filter(RolYetki.Rol_ID == rol_id)
        
    query = query.offset(skip).limit(limit)
    return db.scalars(query).all()

def get_rol_yetki(db: Session, rol_id: int, yetki_id: int) -> Optional[RolYetki]:
    return db.get(RolYetki, (rol_id, yetki_id))

def create_rol_yetki(db: Session, rol_id: int, yetki_id: int, aktif_pasif: bool = True) -> RolYetki:
    db_ryetki = RolYetki(
        Rol_ID=rol_id,
        Yetki_ID=yetki_id,
        Aktif_Pasif=aktif_pasif
    )
    db.add(db_ryetki)
    db.commit()
    db.refresh(db_ryetki)
    return db_ryetki

def update_rol_yetki(db: Session, db_ryetki: RolYetki, aktif_pasif: bool) -> RolYetki:
    db_ryetki.Aktif_Pasif = aktif_pasif
    db.commit()
    db.refresh(db_ryetki)
    return db_ryetki

def delete_rol_yetki(db: Session, db_ryetki: RolYetki) -> bool:
    db.delete(db_ryetki)
    db.commit()
    return True

# ============================================================================
# CARI (CLIENTS) QUERIES
# ============================================================================

def get_cariler(
    db: Session,
    skip: int = 0,
    limit: int = 100,
    search: Optional[str] = None
) -> List[Cari]:
    """Get all cariler with optional search."""
    stmt = select(Cari).options(
        joinedload(Cari.e_fatura_kategori),
        joinedload(Cari.odeme_kategori)
    )
    
    if search:
        stmt = stmt.where(Cari.Alici_Unvani.ilike(f"%{search}%"))
        
    stmt = stmt.offset(skip).limit(limit)
    return db.scalars(stmt).all()


def get_cari_by_id(db: Session, cari_id: int) -> Optional[Cari]:
    """Get a cari by ID."""
    return db.get(Cari, cari_id)


def create_cari(
    db: Session,
    alici_unvani: str,
    e_fatura_kategori_id: Optional[int] = None,
    odeme_kategori_id: Optional[int] = None,
    tip: Optional[str] = None,
    aciklama: Optional[str] = None,
    aktif_pasif: bool = True
) -> Cari:
    """Create a new cari record."""
    new_cari = Cari(
        Alici_Unvani=alici_unvani,
        e_Fatura_Kategori_ID=e_fatura_kategori_id,
        Odeme_Kategori_ID=odeme_kategori_id,
        Tip=tip,
        Aciklama=aciklama,
        Aktif_Pasif=aktif_pasif
    )
    db.add(new_cari)
    db.commit()
    db.refresh(new_cari)
    return new_cari


def update_cari(
    db: Session,
    db_cari: Cari,
    alici_unvani: Optional[str] = None,
    e_fatura_kategori_id: Optional[int] = None,
    odeme_kategori_id: Optional[int] = None,
    tip: Optional[str] = None,
    aciklama: Optional[str] = None,
    aktif_pasif: Optional[bool] = None
) -> Cari:
    """Update an existing cari record."""
    if alici_unvani is not None:
        db_cari.Alici_Unvani = alici_unvani
    if e_fatura_kategori_id is not None:
        db_cari.e_Fatura_Kategori_ID = e_fatura_kategori_id
    if odeme_kategori_id is not None:
        db_cari.Odeme_Kategori_ID = odeme_kategori_id
    if tip is not None:
        db_cari.Tip = tip
    if aciklama is not None:
        db_cari.Aciklama = aciklama
    if aktif_pasif is not None:
        db_cari.Aktif_Pasif = aktif_pasif
        
    db.commit()
    db.refresh(db_cari)
    return db_cari


def delete_cari(db: Session, db_cari: Cari) -> bool:
    """Delete a cari record."""
    db.delete(db_cari)
    db.commit()
    return True


# ============================================================================
# ROBOTPOS GELIR QUERIES
# ============================================================================

def get_robotpos_gelir_by_unique_fields(
    db: Session, 
    tarih: date, 
    tutar: float, 
    odeme_tipi: str, 
    sube_id: int,
    cek_no: Optional[str] = None
) -> Optional[RobotposGelir]:
    """Find a RobotposGelir record by unique combination to prevent duplicates."""
    query_conditions = [
        RobotposGelir.Tarih == tarih,
        RobotposGelir.Tutar == tutar,
        RobotposGelir.Odeme_Tipi == odeme_tipi,
        RobotposGelir.Sube_ID == sube_id
    ]
    if cek_no:
        query_conditions.append(RobotposGelir.Cek_No == cek_no)
        
    stmt = select(RobotposGelir).where(*query_conditions)
    return db.scalars(stmt).first()


def get_gelir_referanslar_for_mapping(db: Session) -> List[RobotposGelirReferans]:
    """Get all Gelir references for mapping during upload."""
    stmt = select(RobotposGelirReferans)
    return db.scalars(stmt).all()


def bulk_upsert_robotpos_gelir(db: Session, records: List[dict]) -> tuple:
    """
    Insert RobotPOS income records with duplicate control.
    Returns (added_count, skipped_count)
    """
    added = 0
    skipped = 0
    
    for rec in records:
        # Check for existing
        existing = get_robotpos_gelir_by_unique_fields(
            db, 
            rec['Tarih'], 
            rec['Tutar'], 
            rec['Odeme_Tipi'], 
            rec['Sube_ID'],
            rec.get('Cek_No')
        )
        
        if existing:
            skipped += 1
            continue
            
        new_rec = RobotposGelir(
            Tarih=rec['Tarih'],
            Tutar=rec['Tutar'],
            Odeme_Tipi=rec['Odeme_Tipi'],
            Kategori_ID=rec['Kategori_ID'],
            Sube_ID=rec['Sube_ID'],
            Cek_No=rec.get('Cek_No'),
            Satis_Kanali=rec.get('Satis_Kanali')
        )
        db.add(new_rec)
        added += 1
        
    db.commit()
    return added, skipped
