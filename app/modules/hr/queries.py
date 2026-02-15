"""
HR Domain Query Functions
CRUD operations for Employee, Attendance, Advance Requests, and Employee Requests.
"""

from datetime import datetime, date
from decimal import Decimal
from typing import List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import select

from app.models import Calisan, PuantajSecimi, Puantaj, AvansIstek, CalisanTalep


# ============================================================================
# CALISAN (EMPLOYEE) QUERIES
# ============================================================================

def get_calisanlar(
    db: Session,
    skip: int = 0,
    limit: int = 100,
    sube_id: Optional[int] = None,
    aktif_pasif: Optional[bool] = None
) -> List[Calisan]:
    """
    Get all employees with optional filtering.
    
    Args:
        db: Database session
        skip: Number of records to skip (pagination)
        limit: Maximum number of records to return (max 1000)
        sube_id: Filter by branch
        aktif_pasif: Filter by active/passive status
    
    Returns:
        List of Calisan records
    """
    limit = min(limit, 1000)
    stmt = select(Calisan)
    
    if sube_id is not None:
        stmt = stmt.where(Calisan.Sube_ID == sube_id)
    if aktif_pasif is not None:
        stmt = stmt.where(Calisan.Aktif_Pasif == aktif_pasif)
    
    return db.scalars(stmt.offset(skip).limit(limit)).all()


def get_calisan_by_tc_no(db: Session, tc_no: str) -> Optional[Calisan]:
    """Get employee by TC ID number."""
    return db.query(Calisan).filter(Calisan.TC_No == tc_no).first()


def create_calisan(
    db: Session,
    tc_no: str,
    adi: str,
    soyadi: str,
    sube_id: int,
    hesap_no: Optional[str] = None,
    iban: Optional[str] = None,
    net_maas: Optional[float] = None,
    sigorta_giris: Optional[date] = None,
    sigorta_cikis: Optional[date] = None,
    aktif_pasif: bool = True
) -> Calisan:
    """Create a new employee."""
    new_calisan = Calisan(
        TC_No=tc_no,
        Adi=adi,
        Soyadi=soyadi,
        Sube_ID=sube_id,
        Hesap_No=hesap_no,
        IBAN=iban,
        Net_Maas=Decimal(str(net_maas)) if net_maas else None,
        Sigorta_Giris=sigorta_giris,
        Sigorta_Cikis=sigorta_cikis,
        Aktif_Pasif=aktif_pasif
    )
    db.add(new_calisan)
    db.commit()
    db.refresh(new_calisan)
    return new_calisan


def update_calisan(
    db: Session,
    tc_no: str,
    adi: Optional[str] = None,
    soyadi: Optional[str] = None,
    hesap_no: Optional[str] = None,
    iban: Optional[str] = None,
    net_maas: Optional[float] = None,
    sigorta_cikis: Optional[date] = None,
    aktif_pasif: Optional[bool] = None
) -> Optional[Calisan]:
    """Update employee."""
    calisan = get_calisan_by_tc_no(db, tc_no)
    if not calisan:
        return None
    
    if adi is not None:
        calisan.Adi = adi
    if soyadi is not None:
        calisan.Soyadi = soyadi
    if hesap_no is not None:
        calisan.Hesap_No = hesap_no
    if iban is not None:
        calisan.IBAN = iban
    if net_maas is not None:
        calisan.Net_Maas = Decimal(str(net_maas))
    if sigorta_cikis is not None:
        calisan.Sigorta_Cikis = sigorta_cikis
    if aktif_pasif is not None:
        calisan.Aktif_Pasif = aktif_pasif
    
    db.commit()
    db.refresh(calisan)
    return calisan


def delete_calisan(db: Session, tc_no: str) -> bool:
    """Delete employee."""
    calisan = get_calisan_by_tc_no(db, tc_no)
    if not calisan:
        return False
    
    db.delete(calisan)
    db.commit()
    return True


# ============================================================================
# PUANTAJ SECIMI (ATTENDANCE TYPE) QUERIES
# ============================================================================

def get_puantaj_secimler(
    db: Session,
    skip: int = 0,
    limit: int = 100,
    aktif_pasif: Optional[bool] = None
) -> List[PuantajSecimi]:
    """
    Get all attendance types with optional filtering.
    
    Args:
        db: Database session
        skip: Number of records to skip (pagination)
        limit: Maximum number of records to return (max 1000)
        aktif_pasif: Filter by active/passive status
    
    Returns:
        List of PuantajSecimi records
    """
    limit = min(limit, 1000)
    stmt = select(PuantajSecimi)
    
    if aktif_pasif is not None:
        stmt = stmt.where(PuantajSecimi.Aktif_Pasif == aktif_pasif)
    
    return db.scalars(stmt.offset(skip).limit(limit)).all()


