"""
Invoicing Domain Database Queries
CRUD operations for EFatura, Odeme, Nakit, Gelir, and related entities.
Uses SQLAlchemy 2.0 style with pagination and filtering.
"""

from typing import Optional, List
from datetime import date, datetime
from sqlalchemy import select
from sqlalchemy.orm import Session
from app.models import (
    EFatura, B2BEkstre, DigerHarcama, Odeme, OdemeReferans,
    Nakit, POSHareketleri, Gelir, GelirEkstra, EFaturaReferans,
    Kategori, Sube
)


# ============================================================================
# EFATURA (E-INVOICES) QUERIES
# ============================================================================

def get_efaturalar(
    db: Session,
    skip: int = 0,
    limit: int = 100,
    sube_id: Optional[int] = None,
    kategori_id: Optional[int] = None,
    status: Optional[str] = None,
    start_date: Optional[date] = None,
    end_date: Optional[date] = None
) -> List[EFatura]:
    """Get e-invoices with optional filtering."""
    stmt = select(EFatura)
    
    if sube_id is not None:
        stmt = stmt.where(EFatura.Sube_ID == sube_id)
    
    if kategori_id is not None:
        stmt = stmt.where(EFatura.Kategori_ID == kategori_id)
    
    if status is not None:
        stmt = stmt.where(EFatura.Durum == status)
    
    if start_date is not None:
        stmt = stmt.where(EFatura.Kayit_Tarihi >= start_date)
    
    if end_date is not None:
        stmt = stmt.where(EFatura.Kayit_Tarihi <= end_date)
    
    stmt = stmt.offset(skip).limit(limit)
    return db.scalars(stmt).all()


def get_efatura_by_id(db: Session, efatura_id: int) -> Optional[EFatura]:
    """Get e-invoice by ID."""
    return db.get(EFatura, efatura_id)


def create_efatura(
    db: Session,
    sube_id: int,
    kategori_id: int,
    fatura_no: str,
    fatura_tutari: float,
    kayit_tarihi: Optional[date] = None,
    aciklama: Optional[str] = None
) -> EFatura:
    """Create a new e-invoice."""
    if kayit_tarihi is None:
        kayit_tarihi = datetime.now().date()
    
    new_efatura = EFatura(
        Sube_ID=sube_id,
        Kategori_ID=kategori_id,
        Fatura_No=fatura_no,
        Fatura_Tutari=fatura_tutari,
        Kayit_Tarihi=kayit_tarihi,
        Aciklama=aciklama,
        Durum='Beklemede'
    )
    db.add(new_efatura)
    db.commit()
    db.refresh(new_efatura)
    return new_efatura


def update_efatura(
    db: Session,
    efatura_id: int,
    fatura_no: Optional[str] = None,
    fatura_tutari: Optional[float] = None,
    durum: Optional[str] = None,
    aciklama: Optional[str] = None
) -> Optional[EFatura]:
    """Update an e-invoice."""
    efatura = get_efatura_by_id(db, efatura_id)
    if not efatura:
        return None
    
    if fatura_no is not None:
        efatura.Fatura_No = fatura_no
    if fatura_tutari is not None:
        efatura.Fatura_Tutari = fatura_tutari
    if durum is not None:
        efatura.Durum = durum
    if aciklama is not None:
        efatura.Aciklama = aciklama
    
    db.commit()
    db.refresh(efatura)
    return efatura


def delete_efatura(db: Session, efatura_id: int) -> bool:
    """Delete an e-invoice."""
    efatura = get_efatura_by_id(db, efatura_id)
    if not efatura:
        return False
    
    db.delete(efatura)
    db.commit()
    return True


# ============================================================================
# ODEME (PAYMENTS) QUERIES
# ============================================================================

def get_odemeler(
    db: Session,
    skip: int = 0,
    limit: int = 100,
    sube_id: Optional[int] = None,
    kategori_id: Optional[int] = None,
    status: Optional[str] = None,
    start_date: Optional[date] = None,
    end_date: Optional[date] = None
) -> List[Odeme]:
    """Get payments with optional filtering."""
    stmt = select(Odeme)
    
    if sube_id is not None:
        stmt = stmt.where(Odeme.Sube_ID == sube_id)
    
    if kategori_id is not None:
        stmt = stmt.where(Odeme.Kategori_ID == kategori_id)
    
    if status is not None:
        stmt = stmt.where(Odeme.Durum == status)
    
    if start_date is not None:
        stmt = stmt.where(Odeme.Odeme_Tarihi >= start_date)
    
    if end_date is not None:
        stmt = stmt.where(Odeme.Odeme_Tarihi <= end_date)
    
    stmt = stmt.offset(skip).limit(limit)
    return db.scalars(stmt).all()


