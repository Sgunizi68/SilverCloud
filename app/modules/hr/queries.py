"""
HR Domain Query Functions
CRUD operations for Employee, Attendance, Advance Requests, and Employee Requests.
"""

from datetime import datetime, date
from decimal import Decimal
import math
import secrets
from typing import List, Optional, Tuple, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import select, desc, func

from app.models import (
    Calisan, PuantajSecimi, Puantaj, VardiyaPlan, AvansIstek, CalisanTalep, Sube,
    Barkod, VardiyaKayit, VardiyaKayitLog, VardiyaRedDeneme
)


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
    cihaz_kaydi: Optional[str] = None,
    aktif_pasif: bool = True
) -> Calisan:
    """Create a new employee or update existing record on re-hire."""
    if isinstance(sigorta_giris, str) and sigorta_giris:
        try:
            sigorta_giris_dt = date.fromisoformat(sigorta_giris)
        except ValueError:
            sigorta_giris_dt = None
    elif isinstance(sigorta_giris, date):
        sigorta_giris_dt = sigorta_giris
    else:
        sigorta_giris_dt = None

    if isinstance(sigorta_cikis, str) and sigorta_cikis:
        try:
            sigorta_cikis_dt = date.fromisoformat(sigorta_cikis)
        except ValueError:
            sigorta_cikis_dt = None
    elif isinstance(sigorta_cikis, date):
        sigorta_cikis_dt = sigorta_cikis
    else:
        sigorta_cikis_dt = None

    net_maas_val = Decimal(str(net_maas)) if net_maas is not None and net_maas != "" else None

    existing = get_calisan_by_tc_no(db, tc_no)
    if existing:
        existing.Adi = adi
        existing.Soyadi = soyadi
        existing.Sube_ID = sube_id
        if hesap_no is not None:
            existing.Hesap_No = hesap_no
        if iban is not None:
            existing.IBAN = iban
        if net_maas is not None and net_maas != "":
            existing.Net_Maas = net_maas_val
        if sigorta_giris_dt is not None:
            existing.Sigorta_Giris = sigorta_giris_dt
        if sigorta_cikis_dt is not None:
            existing.Sigorta_Cikis = sigorta_cikis_dt
        else:
            existing.Sigorta_Cikis = None
        if cihaz_kaydi is not None:
            existing.Cihaz_Kaydi = cihaz_kaydi
        existing.Aktif_Pasif = aktif_pasif
        
        db.commit()
        db.refresh(existing)
        return existing

    new_calisan = Calisan(
        TC_No=tc_no,
        Adi=adi,
        Soyadi=soyadi,
        Sube_ID=sube_id,
        Hesap_No=hesap_no,
        IBAN=iban,
        Net_Maas=net_maas_val,
        Sigorta_Giris=sigorta_giris_dt,
        Sigorta_Cikis=sigorta_cikis_dt,
        Cihaz_Kaydi=cihaz_kaydi,
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
    sigorta_giris: Optional[date] = None,
    sigorta_cikis: Optional[date] = None,
    cihaz_kaydi: Optional[str] = None,
    aktif_pasif: Optional[bool] = None,
    sube_id: Optional[int] = None
) -> Optional[Calisan]:
    """Update employee."""
    calisan = get_calisan_by_tc_no(db, tc_no)
    if not calisan:
        return None
    
    if sube_id is not None:
        calisan.Sube_ID = sube_id
    if adi is not None:
        calisan.Adi = adi
    if soyadi is not None:
        calisan.Soyadi = soyadi
    if hesap_no is not None:
        calisan.Hesap_No = hesap_no
    if iban is not None:
        calisan.IBAN = iban
    if net_maas == "":
        calisan.Net_Maas = None
    elif net_maas is not None:
        calisan.Net_Maas = Decimal(str(net_maas))
        
    if sigorta_giris == "":
        calisan.Sigorta_Giris = None
    elif isinstance(sigorta_giris, str):
        try:
            calisan.Sigorta_Giris = date.fromisoformat(sigorta_giris)
        except ValueError:
            pass
    elif sigorta_giris is not None:
        calisan.Sigorta_Giris = sigorta_giris
        
    if sigorta_cikis == "":
        calisan.Sigorta_Cikis = None
    elif isinstance(sigorta_cikis, str):
        try:
            calisan.Sigorta_Cikis = date.fromisoformat(sigorta_cikis)
        except ValueError:
            pass
    elif sigorta_cikis is not None:
        calisan.Sigorta_Cikis = sigorta_cikis
    if cihaz_kaydi is not None:
        calisan.Cihaz_Kaydi = cihaz_kaydi if cihaz_kaydi != "" else None
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
    aktif_pasif: bool = True,
    planli: bool = False,
    vardiya_kaydi: bool = False
) -> PuantajSecimi:
    """Create a new attendance type."""
    new_secim = PuantajSecimi(
        Secim=secim,
        Degeri=Decimal(str(degeri)),
        Renk_Kodu=renk_kodu,
        Aktif_Pasif=aktif_pasif,
        Planli=planli,
        Vardiya_Kaydi=vardiya_kaydi
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
    aktif_pasif: Optional[bool] = None,
    planli: Optional[bool] = None,
    vardiya_kaydi: Optional[bool] = None
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
    if planli is not None:
        secim_obj.Planli = planli
    if vardiya_kaydi is not None:
        secim_obj.Vardiya_Kaydi = vardiya_kaydi
    
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


def get_puantajlar_for_month(
    db: Session,
    sube_id: int,
    year: int,
    month: int
) -> List[Puantaj]:
    """
    Get all puantaj records for a branch and a specific month.
    Used for the attendance grid (puantaj girisi) screen.
    """
    import calendar
    _, last_day = calendar.monthrange(year, month)
    tarihten = date(year, month, 1)
    tarihine = date(year, month, last_day)
    
    stmt = (
        select(Puantaj)
        .where(Puantaj.Sube_ID == sube_id)
        .where(Puantaj.Tarih >= tarihten)
        .where(Puantaj.Tarih <= tarihine)
    )
    return db.scalars(stmt).all()


# ============================================================================
# VARDIYA PLAN (SHIFT PLAN) QUERIES
# ============================================================================

def get_vardiya_planlar(
    db: Session,
    skip: int = 0,
    limit: int = 100,
    tc_no: Optional[str] = None,
    sube_id: Optional[int] = None,
    secim_id: Optional[int] = None,
    tarihten: Optional[date] = None,
    tarihine: Optional[date] = None
) -> List[VardiyaPlan]:
    """Get shift plan records with optional filtering."""
    stmt = select(VardiyaPlan)
    if tc_no:
        stmt = stmt.where(VardiyaPlan.TC_No == tc_no)
    if sube_id:
        stmt = stmt.where(VardiyaPlan.Sube_ID == sube_id)
    if secim_id:
        stmt = stmt.where(VardiyaPlan.Secim_ID == secim_id)
    if tarihten:
        stmt = stmt.where(VardiyaPlan.Tarih >= tarihten)
    if tarihine:
        stmt = stmt.where(VardiyaPlan.Tarih <= tarihine)
    return db.scalars(stmt.offset(skip).limit(limit)).all()


def get_vardiya_plan_by_id(db: Session, vardiya_plan_id: int) -> Optional[VardiyaPlan]:
    """Get shift plan record by ID."""
    return db.query(VardiyaPlan).filter(VardiyaPlan.Vardiya_Plan_ID == vardiya_plan_id).first()


def get_vardiya_plan_by_tc_date(db: Session, tc_no: str, tarih: date) -> Optional[VardiyaPlan]:
    """Get shift plan record by employee TC and date (to prevent duplicate entries)."""
    return db.query(VardiyaPlan).filter(VardiyaPlan.TC_No == tc_no, VardiyaPlan.Tarih == tarih).first()


def create_vardiya_plan(
    db: Session,
    tc_no: str,
    secim_id: int,
    sube_id: int,
    tarih: Optional[date] = None,
    kayit_tarihi: Optional[datetime] = None
) -> VardiyaPlan:
    """Create or update a shift plan record. If record exists for same (TC_No, Tarih), update it."""
    if tarih is None:
        tarih = datetime.now().date()
    if kayit_tarihi is None:
        kayit_tarihi = datetime.now()

    # Check for existing record for same employee and date
    existing = get_vardiya_plan_by_tc_date(db, tc_no, tarih)
    if existing:
        existing.Secim_ID = secim_id
        existing.Sube_ID = sube_id
        db.commit()
        db.refresh(existing)
        return existing

    new_plan = VardiyaPlan(
        Tarih=tarih,
        TC_No=tc_no,
        Secim_ID=secim_id,
        Sube_ID=sube_id,
        Kayit_Tarihi=kayit_tarihi
    )
    db.add(new_plan)
    db.commit()
    db.refresh(new_plan)
    return new_plan


def update_vardiya_plan(
    db: Session,
    vardiya_plan_id: int,
    secim_id: Optional[int] = None,
    tarih: Optional[date] = None,
    sube_id: Optional[int] = None
) -> Optional[VardiyaPlan]:
    """Update shift plan record."""
    plan = get_vardiya_plan_by_id(db, vardiya_plan_id)
    if not plan:
        return None

    if secim_id is not None:
        plan.Secim_ID = secim_id
    if tarih is not None:
        plan.Tarih = tarih
    if sube_id is not None:
        plan.Sube_ID = sube_id

    db.commit()
    db.refresh(plan)
    return plan


def delete_vardiya_plan(db: Session, vardiya_plan_id: int) -> bool:
    """Delete shift plan record."""
    plan = get_vardiya_plan_by_id(db, vardiya_plan_id)
    if not plan:
        return False

    db.delete(plan)
    db.commit()
    return True


def get_vardiya_planlar_for_month(
    db: Session,
    sube_id: int,
    year: int,
    month: int
) -> List[VardiyaPlan]:
    """Get all shift plan records for a branch and a specific month."""
    import calendar
    _, last_day = calendar.monthrange(year, month)
    tarihten = date(year, month, 1)
    tarihine = date(year, month, last_day)

    stmt = (
        select(VardiyaPlan)
        .where(VardiyaPlan.Sube_ID == sube_id)
        .where(VardiyaPlan.Tarih >= tarihten)
        .where(VardiyaPlan.Tarih <= tarihine)
    )
    return db.scalars(stmt).all()


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
    sube_id: int,
    ilk_soyadi: Optional[str] = None,
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
    if isinstance(dogum_tarihi, str) and dogum_tarihi:
        try:
            dogum_tarihi = date.fromisoformat(dogum_tarihi)
        except ValueError:
            dogum_tarihi = None
            
    if isinstance(sigorta_giris, str) and sigorta_giris:
        try:
            sigorta_giris = date.fromisoformat(sigorta_giris)
        except ValueError:
            sigorta_giris = None
            
    if isinstance(sigorta_cikis, str) and sigorta_cikis:
        try:
            sigorta_cikis = date.fromisoformat(sigorta_cikis)
        except ValueError:
            sigorta_cikis = None

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
    ilk_soyadi: Optional[str] = None,
    hesap_no: Optional[str] = None,
    iban: Optional[str] = None,
    ogrenim_durumu: Optional[str] = None,
    cinsiyet: Optional[str] = None,
    gorevi: Optional[str] = None,
    anne_adi: Optional[str] = None,
    baba_adi: Optional[str] = None,
    dogum_yeri: Optional[str] = None,
    dogum_tarihi: Optional[date] = None,
    medeni_hali: Optional[str] = None,
    cep_no: Optional[str] = None,
    adres_bilgileri: Optional[str] = None,
    gelir_vergisi_matrahi: Optional[float] = None,
    ssk_cikis_nedeni: Optional[str] = None,
    net_maas: Optional[float] = None,
    sigorta_giris: Optional[date] = None,
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
    if ilk_soyadi is not None:
        talep.Ilk_Soyadi = ilk_soyadi
    if hesap_no is not None:
        talep.Hesap_No = hesap_no
    if iban is not None:
        talep.IBAN = iban
    if ogrenim_durumu is not None:
        talep.Ogrenim_Durumu = ogrenim_durumu
    if cinsiyet is not None:
        talep.Cinsiyet = cinsiyet
    if gorevi is not None:
        talep.Gorevi = gorevi
    if anne_adi is not None:
        talep.Anne_Adi = anne_adi
    if baba_adi is not None:
        talep.Baba_Adi = baba_adi
    if dogum_yeri is not None:
        talep.Dogum_Yeri = dogum_yeri
    if dogum_tarihi is not None:
        if isinstance(dogum_tarihi, str) and dogum_tarihi:
            try:
                talep.Dogum_Tarihi = date.fromisoformat(dogum_tarihi)
            except ValueError:
                pass
        else:
            talep.Dogum_Tarihi = dogum_tarihi
            
    if medeni_hali is not None:
        talep.Medeni_Hali = medeni_hali
    if cep_no is not None:
        talep.Cep_No = cep_no
    if adres_bilgileri is not None:
        talep.Adres_Bilgileri = adres_bilgileri
    if gelir_vergisi_matrahi is not None:
        talep.Gelir_Vergisi_Matrahi = Decimal(str(gelir_vergisi_matrahi))
    if ssk_cikis_nedeni is not None:
        talep.SSK_Cikis_Nedeni = ssk_cikis_nedeni
    if net_maas is not None:
        talep.Net_Maas = Decimal(str(net_maas))
        
    if sigorta_giris is not None:
        if isinstance(sigorta_giris, str) and sigorta_giris:
            try:
                talep.Sigorta_Giris = date.fromisoformat(sigorta_giris)
            except ValueError:
                pass
        else:
            talep.Sigorta_Giris = sigorta_giris
            
    if sigorta_cikis is not None:
        if isinstance(sigorta_cikis, str) and sigorta_cikis:
            try:
                talep.Sigorta_Cikis = date.fromisoformat(sigorta_cikis)
            except ValueError:
                pass
        else:
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


def approve_calisan_talep_hr(db: Session, talep_id: int, user_id: int) -> Optional[CalisanTalep]:
    """Approve employee request by HR."""
    talep = get_calisan_talep_by_id(db, talep_id)
    if not talep:
        return None
    
    talep.Is_Onay_Veren_Kullanici_ID = user_id
    talep.Is_Onay_Tarih = datetime.now()
    
    db.commit()
    db.refresh(talep)
    return talep


def approve_calisan_talep_ssk(db: Session, talep_id: int, user_id: int) -> Optional[CalisanTalep]:
    """Approve employee request by SSK."""
    talep = get_calisan_talep_by_id(db, talep_id)
    if not talep:
        return None
    
    talep.SSK_Onay_Veren_Kullanici_ID = user_id
    talep.SSK_Onay_Tarih = datetime.now()
    
    # Gümüşbulut Logic: Auto-create employee or update exit date
    if talep.Talep == 'İşe Giriş':
        create_calisan(
            db=db,
            tc_no=talep.TC_No,
            adi=talep.Adi,
            soyadi=talep.Soyadi,
            sube_id=talep.Sube_ID,
            hesap_no=talep.Hesap_No,
            iban=talep.IBAN,
            net_maas=talep.Net_Maas,
            sigorta_giris=talep.Sigorta_Giris,
            sigorta_cikis=talep.Sigorta_Cikis,
            aktif_pasif=True
        )
    elif talep.Talep == 'İşten Çıkış':
        update_calisan(
            db=db,
            tc_no=talep.TC_No,
            sigorta_cikis=talep.Sigorta_Cikis,
            aktif_pasif=False  # Typically disabled when they exit
        )
    
    db.commit()
    db.refresh(talep)
    return talep


# ============================================================================
# MOBIL ROSTER (GİRİŞ / ÇIKIŞ) QUERIES
# ============================================================================

def calculate_haversine_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """
    Calculate the great-circle distance between two points on Earth using Haversine formula.
    Returns distance in meters.
    """
    R = 6371000.0  # Earth radius in meters
    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    delta_phi = math.radians(lat2 - lat1)
    delta_lambda = math.radians(lon2 - lon1)

    a = (math.sin(delta_phi / 2.0) ** 2 +
         math.cos(phi1) * math.cos(phi2) * (math.sin(delta_lambda / 2.0) ** 2))
    c = 2.0 * math.atan2(math.sqrt(a), math.sqrt(1.0 - a))
    return R * c


# --- Barkod Queries ---

def generate_unique_barcode_token(db: Session) -> str:
    """Generate a crypto-safe 32-char hex token for QR barcode."""
    while True:
        token = secrets.token_hex(16)  # 16 bytes = 32 hex chars
        existing = db.execute(select(Barkod).where(Barkod.barkod_kodu == token)).scalar_one_or_none()
        if not existing:
            return token


def create_barkod(db: Session, sube_id: int, olusturan_id: int) -> Barkod:
    """Create a new active QR barcode for a branch."""
    token = generate_unique_barcode_token(db)
    barkod = Barkod(
        sube_id=sube_id,
        barkod_kodu=token,
        aktif=True,
        olusturan_id=olusturan_id,
        olusturma_zamani=datetime.now()
    )
    db.add(barkod)
    db.commit()
    db.refresh(barkod)
    return barkod


def get_barkod_by_token(db: Session, token: str) -> Optional[Barkod]:
    """Get barcode record by token string."""
    stmt = select(Barkod).where(Barkod.barkod_kodu == token)
    return db.execute(stmt).scalar_one_or_none()


def get_barkod_by_id(db: Session, barkod_id: int) -> Optional[Barkod]:
    """Get barcode record by primary key."""
    stmt = select(Barkod).where(Barkod.id == barkod_id)
    return db.execute(stmt).scalar_one_or_none()


def get_barkodlar_by_sube(db: Session, sube_id: Optional[int] = None) -> List[Barkod]:
    """List barcodes, optionally filtered by branch, ordered by creation desc."""
    stmt = select(Barkod)
    if sube_id:
        stmt = stmt.where(Barkod.sube_id == sube_id)
    stmt = stmt.order_by(desc(Barkod.olusturma_zamani))
    return list(db.execute(stmt).scalars().all())


def toggle_barkod_durum(db: Session, barkod_id: int) -> Optional[Barkod]:
    """Toggle active/passive state of a barcode."""
    barkod = get_barkod_by_id(db, barkod_id)
    if not barkod:
        return None
    barkod.aktif = not barkod.aktif
    db.commit()
    db.refresh(barkod)
    return barkod


# --- Vardiya Red Deneme Query ---

def log_vardiya_red_deneme(
    db: Session,
    neden: str,
    calisan_id: Optional[str] = None,
    sube_id: Optional[int] = None,
    barkod_id: Optional[int] = None,
    islem_tipi: Optional[str] = None,
    enlem: Optional[float] = None,
    boylam: Optional[float] = None,
    konum_dogrulugu_m: Optional[float] = None,
    bolge_mesafesi_m: Optional[float] = None,
    cihaz_id: Optional[str] = None,
    kullanici_araci: Optional[str] = None,
    ip_adresi: Optional[str] = None
) -> VardiyaRedDeneme:
    """Log a rejected check-in/out attempt to vardiya_red_deneme table."""
    red = VardiyaRedDeneme(
        calisan_id=calisan_id,
        sube_id=sube_id,
        barkod_id=barkod_id,
        islem_tipi=islem_tipi,
        neden=neden,
        deneme_zamani=datetime.now(),
        enlem=Decimal(str(round(enlem, 6))) if enlem is not None else None,
        boylam=Decimal(str(round(boylam, 6))) if boylam is not None else None,
        konum_dogrulugu_m=Decimal(str(round(konum_dogrulugu_m, 1))) if konum_dogrulugu_m is not None else None,
        bolge_mesafesi_m=Decimal(str(round(bolge_mesafesi_m, 1))) if bolge_mesafesi_m is not None else None,
        cihaz_id=cihaz_id[:64] if cihaz_id else None,
        kullanici_araci=kullanici_araci[:255] if kullanici_araci else None,
        ip_adresi=ip_adresi[:45] if ip_adresi else None
    )
    db.add(red)
    db.commit()
    db.refresh(red)
    return red


# --- Vardiya Kayıt & Log Queries ---

def get_last_vardiya_kayit_for_calisan(db: Session, tc_no: str) -> Optional[VardiyaKayit]:
    """Get the most recent non-deleted shift record for an employee."""
    stmt = (
        select(VardiyaKayit)
        .where(VardiyaKayit.calisan_id == tc_no, VardiyaKayit.silindi == False)
        .order_by(desc(VardiyaKayit.kayit_zamani))
        .limit(1)
    )
    return db.execute(stmt).scalar_one_or_none()


def create_mobil_vardiya_kayit(
    db: Session,
    calisan_tc: str,
    sube_id: int,
    barkod_id: int,
    islem_tipi: str,
    istemci_zamani: Optional[datetime],
    enlem: float,
    boylam: float,
    konum_dogrulugu_m: float,
    bolge_mesafesi_m: float,
    cihaz_id: str,
    kullanici_araci: Optional[str],
    platform: Optional[str],
    ekran: Optional[str],
    ip_adresi: Optional[str],
    mukerrer_uyari: bool = False
) -> VardiyaKayit:
    """Create a mobile shift check-in/out record from phone."""
    server_time = datetime.now()
    kayit = VardiyaKayit(
        calisan_id=calisan_tc,
        sube_id=sube_id,
        barkod_id=barkod_id,
        islem_tipi=islem_tipi,
        kaynak="TELEFON",
        kayit_zamani=server_time,
        istemci_zamani=istemci_zamani,
        enlem=Decimal(str(round(enlem, 6))),
        boylam=Decimal(str(round(boylam, 6))),
        konum_dogrulugu_m=Decimal(str(round(konum_dogrulugu_m, 1))),
        bolge_mesafesi_m=Decimal(str(round(bolge_mesafesi_m, 1))),
        cihaz_id=cihaz_id[:64] if cihaz_id else None,
        kullanici_araci=kullanici_araci[:255] if kullanici_araci else None,
        platform=platform[:64] if platform else None,
        ekran=ekran[:20] if ekran else None,
        ip_adresi=ip_adresi[:45] if ip_adresi else None,
        mukerrer_uyari=mukerrer_uyari,
        silindi=False,
        olusturma_zamani=server_time
    )
    db.add(kayit)
    db.commit()
    db.refresh(kayit)
    return kayit


def create_manuel_vardiya_kayit(
    db: Session,
    calisan_tc: str,
    sube_id: int,
    islem_tipi: str,
    kayit_zamani: datetime,
    olusturan_id: int,
    gerekce: str
) -> VardiyaKayit:
    """Create a manual shift check-in/out record with required audit log."""
    kayit = VardiyaKayit(
        calisan_id=calisan_tc,
        sube_id=sube_id,
        barkod_id=None,
        islem_tipi=islem_tipi,
        kaynak="MANUEL",
        kayit_zamani=kayit_zamani,
        istemci_zamani=None,
        enlem=None,
        boylam=None,
        konum_dogrulugu_m=None,
        bolge_mesafesi_m=None,
        cihaz_id=None,
        kullanici_araci=None,
        platform=None,
        ekran=None,
        ip_adresi=None,
        mukerrer_uyari=False,
        olusturan_id=olusturan_id,
        silindi=False,
        olusturma_zamani=datetime.now()
    )
    db.add(kayit)
    db.flush()  # get kayit.id

    # Create audit log
    log = VardiyaKayitLog(
        kayit_id=kayit.id,
        islem="EKLE",
        kullanici_id=olusturan_id,
        islem_zamani=datetime.now(),
        gerekce=gerekce,
        eski_deger=None,
        yeni_deger={
            "calisan_id": calisan_tc,
            "sube_id": sube_id,
            "islem_tipi": islem_tipi,
            "kaynak": "MANUEL",
            "kayit_zamani": kayit_zamani.isoformat(),
            "olusturan_id": olusturan_id
        }
    )
    db.add(log)
    db.commit()
    db.refresh(kayit)
    return kayit


def update_vardiya_kayit(
    db: Session,
    kayit_id: int,
    islem_tipi: str,
    kayit_zamani: datetime,
    kullanici_id: int,
    gerekce: str
) -> Optional[VardiyaKayit]:
    """Update a shift record with required audit log (Permission #77)."""
    kayit = db.execute(select(VardiyaKayit).where(VardiyaKayit.id == kayit_id)).scalar_one_or_none()
    if not kayit or kayit.silindi:
        return None

    eski_deger = {
        "islem_tipi": kayit.islem_tipi,
        "kayit_zamani": kayit.kayit_zamani.isoformat() if kayit.kayit_zamani else None
    }

    kayit.islem_tipi = islem_tipi
    kayit.kayit_zamani = kayit_zamani

    yeni_deger = {
        "islem_tipi": islem_tipi,
        "kayit_zamani": kayit_zamani.isoformat()
    }

    log = VardiyaKayitLog(
        kayit_id=kayit.id,
        islem="GUNCELLE",
        kullanici_id=kullanici_id,
        islem_zamani=datetime.now(),
        gerekce=gerekce,
        eski_deger=eski_deger,
        yeni_deger=yeni_deger
    )
    db.add(log)
    db.commit()
    db.refresh(kayit)
    return kayit


def soft_delete_vardiya_kayit(
    db: Session,
    kayit_id: int,
    kullanici_id: int,
    gerekce: str
) -> Optional[VardiyaKayit]:
    """Soft delete a shift record with required audit log (Permission #77)."""
    kayit = db.execute(select(VardiyaKayit).where(VardiyaKayit.id == kayit_id)).scalar_one_or_none()
    if not kayit or kayit.silindi:
        return None

    eski_deger = {
        "calisan_id": kayit.calisan_id,
        "sube_id": kayit.sube_id,
        "islem_tipi": kayit.islem_tipi,
        "kaynak": kayit.kaynak,
        "kayit_zamani": kayit.kayit_zamani.isoformat() if kayit.kayit_zamani else None,
        "silindi": False
    }

    kayit.silindi = True

    log = VardiyaKayitLog(
        kayit_id=kayit.id,
        islem="SIL",
        kullanici_id=kullanici_id,
        islem_zamani=datetime.now(),
        gerekce=gerekce,
        eski_deger=eski_deger,
        yeni_deger={"silindi": True}
    )
    db.add(log)
    db.commit()
    db.refresh(kayit)
    return kayit


def get_vardiya_kayitlar(
    db: Session,
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    sube_id: Optional[int] = None,
    calisan_tc: Optional[str] = None,
    islem_tipi: Optional[str] = None,
    kaynak: Optional[str] = None,
    show_deleted: bool = False,
    page: int = 1,
    per_page: int = 50
) -> Tuple[List[VardiyaKayit], int]:
    """
    Get paginated shift records with filtering, ordered by kayit_zamani desc.
    Returns (records, total_count).
    """
    stmt = select(VardiyaKayit)
    if not show_deleted:
        stmt = stmt.where(VardiyaKayit.silindi == False)

    if start_date:
        stmt = stmt.where(VardiyaKayit.kayit_zamani >= datetime.combine(start_date, datetime.min.time()))
    if end_date:
        stmt = stmt.where(VardiyaKayit.kayit_zamani <= datetime.combine(end_date, datetime.max.time()))
    if sube_id:
        stmt = stmt.where(VardiyaKayit.sube_id == sube_id)
    if calisan_tc:
        stmt = stmt.where(VardiyaKayit.calisan_id == calisan_tc)
    if islem_tipi:
        stmt = stmt.where(VardiyaKayit.islem_tipi == islem_tipi)
    if kaynak:
        stmt = stmt.where(VardiyaKayit.kaynak == kaynak)

    count_stmt = select(func.count()).select_from(stmt.subquery())
    total_count = db.execute(count_stmt).scalar() or 0

    stmt = stmt.order_by(desc(VardiyaKayit.kayit_zamani))
    offset = (max(1, page) - 1) * per_page
    stmt = stmt.offset(offset).limit(per_page)

    records = list(db.execute(stmt).scalars().all())
    return records, total_count


def get_all_vardiya_kayitlar_for_export(
    db: Session,
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    sube_id: Optional[int] = None,
    calisan_tc: Optional[str] = None,
    islem_tipi: Optional[str] = None,
    kaynak: Optional[str] = None
) -> List[VardiyaKayit]:
    """Get all filtered non-deleted records for Excel/Mail/Print (without pagination limit)."""
    stmt = select(VardiyaKayit).where(VardiyaKayit.silindi == False)
    if start_date:
        stmt = stmt.where(VardiyaKayit.kayit_zamani >= datetime.combine(start_date, datetime.min.time()))
    if end_date:
        stmt = stmt.where(VardiyaKayit.kayit_zamani <= datetime.combine(end_date, datetime.max.time()))
    if sube_id:
        stmt = stmt.where(VardiyaKayit.sube_id == sube_id)
    if calisan_tc:
        stmt = stmt.where(VardiyaKayit.calisan_id == calisan_tc)
    if islem_tipi:
        stmt = stmt.where(VardiyaKayit.islem_tipi == islem_tipi)
    if kaynak:
        stmt = stmt.where(VardiyaKayit.kaynak == kaynak)

    stmt = stmt.order_by(desc(VardiyaKayit.kayit_zamani))
    return list(db.execute(stmt).scalars().all())


# ============================================================================
# VARDIYA KAYIT LOG (AUDIT LOG RAPORU) QUERIES
# ============================================================================

def get_vardiya_kayit_loglar(
    db: Session,
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    islem: Optional[str] = None,
    kullanici_id: Optional[int] = None,
    kayit_id: Optional[int] = None,
    page: int = 1,
    per_page: int = 50
) -> Tuple[List[VardiyaKayitLog], int]:
    """
    Get paginated vardiya_kayit_log records with filtering, ordered by islem_zamani desc.
    Returns (records, total_count).
    """
    stmt = select(VardiyaKayitLog)

    if start_date:
        stmt = stmt.where(VardiyaKayitLog.islem_zamani >= datetime.combine(start_date, datetime.min.time()))
    if end_date:
        stmt = stmt.where(VardiyaKayitLog.islem_zamani <= datetime.combine(end_date, datetime.max.time()))
    if islem:
        stmt = stmt.where(VardiyaKayitLog.islem == islem)
    if kullanici_id:
        stmt = stmt.where(VardiyaKayitLog.kullanici_id == kullanici_id)
    if kayit_id:
        stmt = stmt.where(VardiyaKayitLog.kayit_id == kayit_id)

    # Count total
    count_stmt = select(func.count()).select_from(stmt.subquery())
    total_count = db.execute(count_stmt).scalar() or 0

    stmt = stmt.order_by(desc(VardiyaKayitLog.islem_zamani))
    offset = (max(1, page) - 1) * per_page
    stmt = stmt.offset(offset).limit(per_page)

    records = list(db.execute(stmt).scalars().all())
    return records, total_count


def get_all_vardiya_kayit_loglar_for_export(
    db: Session,
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    islem: Optional[str] = None,
    kullanici_id: Optional[int] = None,
    kayit_id: Optional[int] = None
) -> List[VardiyaKayitLog]:
    """Get all filtered log records for Excel/Mail/Print."""
    stmt = select(VardiyaKayitLog)

    if start_date:
        stmt = stmt.where(VardiyaKayitLog.islem_zamani >= datetime.combine(start_date, datetime.min.time()))
    if end_date:
        stmt = stmt.where(VardiyaKayitLog.islem_zamani <= datetime.combine(end_date, datetime.max.time()))
    if islem:
        stmt = stmt.where(VardiyaKayitLog.islem == islem)
    if kullanici_id:
        stmt = stmt.where(VardiyaKayitLog.kullanici_id == kullanici_id)
    if kayit_id:
        stmt = stmt.where(VardiyaKayitLog.kayit_id == kayit_id)

    stmt = stmt.order_by(desc(VardiyaKayitLog.islem_zamani))
    return list(db.execute(stmt).scalars().all())