def get_puantaj_secim_by_id(db: Session, secim_id: int) -> Optional[PuantajSecimi]:
    """Get attendance type by ID."""
    return db.query(PuantajSecimi).filter(PuantajSecimi.Secim_ID == secim_id).first()


def create_puantaj_secim(
    db: Session,
    secim: str,
    degeri: float,
    renk_kodu: str,
    aktif_pasif: bool = True
) -> PuantajSecimi:
    """Create a new attendance type."""
    new_secim = PuantajSecimi(
        Secim=secim,
        Degeri=Decimal(str(degeri)),
        Renk_Kodu=renk_kodu,
        Aktif_Pasif=aktif_pasif
    )
    db.add(new_secim)
    db.commit()
    db.refresh(new_secim)
    return new_secim


def update_puantaj_secim(
    db: Session,
    secim_id: int,
    secim: Optional[str] = None,
    degeri: Optional[float] = None,
    renk_kodu: Optional[str] = None,
    aktif_pasif: Optional[bool] = None
) -> Optional[PuantajSecimi]:
    """Update attendance type."""
    secim_obj = get_puantaj_secim_by_id(db, secim_id)
    if not secim_obj:
        return None
    
    if secim is not None:
        secim_obj.Secim = secim
    if degeri is not None:
        secim_obj.Degeri = Decimal(str(degeri))
    if renk_kodu is not None:
        secim_obj.Renk_Kodu = renk_kodu
    if aktif_pasif is not None:
        secim_obj.Aktif_Pasif = aktif_pasif
    
    db.commit()
    db.refresh(secim_obj)
    return secim_obj


def delete_puantaj_secim(db: Session, secim_id: int) -> bool:
    """Delete attendance type."""
    secim_obj = get_puantaj_secim_by_id(db, secim_id)
    if not secim_obj:
        return False
    
    db.delete(secim_obj)
    db.commit()
    return True


# ============================================================================
# PUANTAJ (ATTENDANCE) QUERIES
# ============================================================================

def get_puantajlar(
    db: Session,
    skip: int = 0,
    limit: int = 100,
    tc_no: Optional[str] = None,
    sube_id: Optional[int] = None,
    secim_id: Optional[int] = None,
    tarihten: Optional[date] = None,
    tarihine: Optional[date] = None
) -> List[Puantaj]:
    """
    Get all attendance records with optional filtering.
    
    Args:
        db: Database session
        skip: Number of records to skip (pagination)
        limit: Maximum number of records to return (max 1000)
        tc_no: Filter by employee TC ID
        sube_id: Filter by branch
        secim_id: Filter by attendance type
        tarihten: Filter records from date
        tarihine: Filter records to date
    
    Returns:
        List of Puantaj records
    """
    limit = min(limit, 1000)
    stmt = select(Puantaj)
    
    if tc_no is not None:
        stmt = stmt.where(Puantaj.TC_No == tc_no)
    if sube_id is not None:
        stmt = stmt.where(Puantaj.Sube_ID == sube_id)
    if secim_id is not None:
        stmt = stmt.where(Puantaj.Secim_ID == secim_id)
    if tarihten is not None:
        stmt = stmt.where(Puantaj.Tarih >= tarihten)
    if tarihine is not None:
        stmt = stmt.where(Puantaj.Tarih <= tarihine)
    
    return db.scalars(stmt.offset(skip).limit(limit)).all()


def get_puantaj_by_id(db: Session, puantaj_id: int) -> Optional[Puantaj]:
    """Get attendance record by ID."""
    return db.query(Puantaj).filter(Puantaj.Puantaj_ID == puantaj_id).first()


def create_puantaj(
    db: Session,
    tc_no: str,
    secim_id: int,
    sube_id: int,
    tarih: Optional[date] = None,
    kayit_tarihi: Optional[datetime] = None
) -> Puantaj:
    """Create a new attendance record."""
    if tarih is None:
        tarih = datetime.now().date()
    if kayit_tarihi is None:
        kayit_tarihi = datetime.now()
    
    new_puantaj = Puantaj(
        Tarih=tarih,
        TC_No=tc_no,
        Secim_ID=secim_id,
        Sube_ID=sube_id,
        Kayit_Tarihi=kayit_tarihi
    )
    db.add(new_puantaj)
    db.commit()
    db.refresh(new_puantaj)
    return new_puantaj