def get_odeme_by_id(db: Session, odeme_id: int) -> Optional[Odeme]:
    """Get payment by ID."""
    return db.get(Odeme, odeme_id)


def create_odeme(
    db: Session,
    sube_id: int,
    kategori_id: int,
    odeme_tutari: float,
    odeme_tarihi: Optional[date] = None,
    odeme_sekli: str = "Nakit",
    aciklama: Optional[str] = None
) -> Odeme:
    """Create a new payment."""
    if odeme_tarihi is None:
        odeme_tarihi = datetime.now().date()
    
    new_odeme = Odeme(
        Sube_ID=sube_id,
        Kategori_ID=kategori_id,
        Odeme_Tutari=odeme_tutari,
        Odeme_Tarihi=odeme_tarihi,
        Odeme_Sekli=odeme_sekli,
        Aciklama=aciklama,
        Durum='Tamamlandı'
    )
    db.add(new_odeme)
    db.commit()
    db.refresh(new_odeme)
    return new_odeme


def update_odeme(
    db: Session,
    odeme_id: int,
    odeme_tutari: Optional[float] = None,
    odeme_sekli: Optional[str] = None,
    durum: Optional[str] = None,
    aciklama: Optional[str] = None
) -> Optional[Odeme]:
    """Update a payment."""
    odeme = get_odeme_by_id(db, odeme_id)
    if not odeme:
        return None
    
    if odeme_tutari is not None:
        odeme.Odeme_Tutari = odeme_tutari
    if odeme_sekli is not None:
        odeme.Odeme_Sekli = odeme_sekli
    if durum is not None:
        odeme.Durum = durum
    if aciklama is not None:
        odeme.Aciklama = aciklama
    
    db.commit()
    db.refresh(odeme)
    return odeme


def delete_odeme(db: Session, odeme_id: int) -> bool:
    """Delete a payment."""
    odeme = get_odeme_by_id(db, odeme_id)
    if not odeme:
        return False
    
    db.delete(odeme)
    db.commit()
    return True


# ============================================================================
# NAKIT (CASH) QUERIES
# ============================================================================

def get_nakit_list(
    db: Session,
    skip: int = 0,
    limit: int = 100,
    sube_id: Optional[int] = None,
    kategori_id: Optional[int] = None,
    start_date: Optional[date] = None,
    end_date: Optional[date] = None
) -> List[Nakit]:
    """Get cash transactions with optional filtering."""
    stmt = select(Nakit)
    
    if sube_id is not None:
        stmt = stmt.where(Nakit.Sube_ID == sube_id)
    
    if kategori_id is not None:
        stmt = stmt.where(Nakit.Kategori_ID == kategori_id)
    
    if start_date is not None:
        stmt = stmt.where(Nakit.Islem_Tarihi >= start_date)
    
    if end_date is not None:
        stmt = stmt.where(Nakit.Islem_Tarihi <= end_date)
    
    stmt = stmt.offset(skip).limit(limit)
    return db.scalars(stmt).all()


def get_nakit_by_id(db: Session, nakit_id: int) -> Optional[Nakit]:
    """Get cash transaction by ID."""
    return db.get(Nakit, nakit_id)


def create_nakit(
    db: Session,
    sube_id: int,
    kategori_id: int,
    islem_tutari: float,
    islem_sekli: str,
    islem_tarihi: Optional[date] = None,
    aciklama: Optional[str] = None
) -> Nakit:
    """Create a new cash transaction."""
    if islem_tarihi is None:
        islem_tarihi = datetime.now().date()
    
    new_nakit = Nakit(
        Sube_ID=sube_id,
        Kategori_ID=kategori_id,
        Islem_Tutari=islem_tutari,
        Islem_Sekli=islem_sekli,
        Islem_Tarihi=islem_tarihi,
        Aciklama=aciklama
    )
    db.add(new_nakit)
    db.commit()
    db.refresh(new_nakit)
    return new_nakit


def update_nakit(
    db: Session,
    nakit_id: int,
    islem_tutari: Optional[float] = None,
    islem_sekli: Optional[str] = None,
    aciklama: Optional[str] = None
) -> Optional[Nakit]:
    """Update a cash transaction."""
    nakit = get_nakit_by_id(db, nakit_id)
    if not nakit:
        return None
    
    if islem_tutari is not None:
        nakit.Islem_Tutari = islem_tutari
    if islem_sekli is not None:
        nakit.Islem_Sekli = islem_sekli
    if aciklama is not None:
        nakit.Aciklama = aciklama
    
    db.commit()
    db.refresh(nakit)
    return nakit


def delete_nakit(db: Session, nakit_id: int) -> bool:
    """Delete a cash transaction."""
    nakit = get_nakit_by_id(db, nakit_id)
    if not nakit:
        return False
    
    db.delete(nakit)
    db.commit()
    return True


# ============================================================================
# GELIR (INCOME) QUERIES
# ============================================================================

def get_gelirler(
    db: Session,
    skip: int = 0,
    limit: int = 100,
    sube_id: Optional[int] = None,
    kategori_id: Optional[int] = None,
    start_date: Optional[date] = None,
    end_date: Optional[date] = None
) -> List[Gelir]:
    """Get incomes with optional filtering."""
    stmt = select(Gelir)
    
    if sube_id is not None:
        stmt = stmt.where(Gelir.Sube_ID == sube_id)
    
    if kategori_id is not None:
        stmt = stmt.where(Gelir.Kategori_ID == kategori_id)
    
    if start_date is not None:
        stmt = stmt.where(Gelir.Kayit_Tarihi >= start_date)
    
    if end_date is not None:
        stmt = stmt.where(Gelir.Kayit_Tarihi <= end_date)
    
    stmt = stmt.offset(skip).limit(limit)
    return db.scalars(stmt).all()


def get_gelir_by_id(db: Session, gelir_id: int) -> Optional[Gelir]:
    """Get income by ID."""
    return db.get(Gelir, gelir_id)


def create_gelir(
    db: Session,
    sube_id: int,
    kategori_id: int,
    gelir_tutari: float,
    kayit_tarihi: Optional[date] = None,
    aciklama: Optional[str] = None
) -> Gelir:
    """Create a new income."""
    if kayit_tarihi is None:
        kayit_tarihi = datetime.now().date()
    
    new_gelir = Gelir(
        Sube_ID=sube_id,
        Kategori_ID=kategori_id,
        Gelir_Tutari=gelir_tutari,
        Kayit_Tarihi=kayit_tarihi,
        Aciklama=aciklama
    )
    db.add(new_gelir)
    db.commit()
    db.refresh(new_gelir)
    return new_gelir


def update_gelir(
    db: Session,
    gelir_id: int,
    gelir_tutari: Optional[float] = None,
    aciklama: Optional[str] = None
) -> Optional[Gelir]:
    """Update income."""
    gelir = get_gelir_by_id(db, gelir_id)
    if not gelir:
        return None
    
    if gelir_tutari is not None:
        gelir.Gelir_Tutari = gelir_tutari
    if aciklama is not None:
        gelir.Aciklama = aciklama
    
    db.commit()
    db.refresh(gelir)
    return gelir


def delete_gelir(db: Session, gelir_id: int) -> bool:
    """Delete income."""
    gelir = get_gelir_by_id(db, gelir_id)
    if not gelir:
        return False
    
    db.delete(gelir)
    db.commit()
    return True


# ============================================================================
# DIGER HARCAMA (OTHER EXPENSES) QUERIES
# ============================================================================

def get_diger_harcamalar(
    db: Session,
    skip: int = 0,
    limit: int = 100,
    sube_id: Optional[int] = None,
    start_date: Optional[date] = None,
    end_date: Optional[date] = None
) -> List[DigerHarcama]:
    """Get other expenses with optional filtering."""
    stmt = select(DigerHarcama)
    
    if sube_id is not None:
        stmt = stmt.where(DigerHarcama.Sube_ID == sube_id)
    
    if start_date is not None:
        stmt = stmt.where(DigerHarcama.Kayit_Tarihi >= start_date)
    
    if end_date is not None:
        stmt = stmt.where(DigerHarcama.Kayit_Tarihi <= end_date)
    
    stmt = stmt.offset(skip).limit(limit)
    return db.scalars(stmt).all()


def get_diger_harcama_by_id(db: Session, harcama_id: int) -> Optional[DigerHarcama]:
    """Get other expense by ID."""
    return db.get(DigerHarcama, harcama_id)