def update_puantaj(
    db: Session,
    puantaj_id: int,
    secim_id: Optional[int] = None,
    tarih: Optional[date] = None
) -> Optional[Puantaj]:
    """Update attendance record."""
    puantaj = get_puantaj_by_id(db, puantaj_id)
    if not puantaj:
        return None
    
    if secim_id is not None:
        puantaj.Secim_ID = secim_id
    if tarih is not None:
        puantaj.Tarih = tarih
    
    db.commit()
    db.refresh(puantaj)
    return puantaj


def delete_puantaj(db: Session, puantaj_id: int) -> bool:
    """Delete attendance record."""
    puantaj = get_puantaj_by_id(db, puantaj_id)
    if not puantaj:
        return False
    
    db.delete(puantaj)
    db.commit()
    return True


# ============================================================================
# AVANS ISTEK (ADVANCE REQUEST) QUERIES
# ============================================================================

def get_avans_istekler(
    db: Session,
    skip: int = 0,
    limit: int = 100,
    tc_no: Optional[str] = None,
    sube_id: Optional[int] = None,
    donem: Optional[int] = None,
    donemden: Optional[int] = None,
    doneme: Optional[int] = None
) -> List[AvansIstek]:
    """
    Get all advance requests with optional filtering.
    
    Args:
        db: Database session
        skip: Number of records to skip (pagination)
        limit: Maximum number of records to return (max 1000)
        tc_no: Filter by employee TC ID
        sube_id: Filter by branch
        donem: Filter by specific period (YYMM format)
        donemden: Filter period from
        doneme: Filter period to
    
    Returns:
        List of AvansIstek records
    """
    limit = min(limit, 1000)
    stmt = select(AvansIstek)
    
    if tc_no is not None:
        stmt = stmt.where(AvansIstek.TC_No == tc_no)
    if sube_id is not None:
        stmt = stmt.where(AvansIstek.Sube_ID == sube_id)
    if donem is not None:
        stmt = stmt.where(AvansIstek.Donem == donem)
    if donemden is not None:
        stmt = stmt.where(AvansIstek.Donem >= donemden)
    if doneme is not None:
        stmt = stmt.where(AvansIstek.Donem <= doneme)
    
    return db.scalars(stmt.offset(skip).limit(limit)).all()


def get_avans_istek_by_id(db: Session, avans_id: int) -> Optional[AvansIstek]:
    """Get advance request by ID."""
    return db.query(AvansIstek).filter(AvansIstek.Avans_ID == avans_id).first()


def create_avans_istek(
    db: Session,
    tc_no: str,
    sube_id: int,
    donem: int,
    tutar: float,
    aciklama: Optional[str] = None,
    kayit_tarihi: Optional[datetime] = None
) -> AvansIstek:
    """Create a new advance request."""
    if kayit_tarihi is None:
        kayit_tarihi = datetime.now()
    
    new_avans = AvansIstek(
        Donem=donem,
        TC_No=tc_no,
        Tutar=Decimal(str(tutar)),
        Aciklama=aciklama,
        Sube_ID=sube_id,
        Kayit_Tarihi=kayit_tarihi
    )
    db.add(new_avans)
    db.commit()
    db.refresh(new_avans)
    return new_avans


def update_avans_istek(
    db: Session,
    avans_id: int,
    tutar: Optional[float] = None,
    aciklama: Optional[str] = None
) -> Optional[AvansIstek]:
    """Update advance request."""
    avans = get_avans_istek_by_id(db, avans_id)
    if not avans:
        return None
    
    if tutar is not None:
        avans.Tutar = Decimal(str(tutar))
    if aciklama is not None:
        avans.Aciklama = aciklama
    
    db.commit()
    db.refresh(avans)
    return avans


def delete_avans_istek(db: Session, avans_id: int) -> bool:
    """Delete advance request."""
    avans = get_avans_istek_by_id(db, avans_id)
    if not avans:
        return False
    
    db.delete(avans)
    db.commit()
    return True


# ============================================================================
# CALISAN TALEP (EMPLOYEE REQUEST) QUERIES
# ============================================================================

def get_calisan_talepler(
    db: Session,
    skip: int = 0,
    limit: int = 100,
    sube_id: Optional[int] = None,
    talep: Optional[str] = None
) -> List[CalisanTalep]:
    """
    Get all employee requests with optional filtering.
    
    Args:
        db: Database session
        skip: Number of records to skip (pagination)
        limit: Maximum number of records to return (max 1000)
        sube_id: Filter by branch
        talep: Filter by request type (İşe Giriş, İşten Çıkış)
    
    Returns:
        List of CalisanTalep records
    """
    limit = min(limit, 1000)
    stmt = select(CalisanTalep)
    
    if sube_id is not None:
        stmt = stmt.where(CalisanTalep.Sube_ID == sube_id)
    if talep is not None:
        stmt = stmt.where(CalisanTalep.Talep == talep)
    
    return db.scalars(stmt.offset(skip).limit(limit)).all()


def get_calisan_talep_by_id(db: Session, talep_id: int) -> Optional[CalisanTalep]:
    """Get employee request by ID."""
    return db.query(CalisanTalep).filter(CalisanTalep.Calisan_Talep_ID == talep_id).first()


def create_calisan_talep(
    db: Session,
    tc_no: str,
    adi: str,
    soyadi: str,
    ilk_soyadi: str,
    sube_id: int,
    talep: str = "İşe Giriş",
    hesap_no: Optional[str] = None,
    iban: Optional[str] = None,
    ogrenim_durumu: Optional[str] = None,
    cinsiyet: str = "Erkek",
    gorevi: Optional[str] = None,
    anne_adi: Optional[str] = None,
    baba_adi: Optional[str] = None,
    dogum_yeri: Optional[str] = None,
    dogum_tarihi: Optional[date] = None,
    medeni_hali: str = "Bekar",
    cep_no: Optional[str] = None,
    adres_bilgileri: Optional[str] = None,
    gelir_vergisi_matrahi: Optional[float] = None,
    ssk_cikis_nedeni: Optional[str] = None,
    net_maas: Optional[float] = None,
    sigorta_giris: Optional[date] = None,
    sigorta_cikis: Optional[date] = None
) -> CalisanTalep:
    """Create a new employee request."""
    new_talep = CalisanTalep(
        Talep=talep,
        TC_No=tc_no,
        Adi=adi,
        Soyadi=soyadi,
        Ilk_Soyadi=ilk_soyadi,
        Sube_ID=sube_id,
        Hesap_No=hesap_no,
        IBAN=iban,
        Ogrenim_Durumu=ogrenim_durumu,
        Cinsiyet=cinsiyet,
        Gorevi=gorevi,
        Anne_Adi=anne_adi,
        Baba_Adi=baba_adi,
        Dogum_Yeri=dogum_yeri,
        Dogum_Tarihi=dogum_tarihi,
        Medeni_Hali=medeni_hali,
        Cep_No=cep_no,
        Adres_Bilgileri=adres_bilgileri,
        Gelir_Vergisi_Matrahi=Decimal(str(gelir_vergisi_matrahi)) if gelir_vergisi_matrahi else None,
        SSK_Cikis_Nedeni=ssk_cikis_nedeni,
        Net_Maas=Decimal(str(net_maas)) if net_maas else None,
        Sigorta_Giris=sigorta_giris,
        Sigorta_Cikis=sigorta_cikis
    )
    db.add(new_talep)
    db.commit()
    db.refresh(new_talep)
    return new_talep


def update_calisan_talep(
    db: Session,
    talep_id: int,
    adi: Optional[str] = None,
    soyadi: Optional[str] = None,
    hesap_no: Optional[str] = None,
    iban: Optional[str] = None,
    net_maas: Optional[float] = None,
    sigorta_cikis: Optional[date] = None
) -> Optional[CalisanTalep]:
    """Update employee request."""
    talep = get_calisan_talep_by_id(db, talep_id)
    if not talep:
        return None
    
    if adi is not None:
        talep.Adi = adi
    if soyadi is not None:
        talep.Soyadi = soyadi
    if hesap_no is not None:
        talep.Hesap_No = hesap_no
    if iban is not None:
        talep.IBAN = iban
    if net_maas is not None:
        talep.Net_Maas = Decimal(str(net_maas))
    if sigorta_cikis is not None:
        talep.Sigorta_Cikis = sigorta_cikis
    
    db.commit()
    db.refresh(talep)
    return talep


def delete_calisan_talep(db: Session, talep_id: int) -> bool:
    """Delete employee request."""
    talep = get_calisan_talep_by_id(db, talep_id)
    if not talep:
        return False
    
    db.delete(talep)
    db.commit()
    return True