def create_diger_harcama(
    db: Session,
    sube_id: int,
    harcama_adi: str,
    harcama_tutari: float,
    kayit_tarihi: Optional[date] = None,
    aciklama: Optional[str] = None
) -> DigerHarcama:
    """Create a new other expense."""
    if kayit_tarihi is None:
        kayit_tarihi = datetime.now().date()
    
    new_harcama = DigerHarcama(
        Sube_ID=sube_id,
        Harcama_Adi=harcama_adi,
        Harcama_Tutari=harcama_tutari,
        Kayit_Tarihi=kayit_tarihi,
        Aciklama=aciklama
    )
    db.add(new_harcama)
    db.commit()
    db.refresh(new_harcama)
    return new_harcama


def update_diger_harcama(
    db: Session,
    harcama_id: int,
    harcama_adi: Optional[str] = None,
    harcama_tutari: Optional[float] = None,
    aciklama: Optional[str] = None
) -> Optional[DigerHarcama]:
    """Update other expense."""
    harcama = get_diger_harcama_by_id(db, harcama_id)
    if not harcama:
        return None
    
    if harcama_adi is not None:
        harcama.Harcama_Adi = harcama_adi
    if harcama_tutari is not None:
        harcama.Harcama_Tutari = harcama_tutari
    if aciklama is not None:
        harcama.Aciklama = aciklama
    
    db.commit()
    db.refresh(harcama)
    return harcama


def delete_diger_harcama(db: Session, harcama_id: int) -> bool:
    """Delete other expense."""
    harcama = get_diger_harcama_by_id(db, harcama_id)
    if not harcama:
        return False
    
    db.delete(harcama)
    db.commit()
    return True


# ============================================================================
# POSHAREKETLERİ (POS TRANSACTIONS) QUERIES
# ============================================================================

def get_pos_hareketleri(
    db: Session,
    skip: int = 0,
    limit: int = 100,
    sube_id: Optional[int] = None,
    start_date: Optional[date] = None,
    end_date: Optional[date] = None
) -> List[POSHareketleri]:
    """Get POS transactions with optional filtering."""
    stmt = select(POSHareketleri)
    
    if sube_id is not None:
        stmt = stmt.where(POSHareketleri.Sube_ID == sube_id)
    
    if start_date is not None:
        stmt = stmt.where(POSHareketleri.Islem_Tarihi >= start_date)
    
    if end_date is not None:
        stmt = stmt.where(POSHareketleri.Islem_Tarihi <= end_date)
    
    stmt = stmt.offset(skip).limit(limit)
    return db.scalars(stmt).all()


def get_pos_hareketi_by_id(db: Session, hareketi_id: int) -> Optional[POSHareketleri]:
    """Get POS transaction by ID."""
    return db.get(POSHareketleri, hareketi_id)


def create_pos_hareketi(
    db: Session,
    sube_id: int,
    islem_tutari: float,
    pos_adi: str,
    islem_tarihi: Optional[date] = None,
    aciklama: Optional[str] = None
) -> POSHareketleri:
    """Create a new POS transaction."""
    if islem_tarihi is None:
        islem_tarihi = datetime.now().date()
    
    new_hareketi = POSHareketleri(
        Sube_ID=sube_id,
        Islem_Tutari=islem_tutari,
        Pos_Adi=pos_adi,
        Islem_Tarihi=islem_tarihi,
        Aciklama=aciklama
    )
    db.add(new_hareketi)
    db.commit()
    db.refresh(new_hareketi)
    return new_hareketi


def update_pos_hareketi(
    db: Session,
    hareketi_id: int,
    islem_tutari: Optional[float] = None,
    pos_adi: Optional[str] = None,
    aciklama: Optional[str] = None
) -> Optional[POSHareketleri]:
    """Update POS transaction."""
    hareketi = get_pos_hareketi_by_id(db, hareketi_id)
    if not hareketi:
        return None
    
    if islem_tutari is not None:
        hareketi.Islem_Tutari = islem_tutari
    if pos_adi is not None:
        hareketi.Pos_Adi = pos_adi
    if aciklama is not None:
        hareketi.Aciklama = aciklama
    
    db.commit()
    db.refresh(hareketi)
    return hareketi


def delete_pos_hareketi(db: Session, hareketi_id: int) -> bool:
    """Delete POS transaction."""
    hareketi = get_pos_hareketi_by_id(db, hareketi_id)
    if not hareketi:
        return False
    
    db.delete(hareketi)
    db.commit()
    return True
