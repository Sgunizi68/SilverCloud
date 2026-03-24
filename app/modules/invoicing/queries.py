"""
Invoicing Domain Database Queries
CRUD operations for EFatura, Odeme, Nakit, Gelir, and related entities.
Uses SQLAlchemy 2.0 style with pagination and filtering.
"""

from typing import Optional, List
from datetime import date, datetime
from sqlalchemy import select, func
from sqlalchemy.orm import Session
from app.models import (
    EFatura, B2BEkstre, DigerHarcama, Odeme, OdemeReferans,
    Nakit, POSHareketleri, Gelir, GelirEkstra, EFaturaReferans,
    Kategori, Sube, YemekCeki, Mutabakat, Cari
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
    donem: Optional[int] = None,
    giden_fatura: Optional[bool] = None,
    search: Optional[str] = None,
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    can_view_gizli: bool = False
) -> List[EFatura]:
    """Get e-invoices with optional filtering."""
    stmt = select(EFatura)
    
    if sube_id is not None:
        stmt = stmt.where(EFatura.Sube_ID == sube_id)
    
    if kategori_id is not None:
        stmt = stmt.where(EFatura.Kategori_ID == kategori_id)
    
    # Note: EFatura has no Durum column; status filter removed

    if donem is not None:
        stmt = stmt.where(EFatura.Donem == donem)
        
    if giden_fatura is not None:
        stmt = stmt.where(EFatura.Giden_Fatura == giden_fatura)
        
    if search:
        search_filter = f"%{search}%"
        stmt = stmt.where(
            (EFatura.Fatura_Numarasi.ilike(search_filter)) |
            (EFatura.Alici_Unvani.ilike(search_filter)) |
            (EFatura.Aciklama.ilike(search_filter))
        )

    if end_date is not None:
        stmt = stmt.where(EFatura.Kayit_Tarihi <= end_date)
    
    # Category and Invoice privacy filtering
    if not can_view_gizli:
        from sqlalchemy import or_
        from sqlalchemy.sql.functions import coalesce
        
        # Join with Kategori to check Kategori.Gizli
        # We use an outer join to keep invoices without categories (if any)
        stmt = stmt.outerjoin(Kategori, EFatura.Kategori_ID == Kategori.Kategori_ID)
        
        # Rule: (Kategori.Gizli == 0 OR Kategori.Gizli IS NULL) AND (EFatura.Ozel == 0)
        stmt = stmt.where(
            coalesce(Kategori.Gizli, False) == False,
            EFatura.Ozel == False
        )
    
    stmt = stmt.order_by(EFatura.Donem.desc(), EFatura.Fatura_ID.desc())
    stmt = stmt.offset(skip).limit(limit)
    return db.scalars(stmt).all()


def get_efatura_by_id(db: Session, efatura_id: int) -> Optional[EFatura]:
    """Get e-invoice by ID."""
    return db.get(EFatura, efatura_id)


def get_efatura_by_no(db: Session, fatura_no: str) -> Optional[EFatura]:
    """Get e-invoice by Fatura_Numarasi."""
    stmt = select(EFatura).where(EFatura.Fatura_Numarasi == fatura_no)
    return db.scalars(stmt).first()


def create_efatura(
    db: Session,
    sube_id: int,
    kategori_id: int,
    fatura_no: str,
    fatura_tutari: float,
    kayit_tarihi: Optional[date] = None,
    fatura_tarihi: Optional[date] = None,
    alici_unvani: Optional[str] = "Bölünmüş Fatura Alıcısı",
    donem: Optional[int] = None,
    aciklama: Optional[str] = None,
    ozel: bool = False,
    gunluk: bool = False,
    giden: bool = False
) -> EFatura:
    """Create a new e-invoice with correct field names."""
    if kayit_tarihi is None:
        kayit_tarihi = datetime.now()
    if fatura_tarihi is None:
        fatura_tarihi = date.today()
    
    new_efatura = EFatura(
        Sube_ID=sube_id,
        Kategori_ID=kategori_id,
        Fatura_Numarasi=fatura_no,
        Tutar=fatura_tutari,
        Fatura_Tarihi=fatura_tarihi,
        Alici_Unvani=alici_unvani,
        Donem=donem or 0,
        Aciklama=aciklama,
        Ozel=ozel,
        Gunluk_Harcama=gunluk,
        Giden_Fatura=giden,
        Kayit_Tarihi=kayit_tarihi
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
    kategori_id: Optional[int] = None,
    donem: Optional[int] = None,
    ozel: Optional[bool] = None,
    gunluk_harcama: Optional[bool] = None,
    aciklama: Optional[str] = None
) -> Optional[EFatura]:
    """Update an e-invoice."""
    efatura = get_efatura_by_id(db, efatura_id)
    if not efatura:
        return None
    
    if fatura_no is not None:
        efatura.Fatura_Numarasi = fatura_no
    if fatura_tutari is not None:
        efatura.Tutar = fatura_tutari
    if kategori_id is not None:
        efatura.Kategori_ID = kategori_id if kategori_id != 0 else None
    if donem is not None:
        efatura.Donem = donem
    if ozel is not None:
        efatura.Ozel = ozel
    if gunluk_harcama is not None:
        efatura.Gunluk_Harcama = gunluk_harcama
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


def create_efatura_bulk(
    db: Session,
    efatura_list: List[dict]
) -> dict:
    """
    Bulk create e-invoices.
    efatura_list should be a list of dicts with EFatura fields.
    Returns counts of added and skipped records.
    """
    added = 0
    skipped = 0
    
    for data in efatura_list:
        try:
            # Check for existing invoice to avoid duplicates
            fatura_no = data.get("Fatura_No")
            if not fatura_no:
                skipped += 1
                continue
                
            existing = db.scalars(
                select(EFatura).where(
                    EFatura.Fatura_Numarasi == fatura_no,
                    EFatura.Sube_ID == data["Sube_ID"]
                )
            ).first()
            if existing:
                skipped += 1
                continue
            
            # Parse date if string
            fatura_tarihi = data.get("Fatura_Tarihi")
            if isinstance(fatura_tarihi, str):
                try:
                    fatura_tarihi = datetime.strptime(fatura_tarihi, "%Y-%m-%d").date()
                except ValueError:
                    fatura_tarihi = datetime.now().date()
            elif not fatura_tarihi:
                fatura_tarihi = datetime.now().date()

            # Business Rules refinement (Reversed)
            is_giden = data.get("Giden_Fatura", False)
            kategori_id = None
            
            if not is_giden:
                # Gelen fatura (Incoming) -> Look up Kategori_ID from EFaturaReferans
                alici_unvani = data.get("Alici_Unvani", "").strip()
                if alici_unvani:
                    ref = db.scalars(
                        select(EFaturaReferans).where(
                            EFaturaReferans.Alici_Unvani == alici_unvani
                        )
                    ).first()
                    if ref:
                        kategori_id = ref.Kategori_ID
            else:
                # Giden fatura (Outgoing) -> Kategori_ID should remain empty (None)
                kategori_id = None

            new_efatura = EFatura(
                Sube_ID=data["Sube_ID"],
                Kategori_ID=kategori_id,
                Fatura_Numarasi=fatura_no,
                Alici_Unvani=data.get("Alici_Unvani", "Bilinmiyor"),
                Alici_VKN_TCKN=data.get("Alici_VKN_TCKN"),
                Tutar=data.get("Fatura_Tutari", 0.0),
                Fatura_Tarihi=fatura_tarihi,
                Donem=data.get("Donem", 0),
                Giden_Fatura=is_giden,
                Ozel=data.get("Ozel", False),
                Gunluk_Harcama=data.get("Gunluk_Harcama", False),
                Aciklama=None,  # User requested this be kept empty
            )
            db.add(new_efatura)
            added += 1
        except Exception as e:
            db.rollback()
            raise e
            
    db.commit()
    return {"added": added, "skipped": skipped}


def get_bolunmus_faturalar(db: Session, donem: Optional[int] = None) -> List[dict]:
    """
    Get split invoices (parent-child relationship).
    Parent is identified by category 'Bölünmüş Fatura'.
    Children match 'PARENT_NO-N' naming convention.
    Returns one row per child split, including parent metadata.
    Parents with no children are returned as a single row with NULL child fields.
    """
    from sqlalchemy import text
    
    sql_query = """
    SELECT
        s.Fatura_Numarasi  AS Ana_Fatura,
        s.Tutar            AS Ana_Tutar,
        s.Alici_Unvani     AS Ana_Alici_Unvani,
        s.Fatura_Tarihi    AS Ana_Fatura_Tarihi,
        s.Aciklama         AS Ana_Aciklama,
        s.Donem            AS Ana_Donem,
        s.Gunluk_Harcama   AS Ana_Gunluk,
        s.Sube_ID          AS Ana_Sube_ID,
        t.Fatura_ID,
        t.Fatura_Numarasi,
        t.Alici_Unvani,
        t.Fatura_Tarihi,
        t.Tutar,
        t.Kategori_ID,
        k_t.Kategori_Adi   AS Kategori_Adi,
        t.Aciklama,
        t.Donem,
        t.Ozel,
        t.Gunluk_Harcama,
        t.Sube_ID
    FROM e_Fatura s
    INNER JOIN Kategori k
        ON s.Kategori_ID = k.Kategori_ID
        AND k.Kategori_ID = 88
    LEFT JOIN e_Fatura t
        ON t.Fatura_Numarasi LIKE CONCAT(s.Fatura_Numarasi, '-%')
        AND t.Fatura_Numarasi != s.Fatura_Numarasi
    LEFT JOIN Kategori k_t ON t.Kategori_ID = k_t.Kategori_ID
    """
    
    if donem:
        sql_query += f" WHERE s.Donem = {donem}"
        
    sql_query += " ORDER BY s.Fatura_Numarasi, t.Fatura_Numarasi;"
    
    result = db.execute(text(sql_query))
    rows = []
    for row in result:
        rows.append(row._asdict())
    return rows



# ============================================================================
# B2B EKSTRE (B2B STATEMENTS) QUERIES
# ============================================================================

def create_b2b_ekstre_bulk(
    db: Session,
    ekstre_list: List[dict]
) -> dict:
    """
    Bulk create B2B ekstre records with optimized batch processing.
    """
    added = 0
    skipped = 0
    
    if not ekstre_list:
        return {"added": 0, "skipped": 0}

    # Preparation: Collect keys for batch lookups
    all_sube_ids = set()
    all_fis_nos = set()
    all_fatura_nos = set()
    processed_rows = []

    for data in ekstre_list:
        sube_id = data.get("Sube_ID")
        if not sube_id: continue
        all_sube_ids.add(sube_id)

        # Parse and normalize Date
        tarih_val = data.get("Tarih")
        if isinstance(tarih_val, str):
            try:
                tarih = datetime.strptime(tarih_val, "%Y-%m-%d").date()
            except ValueError:
                tarih = datetime.now().date()
        elif isinstance(tarih_val, (date, datetime)):
            tarih = tarih_val if isinstance(tarih_val, date) else tarih_val.date()
        else:
            tarih = datetime.now().date()

        fis_no = (data.get("Fis_No") or "").strip()
        fatura_no = (data.get("Fatura_No") or "").strip()
        
        all_fis_nos.add(fis_no)
        if fatura_no: all_fatura_nos.add(fatura_no)
        
        # Store for second pass
        processed_rows.append({
            "data": data,
            "tarih": tarih,
            "fis_no": fis_no,
            "fatura_no": fatura_no,
            "sube_id": sube_id,
            "borc": float(data.get("Borc", 0.0)),
            "alacak": float(data.get("Alacak", 0.0))
        })

    if not processed_rows:
        return {"added": 0, "skipped": 0}

    # Batch Fetch 1: Existing B2BEkstre for duplicate check
    # We fetch all matching Fis_No for the involved branches
    existing_stmt = select(B2BEkstre).where(
        B2BEkstre.Sube_ID.in_(list(all_sube_ids)),
        B2BEkstre.Fis_No.in_(list(all_fis_nos))
    )
    existing_ekstreler = db.scalars(existing_stmt).all()
    # Lookup map: (Fis_No, Tarih, Sube_ID, Borc, Alacak) -> Record
    ekstre_map = {
        (e.Fis_No, e.Tarih, e.Sube_ID, float(e.Borc), float(e.Alacak)): e 
        for e in existing_ekstreler
    }

    # Batch Fetch 2: Relevant EFaturalar for description updates
    # Combine Fatura_No and Fis_No as they are both used for matching
    invoice_match_candidates = all_fatura_nos.union(all_fis_nos)
    efatura_stmt = select(EFatura).where(
        EFatura.Sube_ID.in_(list(all_sube_ids)),
        EFatura.Fatura_Numarasi.in_(list(invoice_match_candidates))
    )
    existing_efaturalar = db.scalars(efatura_stmt).all()
    # Lookup map: (Fatura_Numarasi, Sube_ID) -> Record
    efatura_map = {
        (f.Fatura_Numarasi, f.Sube_ID): f 
        for f in existing_efaturalar
    }

    # Processing Loop
    for item in processed_rows:
        data = item["data"]
        tarih = item["tarih"]
        fis_no = item["fis_no"]
        fatura_no = item["fatura_no"]
        sube_id = item["sube_id"]
        borc = item["borc"]
        alacak = item["alacak"]

        # 1. EFatura description update logic
        match_invoice_no = fatura_no or fis_no
        aciklama_from_b2b = data.get("Aciklama")
        
        if match_invoice_no and aciklama_from_b2b:
            ef = efatura_map.get((match_invoice_no, sube_id))
            if ef and not ef.Aciklama:
                ef.Aciklama = aciklama_from_b2b

        # 2. Duplicate Check
        if (fis_no, tarih, sube_id, borc, alacak) in ekstre_map:
            skipped += 1
            continue

        # 3. Create new record
        donem = int(str(tarih.year)[-2:] + str(tarih.month).zfill(2))
        
        new_ekstre = B2BEkstre(
            Tarih=tarih,
            Fis_No=fis_no,
            Fis_Turu=data.get("Fis_Turu"),
            Aciklama=data.get("Aciklama"),
            Borc=borc,
            Alacak=alacak,
            Toplam_Bakiye=data.get("Toplam_Bakiye", 0.0),
            Fatura_No=fatura_no,
            Fatura_Metni=data.get("Fatura_Metni"),
            Donem=donem,
            Sube_ID=sube_id,
        )
        db.add(new_ekstre)
        # Update map to prevent duplicates within the same file too
        ekstre_map[(fis_no, tarih, sube_id, borc, alacak)] = new_ekstre
        added += 1

    try:
        db.commit()
    except Exception as e:
        db.rollback()
        raise e

    return {"added": added, "skipped": skipped}


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

def create_odeme_bulk(
    db: Session,
    odeme_list: List[dict]
) -> dict:
    """
    Bulk create Odeme records.
    Returns counts of added and skipped records.
    """
    added = 0
    skipped = 0
    
    # Pre-fetch all OdemeReferans to match Kategori_ID
    odeme_referanslar = db.execute(select(OdemeReferans)).scalars().all()
    
    for data in odeme_list:
        try:
            # Parse date if string
            tarih = data.get("Odeme_Tarihi")
            if isinstance(tarih, str):
                try:
                    tarih = datetime.strptime(tarih, "%Y-%m-%d").date()
                except ValueError:
                    tarih = datetime.now().date()
            elif not tarih:
                tarih = datetime.now().date()
            
            # Allow duplicates? GumusBulut Odeme typically allows multiple identical records but maybe we check exact matches to prevent accidental double-submit
            aciklama = data.get("Aciklama", "")
            
            existing = db.scalars(
                select(Odeme).where(
                    Odeme.Sube_ID == data["Sube_ID"],
                    Odeme.Tarih == tarih,
                    Odeme.Tip == data.get("Tip", ""),
                    Odeme.Hesap_Adi == data.get("Hesap_Adi", ""),
                    Odeme.Tutar == data.get("Odeme_Tutari", 0.0),
                    Odeme.Aciklama == aciklama
                )
            ).first()
            
            if existing:
                skipped += 1
                continue
            
            # Find Kategori_ID from odeme_referanslar
            kategori_id = None
            if aciklama:
                for ref in odeme_referanslar:
                    if ref.Referans_Metin and ref.Referans_Metin in aciklama:
                        kategori_id = ref.Kategori_ID
                        break
                
            new_odeme = Odeme(
                Sube_ID=data["Sube_ID"],
                Tip=data.get("Tip", ""),
                Hesap_Adi=data.get("Hesap_Adi", ""),
                Tarih=tarih,
                Aciklama=aciklama,
                Tutar=data.get("Odeme_Tutari", 0.0),
                Kategori_ID=kategori_id, # Assigned from referanslar
                Donem=data.get("Donem")
            )
            db.add(new_odeme)
            added += 1
        except Exception as e:
            db.rollback()
            raise e
            
    db.commit()
    return {"added": added, "skipped": skipped}


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
    stmt = stmt.offset(skip).limit(limit)
    return db.scalars(stmt).all()


# ============================================================================
# ODEME (PAYMENT) QUERIES
# ============================================================================

def get_odemeler(
    db: Session,
    sube_id: Optional[int] = None,
    donem: Optional[int] = None,
    kategori_id: Optional[int] = None,
    search_term: Optional[str] = None,
    sadece_kategorisiz: bool = False,
    skip: int = 0,
    limit: int = 5000
) -> List[Odeme]:
    """Get payments with exact filtering matching the legacy UI constraints."""
    from sqlalchemy import select, or_, cast, String
    
    stmt = select(Odeme)
    
    if sube_id is not None:
        stmt = stmt.where(Odeme.Sube_ID == sube_id)
        
    if donem is not None:
        stmt = stmt.where(Odeme.Donem == donem)
        
    if sadece_kategorisiz:
        stmt = stmt.where(Odeme.Kategori_ID.is_(None))
    elif kategori_id is not None:
        stmt = stmt.where(Odeme.Kategori_ID == kategori_id)
        
    if search_term:
        term = f"%{search_term}%"
        stmt = stmt.where(
            or_(
                Odeme.Tip.ilike(term),
                Odeme.Hesap_Adi.ilike(term),
                Odeme.Aciklama.ilike(term),
                cast(Odeme.Tutar, String).ilike(term)
            )
        )
        
    stmt = stmt.order_by(Odeme.Tarih.desc()).offset(skip).limit(limit)
    return db.scalars(stmt).all()

def update_odeme(
    db: Session,
    odeme_id: int,
    kategori_id: Optional[int] = None,
    donem: Optional[int] = None,
    kategori_clear: bool = False,
    donem_clear: bool = False
) -> Optional[Odeme]:
    """Update payment category or period fields inline."""
    odeme = db.get(Odeme, odeme_id)
    if not odeme:
        return None
        
    if kategori_clear:
        odeme.Kategori_ID = None
    elif kategori_id is not None:
        odeme.Kategori_ID = kategori_id
        
    if donem_clear:
        odeme.Donem = None
    elif donem is not None:
        odeme.Donem = donem
        
    db.commit()
    db.refresh(odeme)
    return odeme


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
    harcama = get_diger_harcama_by_id(db, harcama_id, can_view_gizli=True)
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
    harcama = get_diger_harcama_by_id(db, harcama_id, can_view_gizli=True)
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


def create_pos_hareketi_bulk(
    db: Session,
    pos_list: List[dict]
) -> dict:
    """
    Bulk create POS transactions.
    pos_list should be a list of dicts with POSHareketleri fields.
    Returns counts of added and skipped records.
    """
    added = 0
    skipped = 0
    
    for data in pos_list:
        try:
            # Check for existing transaction to avoid duplicates
            # Using Islem_Tarihi, Islem_Tutari, and Sube_ID as a unique-ish combination
            islem_tarihi = data.get("Islem_Tarihi")
            if isinstance(islem_tarihi, str):
                try:
                    islem_tarihi = datetime.strptime(islem_tarihi, "%Y-%m-%d").date()
                except ValueError:
                    islem_tarihi = None
            
            if not islem_tarihi:
                skipped += 1
                continue

            existing = db.scalars(
                select(POSHareketleri).where(
                    POSHareketleri.Islem_Tarihi == islem_tarihi,
                    POSHareketleri.Islem_Tutari == data["Islem_Tutari"],
                    POSHareketleri.Sube_ID == data["Sube_ID"]
                )
            ).first()
            
            if existing:
                skipped += 1
                continue
            
            # Parse Hesaba_Gecis if string
            hesaba_gecis = data.get("Hesaba_Gecis")
            if isinstance(hesaba_gecis, str):
                try:
                    hesaba_gecis = datetime.strptime(hesaba_gecis, "%Y-%m-%d").date()
                except ValueError:
                    hesaba_gecis = islem_tarihi # Fallback
            elif not hesaba_gecis:
                hesaba_gecis = islem_tarihi

            new_hareketi = POSHareketleri(
                Islem_Tarihi=islem_tarihi,
                Hesaba_Gecis=hesaba_gecis,
                Para_Birimi=data.get("Para_Birimi", "TRY"),
                Islem_Tutari=data["Islem_Tutari"],
                Kesinti_Tutari=data.get("Kesinti_Tutari", 0.00),
                Net_Tutar=data.get("Net_Tutar"),
                Sube_ID=data["Sube_ID"]
            )
            db.add(new_hareketi)
            added += 1
            
        except Exception as e:
            print(f"Error skipping POS row: {e}")
            skipped += 1
            continue
            
    db.commit()
    return {"added": added, "skipped": skipped}

# ============================================================================
# DIGER HARCAMA (OTHER EXPENSES) QUERIES
# ============================================================================

def get_diger_harcamalar(
    db: Session,
    skip: int = 0,
    limit: int = 100,
    sube_id: Optional[int] = None,
    donem: Optional[int] = None,
    kategori_id: Optional[int] = None,
    harcama_tipi: Optional[str] = None,
    can_view_gizli: bool = False
) -> List[DigerHarcama]:
    """Get Diger Harcamalar with optional filtering."""
    stmt = select(DigerHarcama)
    
    if not can_view_gizli:
        stmt = stmt.join(Kategori).where(Kategori.Gizli == False)
    
    if sube_id is not None:
        stmt = stmt.where(DigerHarcama.Sube_ID == sube_id)
    if donem is not None:
        stmt = stmt.where(DigerHarcama.Donem == donem)
    if kategori_id is not None:
        stmt = stmt.where(DigerHarcama.Kategori_ID == kategori_id)
    if harcama_tipi:
        stmt = stmt.where(DigerHarcama.Harcama_Tipi == harcama_tipi)
    
    stmt = stmt.offset(skip).limit(limit)
    return db.scalars(stmt).all()

def get_diger_harcama_by_id(db: Session, harcama_id: int, can_view_gizli: bool = False) -> Optional[DigerHarcama]:
    """Get a single Diger Harcama by ID with visibility check."""
    stmt = select(DigerHarcama).where(DigerHarcama.Harcama_ID == harcama_id)
    if not can_view_gizli:
        # Join with Kategori to check Gizli status
        stmt = stmt.join(Kategori).where(Kategori.Gizli == False)
    
    return db.scalars(stmt).first()

def create_diger_harcama(
    db: Session,
    data: dict,
    imaj: Optional[bytes] = None,
    imaj_adi: Optional[str] = None
) -> DigerHarcama:
    """Create a new Diger Harcama record."""
    new_harcama = DigerHarcama(
        Alici_Adi=data.get('Alici_Adi'),
        Belge_Numarasi=data.get('Belge_Numarasi'),
        Belge_Tarihi=data.get('Belge_Tarihi'),
        Donem=data.get('Donem'),
        Tutar=data.get('Tutar'),
        Kategori_ID=data.get('Kategori_ID'),
        Harcama_Tipi=data.get('Harcama_Tipi'),
        Gunluk_Harcama=data.get('Gunluk_Harcama', False),
        Sube_ID=data.get('Sube_ID'),
        Açıklama=data.get('Açıklama'),
        Imaj=imaj,
        Imaj_Adi=imaj_adi
    )
    db.add(new_harcama)
    db.commit()
    db.refresh(new_harcama)
    return new_harcama

def update_diger_harcama(
    db: Session,
    harcama_id: int,
    data: dict,
    imaj: Optional[bytes] = None,
    imaj_adi: Optional[str] = None,
    clear_image: bool = False
) -> Optional[DigerHarcama]:
    """Update a Diger Harcama record."""
    harcama = get_diger_harcama_by_id(db, harcama_id, can_view_gizli=True)
    if not harcama:
        return None
        
    for key, value in data.items():
        if hasattr(harcama, key) and value is not None:
            setattr(harcama, key, value)
            
    if clear_image:
        harcama.Imaj = None
        harcama.Imaj_Adi = None
    elif imaj is not None:
        harcama.Imaj = imaj
        harcama.Imaj_Adi = imaj_adi
        
    db.commit()
    db.refresh(harcama)
    return harcama

def delete_diger_harcama(db: Session, harcama_id: int) -> bool:
    """Delete a Diger Harcama record."""
    harcama = get_diger_harcama_by_id(db, harcama_id, can_view_gizli=True)
    if not harcama:
        return False
        
    db.delete(harcama)
    db.commit()
    return True

# ============================================================================
# GELIR EKSTRA (REVENUE EXTRA) QUERIES
# ============================================================================

def update_tabak_sayisi_bulk(db: Session, sube_id: int, data_list: List[dict]) -> dict:
    """
    Update Tabak_Sayisi in GelirEkstra for multiple dates.
    If record doesn't exist, it might be skipped or created with default values.
    Traditional GümüşBulut behavior is to update existing records.
    """
    updated_count = 0
    not_found_count = 0
    errors = []

    for index, item in enumerate(data_list):
        try:
            islem_tarihi = item.get('islem_tarihi')
            tabak_sayisi = item.get('tabak_sayisi')

            if not islem_tarihi:
                continue

            # Convert to date object if it's a string
            if isinstance(islem_tarihi, str):
                islem_tarihi = datetime.strptime(islem_tarihi, '%Y-%m-%d').date()

            # Search for existing record
            stmt = select(GelirEkstra).where(
                GelirEkstra.Sube_ID == sube_id,
                GelirEkstra.Tarih == islem_tarihi
            )
            record = db.scalars(stmt).first()

            if record:
                record.Tabak_Sayisi = int(tabak_sayisi)
                updated_count += 1
            else:
                # In SilverCloud, if record doesn't exist, we skip it
                # as GelirEkstra records are usually created by robotpos daily sync.
                not_found_count += 1
                
        except Exception as e:
            errors.append(f"Row {index + 1}: {str(e)}")

    try:
        db.commit()
    except Exception as e:
        db.rollback()
        return {"error": f"Database commit failed: {str(e)}"}

    return {
        "updated_records": updated_count,
        "records_not_found": not_found_count,
        "errors": errors
    }

# ============================================================================
# YEMEK CEKI (MEAL TICKETS) QUERIES
# ============================================================================

def get_yemek_cekileri(
    db: Session,
    skip: int = 0,
    limit: int = 100,
    sube_id: Optional[int] = None,
    donem: Optional[int] = None
) -> List[YemekCeki]:
    """Get meal tickets with optional filtering."""
    stmt = select(YemekCeki)
    
    if sube_id is not None:
        stmt = stmt.where(YemekCeki.Sube_ID == sube_id)
    if donem is not None:
        # Donem is YYMM format. Example: 2602 -> Feb 2026
        year = 2000 + (donem // 100)
        month = donem % 100
        from sqlalchemy import extract
        stmt = stmt.where(
            (extract('year', YemekCeki.Tarih) == year) &
            (extract('month', YemekCeki.Tarih) == month)
        )
    
    stmt = stmt.order_by(YemekCeki.Tarih.desc())
    stmt = stmt.offset(skip).limit(limit)
    return db.scalars(stmt).all()

def get_yemek_ceki_by_id(db: Session, ceki_id: int) -> Optional[YemekCeki]:
    """Get a meal ticket by ID."""
    return db.get(YemekCeki, ceki_id)

def create_yemek_ceki(
    db: Session,
    data: dict,
    imaj: Optional[bytes] = None,
    imaj_adi: Optional[str] = None
) -> YemekCeki:
    """Create a new meal ticket."""
    new_ceki = YemekCeki(
        Kategori_ID=data.get('Kategori_ID'),
        Tarih=data.get('Tarih'),
        Tutar=data.get('Tutar'),
        Odeme_Tarih=data.get('Odeme_Tarih'),
        Ilk_Tarih=data.get('Ilk_Tarih'),
        Son_Tarih=data.get('Son_Tarih'),
        Sube_ID=data.get('Sube_ID'),
        Imaj=imaj,
        Imaj_Adi=imaj_adi
    )
    db.add(new_ceki)
    db.commit()
    db.refresh(new_ceki)
    return new_ceki

def delete_yemek_ceki(db: Session, ceki_id: int) -> bool:
    """Delete a meal ticket."""
    ceki = get_yemek_ceki_by_id(db, ceki_id)
    if not ceki:
        return False
    db.delete(ceki)
    db.commit()
    return True

def update_yemek_ceki(
    db: Session,
    ceki_id: int,
    data: dict,
    imaj: Optional[bytes] = None,
    imaj_adi: Optional[str] = None,
    clear_imaj: bool = False
) -> Optional[YemekCeki]:
    """Update a meal ticket."""
    ceki = get_yemek_ceki_by_id(db, ceki_id)
    if not ceki:
        return None
        
    if 'Kategori_ID' in data: ceki.Kategori_ID = data['Kategori_ID']
    if 'Tarih' in data: ceki.Tarih = data['Tarih']
    if 'Tutar' in data: ceki.Tutar = data['Tutar']
    if 'Odeme_Tarih' in data: ceki.Odeme_Tarih = data['Odeme_Tarih']
    if 'Ilk_Tarih' in data: ceki.Ilk_Tarih = data['Ilk_Tarih']
    if 'Son_Tarih' in data: ceki.Son_Tarih = data['Son_Tarih']
    if 'Sube_ID' in data: ceki.Sube_ID = data['Sube_ID']
    
    if clear_imaj:
        ceki.Imaj = None
        ceki.Imaj_Adi = None
    elif imaj is not None:
        ceki.Imaj = imaj
        ceki.Imaj_Adi = imaj_adi
        
    db.commit()
    db.refresh(ceki)
    return ceki

# ==========================================
# NAKIT QUERIES
# ==========================================

from app.models import Nakit
from sqlalchemy import extract

def get_nakitler(db: Session, sube_id: int = None, donem: int = None, limit: int = 1000) -> list[Nakit]:
    """
    Belirli Şube ve/veya döneme göre Nakit kayıtlarını getirir.
    Sıralama: Tarihe göre Azalan (DESC)
    """
    query = db.query(Nakit)
    if sube_id:
        query = query.filter(Nakit.Sube_ID == sube_id)
    if donem:
        query = query.filter(Nakit.Donem == donem)
        
    return query.order_by(Nakit.Tarih.desc()).limit(limit).all()

def get_nakit_by_id(db: Session, nakit_id: int) -> Optional[Nakit]:
    """Nakit ID'sine göre tekil kayıt getirir."""
    return db.query(Nakit).filter(Nakit.Nakit_ID == nakit_id).first()

def create_nakit(db: Session, data: dict, imaj: Optional[bytes] = None, imaj_adi: Optional[str] = None) -> Nakit:
    """Yeni Nakit kaydı ekler."""
    yeni_nakit = Nakit(
        Tarih=data.get('Tarih'),
        Tutar=data.get('Tutar'),
        Tip=data.get('Tip', 'Bankaya Yatan'),
        Donem=data.get('Donem'),
        Sube_ID=data.get('Sube_ID'),
        Imaj=imaj,
        Imaj_Adı=imaj_adi
    )
    db.add(yeni_nakit)
    db.commit()
    db.refresh(yeni_nakit)
    return yeni_nakit

def update_nakit(db: Session, nakit_id: int, data: dict, imaj: Optional[bytes] = None, imaj_adi: Optional[str] = None, clear_imaj: bool = False) -> Optional[Nakit]:
    """Mevcut Nakit kaydını günceller. Opsiyonel resim güncelleme/silme barındırır."""
    db_nakit = get_nakit_by_id(db, nakit_id)
    if not db_nakit:
        return None

    if 'Tarih' in data: db_nakit.Tarih = data['Tarih']
    if 'Tutar' in data: db_nakit.Tutar = data['Tutar']
    if 'Tip' in data: db_nakit.Tip = data['Tip']
    if 'Donem' in data: db_nakit.Donem = data['Donem']
    if 'Sube_ID' in data: db_nakit.Sube_ID = data['Sube_ID']
            
    if clear_imaj:
        db_nakit.Imaj = None
        db_nakit.Imaj_Adı = None
    elif imaj is not None:
        db_nakit.Imaj = imaj
        db_nakit.Imaj_Adı = imaj_adi
        
    db.commit()
    db.refresh(db_nakit)
    return db_nakit

def delete_nakit(db: Session, nakit_id: int) -> bool:
    """Mevcut Nakit kaydını ID'sine göre siler."""
    db_nakit = get_nakit_by_id(db, nakit_id)
    if not db_nakit:
        return False
        
    db.delete(db_nakit)
    db.commit()
    return True

# ==========================================
# GELİR QUERIES (Matrix / Pivot Tablo İçin)
# ==========================================

from app.models import Gelir, Kategori, UstKategori
from datetime import date as _date
import calendar

def get_gelir_kategorileri(db: Session, can_view_gizli: bool = False):
    """
    Gelir Girişi ekranında sol sütunda (satır başlıkları) yer alacak 
    Kategorileri döner. Sadece Tip='Gelir' olanlar.
    """
    query = db.query(Kategori).filter(
        Kategori.Tip == 'Gelir',
        Kategori.Aktif_Pasif == True
    )
    if not can_view_gizli:
        query = query.filter(Kategori.Gizli == False)
        
    kategoriler = query.order_by(Kategori.Kategori_Adi).all()
        
    return kategoriler

def get_gelirler_by_donem(db: Session, sube_id: int, year: int, month: int) -> dict:
    """
    Belirli Şube, Yıl ve Ay için Gelir kayıtlarını döner.
    Dictionary yapısı şöyledir: { (Kategori_ID, Gun): Tutar ... }
    """
    query = db.query(Gelir).filter(Gelir.Sube_ID == sube_id)
    query = query.filter(extract('year', Gelir.Tarih) == year)
    query = query.filter(extract('month', Gelir.Tarih) == month)
    
    kayitlar = query.all()
    
    # Hücreleri (Matris) kolay okuyabilmek için mapleme yapıyoruz:
    matrix_data = {}
    for g in kayitlar:
        gun = g.Tarih.day
        kat_id = g.Kategori_ID
        matrix_data[(kat_id, gun)] = float(g.Tutar)
        
    return matrix_data

def get_gelir_ekstra_by_donem(db: Session, sube_id: int, year: int, month: int):
    """
    Belirli döneme ait GelirEkstra kayıtlarını çeker (örn: RobotPos_Tutar, ZRapor_Tutar)
    """
    from app.models import GelirEkstra
    kayitlar = db.query(GelirEkstra).filter(
        GelirEkstra.Sube_ID == sube_id,
        extract('year', GelirEkstra.Tarih) == year,
        extract('month', GelirEkstra.Tarih) == month
    ).all()
    
    ekstra_data = {}
    for r in kayitlar:
        gun = r.Tarih.day
        ekstra_data[gun] = {
            'RobotPos_Tutar': float(r.RobotPos_Tutar) if r.RobotPos_Tutar else 0.0,
            'ZRapor_Tutar': float(r.ZRapor_Tutar) if r.ZRapor_Tutar else 0.0,
            'Tabak_Sayisi': r.Tabak_Sayisi or 0
        }
    return ekstra_data

def get_gunluk_harcamalar_by_donem(db: Session, sube_id: int, year: int, month: int):
    """
    Belirli döneme ait Gunluk_Harcama (eFatura ve DigerHarcama) tablo değerlerini çeker.
    "FİŞ / FATURA" gösterimi (read-only) için kullanılır.
    """
    from app.models import DigerHarcama, EFatura
    
    diger_harcamalar = db.query(DigerHarcama).filter(
        DigerHarcama.Sube_ID == sube_id,
        extract('year', DigerHarcama.Belge_Tarihi) == year,
        extract('month', DigerHarcama.Belge_Tarihi) == month,
        DigerHarcama.Gunluk_Harcama == True
    ).all()
    
    efaturalar = db.query(EFatura).filter(
        EFatura.Sube_ID == sube_id,
        extract('year', EFatura.Fatura_Tarihi) == year,
        extract('month', EFatura.Fatura_Tarihi) == month,
        EFatura.Gunluk_Harcama == True
    ).all()
    
    harcama_data = {}
    
    for h in diger_harcamalar:
        gun = h.Belge_Tarihi.day
        if gun not in harcama_data:
            harcama_data[gun] = {'efatura': 0.0, 'diger': 0.0}
        harcama_data[gun]['diger'] += float(h.Tutar) if h.Tutar else 0.0
        
    for e in efaturalar:
        gun = e.Fatura_Tarihi.day
        if gun not in harcama_data:
            harcama_data[gun] = {'efatura': 0.0, 'diger': 0.0}
        harcama_data[gun]['efatura'] += float(e.Tutar) if e.Tutar else 0.0
        
    return harcama_data

def save_bulk_gelirler(db: Session, sube_id: int, year: int, month: int, payload_data: dict) -> bool:
    """
    Matrix üzerindeki değişiklikleri alır ve kaydeder.
    Gelir için key: "KategoriID-Gun" -> (örn: "23-5")
    GelirEkstra için key: "RobotPos-Gun" -> (örn: "RobotPos-5") veya "TabakSayisi-Gun"
    """
    from app.models import GelirEkstra
    try:
        # Gelir Tablosu Mevcutlar
        mevcut_query = db.query(Gelir).filter(
            Gelir.Sube_ID == sube_id,
            extract('year', Gelir.Tarih) == year,
            extract('month', Gelir.Tarih) == month
        ).all()
        mevcut_map = { (g.Kategori_ID, g.Tarih.day): g for g in mevcut_query }
        
        # GelirEkstra Tablosu Mevcutlar
        ekstra_query = db.query(GelirEkstra).filter(
            GelirEkstra.Sube_ID == sube_id,
            extract('year', GelirEkstra.Tarih) == year,
            extract('month', GelirEkstra.Tarih) == month
        ).all()
        ekstra_map = { e.Tarih.day: e for e in ekstra_query }
        
        for key, tutar_val in payload_data.items():
            if not key or tutar_val is None: continue
            
            parts = key.split('-')
            if len(parts) != 2: continue
            
            prefix = parts[0]
            gun = int(parts[1])
            
            gelir_tarihi = _date(year, month, gun)
            
            # GelirEkstra alanları ("RobotPos" gibi)
            if prefix in ['RobotPos', 'ZRapor', 'TabakSayisi']:
                try:
                    tutar = float(tutar_val)
                except ValueError:
                    tutar = 0.0
                    
                if gun in ekstra_map:
                    ekstra_kayit = ekstra_map[gun]
                    if prefix == 'RobotPos' and ekstra_kayit.RobotPos_Tutar != tutar:
                        ekstra_kayit.RobotPos_Tutar = tutar
                    elif prefix == 'ZRapor' and ekstra_kayit.ZRapor_Tutar != tutar:
                        ekstra_kayit.ZRapor_Tutar = tutar
                    elif prefix == 'TabakSayisi' and ekstra_kayit.Tabak_Sayisi != tutar:
                        ekstra_kayit.Tabak_Sayisi = int(tutar)
                else:
                    new_e = GelirEkstra(
                        Sube_ID=sube_id,
                        Tarih=gelir_tarihi,
                        RobotPos_Tutar=tutar if prefix == 'RobotPos' else 0.0,
                        ZRapor_Tutar=tutar if prefix == 'ZRapor' else 0.0,
                        Tabak_Sayisi=int(tutar) if prefix == 'TabakSayisi' else 0
                    )
                    db.add(new_e)
                    ekstra_map[gun] = new_e # add mapping so subsequent updates for same day reuse it
            else:
                # Normal Kategori Geliri
                try:
                    kat_id = int(prefix)
                    tutar = float(tutar_val)
                except ValueError:
                    continue
                
                if (kat_id, gun) in mevcut_map:
                    mevcut_kayit = mevcut_map[(kat_id, gun)]
                    if mevcut_kayit.Tutar != tutar:
                        mevcut_kayit.Tutar = tutar
                else:
                    new_g = Gelir(
                        Sube_ID=sube_id,
                        Kategori_ID=kat_id,
                        Tarih=gelir_tarihi,
                        Tutar=tutar
                    )
                    db.add(new_g)
                    
        db.commit()
        return True
    except Exception as e:
        db.rollback()
        print(f"Bulk Save Gelir Hatası: {e}")
        return False


# ============================================================================
# REPORT QUERIES
# ============================================================================

def get_odeme_raporu_data(
    db: Session,
    sube_id: int,
    donem_list: Optional[List[int]] = None,
    kategori_list: Optional[List[int]] = None
) -> dict:
    """
    Get grouped Odeme data for report: Donem -> Kategori -> Hesap_Adi
    """
    from decimal import Decimal
    from collections import defaultdict
    
    stmt = select(Odeme).where(Odeme.Sube_ID == sube_id)
    
    if donem_list:
        stmt = stmt.where(Odeme.Donem.in_(donem_list))
    
    if kategori_list:
        stmt = stmt.where(Odeme.Kategori_ID.in_(kategori_list))
        
    stmt = stmt.order_by(Odeme.Donem.desc(), Odeme.Tarih.desc())
    
    records = db.scalars(stmt).all()
    
    # Hierarchical grouping
    # structure: { donem: { kat_id: { hesap_adi: [details] } } }
    report_tree = defaultdict(lambda: defaultdict(lambda: defaultdict(list)))
    
    # We need category names
    kat_ids = {r.Kategori_ID for r in records if r.Kategori_ID}
    kat_map = {}
    if kat_ids:
        kats = db.scalars(select(Kategori).where(Kategori.Kategori_ID.in_(list(kat_ids)))).all()
        kat_map = {k.Kategori_ID: k.Kategori_Adi for k in kats}
        
    for r in records:
        d = r.Donem or 0
        k_id = r.Kategori_ID or 0
        h_name = r.Hesap_Adi or "Tanımsız Hesap"
        
        report_tree[d][k_id][h_name].append(r)
        
    # Build final structure with totals
    data = []
    grand_total = Decimal('0')
    total_records = len(records)
    
    sorted_donemler = sorted(report_tree.keys(), reverse=True)
    
    for d in sorted_donemler:
        donem_total = Decimal('0')
        donem_count = 0
        kategoriler_list = []
        
        sorted_kat_ids = sorted(report_tree[d].keys())
        for k_id in sorted_kat_ids:
            kat_total = Decimal('0')
            kat_count = 0
            hesaplar_list = []
            kat_name = kat_map.get(k_id, "Kategorilendirilmemiş")
            
            sorted_hesaplar = sorted(report_tree[d][k_id].keys())
            for h_name in sorted_hesaplar:
                h_total = Decimal('0')
                h_count = 0
                details = []
                
                for r in report_tree[d][k_id][h_name]:
                    val = Decimal(str(r.Tutar or 0))
                    h_total += val
                    h_count += 1
                    details.append({
                        'Odeme_ID': r.Odeme_ID,
                        'Tarih': r.Tarih.strftime('%d.%m.%Y') if r.Tarih else '',
                        'Aciklama': r.Aciklama,
                        'Tutar': float(val),
                        'Tip': r.Tip
                    })
                
                hesaplar_list.append({
                    'hesap_adi': h_name,
                    'hesap_total': float(h_total),
                    'record_count': h_count,
                    'details': details
                })
                kat_total += h_total
                kat_count += h_count
                
            kategoriler_list.append({
                'kategori_id': k_id,
                'kategori_adi': kat_name,
                'kategori_total': float(kat_total),
                'record_count': kat_count,
                'banka_hesaplari': hesaplar_list
            })
            donem_total += kat_total
            donem_count += kat_count
            
        data.append({
            'donem': d,
            'donem_total': float(donem_total),
            'record_count': donem_count,
            'kategoriler': kategoriler_list
        })
        grand_total += donem_total
        
    return {
        'data': data,
        'totals': {
            'grand_total': float(grand_total)
        },
        'total_records': total_records
    }


def get_fatura_raporu_data(
    db: Session,
    sube_id: int,
    donem_list: Optional[List[int]] = None,
    kategori_list: Optional[List[int]] = None
) -> dict:
    """
    Get grouped EFatura data for report: Donem -> Kategori -> Fatura Details
    """
    from decimal import Decimal
    from collections import defaultdict
    
    stmt = select(EFatura).where(EFatura.Sube_ID == sube_id)
    
    if donem_list:
        stmt = stmt.where(EFatura.Donem.in_(donem_list))
    
    if kategori_list:
        stmt = stmt.where(EFatura.Kategori_ID.in_(kategori_list))
        
    stmt = stmt.order_by(EFatura.Donem.desc(), EFatura.Fatura_Tarihi.desc())
    
    records = db.scalars(stmt).all()
    
    # Hierarchical grouping
    # structure: { donem: { kat_id: [faturalar] } }
    report_tree = defaultdict(lambda: defaultdict(list))
    
    # We need category names
    kat_ids = {r.Kategori_ID for r in records if r.Kategori_ID}
    kat_map = {}
    if kat_ids:
        kats = db.scalars(select(Kategori).where(Kategori.Kategori_ID.in_(list(kat_ids)))).all()
        kat_map = {k.Kategori_ID: k.Kategori_Adi for k in kats}
        
    for r in records:
        d = r.Donem or 0
        k_id = r.Kategori_ID or 0
        report_tree[d][k_id].append(r)
        
    # Build final structure with totals
    data = []
    grand_total = Decimal('0')
    total_records = len(records)
    
    sorted_donemler = sorted(report_tree.keys(), reverse=True)
    
    for d in sorted_donemler:
        donem_total = Decimal('0')
        donem_count = 0
        kategoriler_list = []
        
        sorted_kat_ids = sorted(report_tree[d].keys())
        for k_id in sorted_kat_ids:
            kat_total = Decimal('0')
            kat_count = 0
            faturalar_list = []
            kat_name = kat_map.get(k_id, "Kategorilendirilmemiş")
            
            for r in report_tree[d][k_id]:
                val = Decimal(str(r.Tutar or 0))
                kat_total += val
                kat_count += 1
                faturalar_list.append({
                    'fatura_id': r.Fatura_ID,
                    'fatura_numarasi': r.Fatura_Numarasi,
                    'alici_unvani': r.Alici_Unvani,
                    'fatura_tarihi': r.Fatura_Tarihi.strftime('%d.%m.%Y') if r.Fatura_Tarihi else '',
                    'tutar': float(val),
                    'aciklama': r.Aciklama,
                    'giden_fatura': r.Giden_Fatura,
                    'ozel': r.Ozel,
                    'gunluk_harcama': r.Gunluk_Harcama
                })
            
            kategoriler_list.append({
                'kategori_id': k_id,
                'kategori_adi': kat_name,
                'kategori_total': float(kat_total),
                'record_count': kat_count,
                'faturalar': faturalar_list
            })
            donem_total += kat_total
            donem_count += kat_count
            
        data.append({
            'donem': d,
            'donem_total': float(donem_total),
            'record_count': donem_count,
            'kategoriler': kategoriler_list
        })
        grand_total += donem_total
        
    return {
        'data': data,
        'totals': {
            'grand_total': float(grand_total)
        },
        'total_records': total_records
    }


def get_fatura_diger_harcama_rapor(
    db: Session,
    sube_id: int,
    donem_list: Optional[List[int]] = None,
    kategori_list: Optional[List[int]] = None
) -> dict:
    """
    Combined report for EFatura (Incoming) and DigerHarcama.
    Grouped by Donem -> Kategori.
    """
    from decimal import Decimal
    from collections import defaultdict

    # 1. Query EFatura (Gelen Faturalar only)
    stmt_efatura = select(EFatura).where(
        EFatura.Sube_ID == sube_id,
        EFatura.Giden_Fatura == False
    )
    if donem_list:
        stmt_efatura = stmt_efatura.where(EFatura.Donem.in_(donem_list))
    if kategori_list:
        stmt_efatura = stmt_efatura.where(EFatura.Kategori_ID.in_(kategori_list))
    
    efatura_records = db.scalars(stmt_efatura).all()

    # 2. Query DigerHarcama
    stmt_diger = select(DigerHarcama).where(DigerHarcama.Sube_ID == sube_id)
    if donem_list:
        stmt_diger = stmt_diger.where(DigerHarcama.Donem.in_(donem_list))
    if kategori_list:
        stmt_diger = stmt_diger.where(DigerHarcama.Kategori_ID.in_(kategori_list))
        
    diger_records = db.scalars(stmt_diger).all()

    # 3. Combine and Group
    # structure: { donem: { kat_id: [records] } }
    report_tree = defaultdict(lambda: defaultdict(list))
    all_kat_ids = set()

    for r in efatura_records:
        d = r.Donem or 0
        k_id = r.Kategori_ID or 0
        all_kat_ids.add(k_id)
        report_tree[d][k_id].append({
            'type': 'EFatura',
            'id': r.Fatura_ID,
            'belge_numarasi': r.Fatura_Numarasi,
            'karsi_taraf_adi': r.Alici_Unvani,
            'tarih': r.Fatura_Tarihi,
            'tutar': r.Tutar,
            'aciklama': r.Aciklama,
            'etiket': 'e-Fatura',
            'ozel': r.Ozel,
            'gunluk_harcama': r.Gunluk_Harcama
        })

    for r in diger_records:
        d = r.Donem or 0
        k_id = r.Kategori_ID or 0
        all_kat_ids.add(k_id)
        report_tree[d][k_id].append({
            'type': 'DigerHarcama',
            'id': r.Harcama_ID,
            'belge_numarasi': r.Belge_Numarasi or '-',
            'karsi_taraf_adi': r.Alici_Adi,
            'tarih': r.Belge_Tarihi,
            'tutar': r.Tutar,
            'aciklama': r.Açıklama,
            'etiket': r.Harcama_Tipi,
            'ozel': False,
            'gunluk_harcama': r.Gunluk_Harcama
        })

    # Fetch category names
    kat_map = {}
    if all_kat_ids:
        kats = db.scalars(select(Kategori).where(Kategori.Kategori_ID.in_(list(all_kat_ids)))).all()
        kat_map = {k.Kategori_ID: k.Kategori_Adi for k in kats}

    # Build final structure with totals
    data = []
    grand_total = Decimal('0')
    total_records_count = len(efatura_records) + len(diger_records)
    
    sorted_donemler = sorted(report_tree.keys(), reverse=True)
    
    for d in sorted_donemler:
        donem_total = Decimal('0')
        donem_count = 0
        kategoriler_list = []
        
        # Sort categories by name
        kat_ids_in_donem = list(report_tree[d].keys())
        # Sort by category name from kat_map, "Bilinmiyor" for 0
        kat_ids_in_donem.sort(key=lambda x: kat_map.get(x, "Bilinmiyor") if x != 0 else "ZZZ")

        for k_id in kat_ids_in_donem:
            kat_total = Decimal('0')
            kat_count = 0
            kayitlar_list = []
            kat_name = kat_map.get(k_id, "Kategorilendirilmemiş")
            
            # Sort records within category by date desc, then by name
            records_in_kat = report_tree[d][k_id]
            records_in_kat.sort(key=lambda x: (x['tarih'], x['karsi_taraf_adi']), reverse=True)

            for r in records_in_kat:
                val = Decimal(str(r['tutar'] or 0))
                kat_total += val
                kat_count += 1
                
                # Format for display
                rec_copy = r.copy()
                rec_copy['tarih'] = r['tarih'].strftime('%Y-%m-%d') if r['tarih'] else ''
                rec_copy['tutar'] = float(val)
                kayitlar_list.append(rec_copy)
            
            kategoriler_list.append({
                'kategori_id': k_id,
                'kategori_adi': kat_name,
                'kategori_total': float(kat_total),
                'record_count': kat_count,
                'kayitlar': kayitlar_list
            })
            donem_total += kat_total
            donem_count += kat_count
            
        data.append({
            'donem': d,
            'donem_total': float(donem_total),
            'record_count': donem_count,
            'kategoriler': kategoriler_list
        })
        grand_total += donem_total
        
    return {
        'data': data,
        'totals': {
            'grand_total': float(grand_total)
        },
        'total_records': total_records_count
    }

def get_pos_kontrol_dashboard_data(db: Session, sube_id: int, donem: int):
    """
    Get POS reconciliation data for a specific branch and period.
    donem is in YYMM format (e.g., 2603 for March 2026).
    """
    from datetime import date, timedelta
    from decimal import Decimal
    from sqlalchemy import and_
    import calendar

    # Convert donem (YYMM) to date range
    year = 2000 + (donem // 100)
    month = donem % 100
    
    _, last_day_num = calendar.monthrange(year, month)
    start_date = date(year, month, 1)
    end_date = date(year, month, last_day_num)

    # 1. Identify Categories
    # Gelir POS Category
    stmt_pos = select(Kategori).where(Kategori.Kategori_Adi == "POS")
    pos_kat = db.scalars(stmt_pos).first()
    pos_kat_id = pos_kat.Kategori_ID if pos_kat else None

    # Odeme Kredi Karti Category
    stmt_kk = select(Kategori).where(Kategori.Kategori_Adi == "Kredi Kartı Ödemesi")
    kk_kat = db.scalars(stmt_kk).first()
    kk_kat_id = kk_kat.Kategori_ID if kk_kat else None

    # Bank Commission/Fee Category (Legacy used ID 81)
    stmt_kesinti = select(Kategori).where(
        (Kategori.Kategori_Adi == "Banka Komisyon") | 
        (Kategori.Kategori_ID == 81)
    )
    kesinti_kat = db.scalars(stmt_kesinti).first()
    kesinti_kat_id = kesinti_kat.Kategori_ID if kesinti_kat else 81 # Fallback to 81

    # 2. Fetch Data
    # Gelir records
    stmt_gelir = select(Gelir).where(
        and_(
            Gelir.Sube_ID == sube_id,
            Gelir.Kategori_ID == pos_kat_id,
            Gelir.Tarih >= start_date,
            Gelir.Tarih <= end_date
        )
    )
    gelir_records = db.scalars(stmt_gelir).all()
    gelir_map = {}
    for r in gelir_records:
        gelir_map[r.Tarih] = gelir_map.get(r.Tarih, Decimal('0')) + r.Tutar

    # POS Hareketleri
    stmt_pos_h = select(POSHareketleri).where(
        and_(
            POSHareketleri.Sube_ID == sube_id,
            POSHareketleri.Islem_Tarihi >= start_date,
            POSHareketleri.Islem_Tarihi <= end_date
        )
    )
    pos_h_records = db.scalars(stmt_pos_h).all()
    pos_h_map = {}
    for r in pos_h_records:
        if r.Islem_Tarihi not in pos_h_map:
            pos_h_map[r.Islem_Tarihi] = {
                'islem': Decimal('0'),
                'kesinti': Decimal('0'),
                'net': Decimal('0'),
                'matched_odeme': Decimal('0')
            }
        pos_h_map[r.Islem_Tarihi]['islem'] += r.Islem_Tutari
        pos_h_map[r.Islem_Tarihi]['kesinti'] += r.Kesinti_Tutari
        pos_h_map[r.Islem_Tarihi]['net'] += r.Net_Tutar

    # Odeme records
    stmt_odeme = select(Odeme).where(
        and_(
            Odeme.Sube_ID == sube_id,
            Odeme.Tarih >= start_date,
            Odeme.Tarih <= end_date + timedelta(days=5) # Some payments might land a few days later
        )
    )
    odeme_records = db.scalars(stmt_odeme).all()
    
    # Organize Odeme for matching
    # Map by (Tarih, Tutar) for KK payments
    kk_odeme_map = {}
    for r in odeme_records:
        if r.Kategori_ID == kk_kat_id:
            key = (r.Tarih, r.Tutar)
            kk_odeme_map[key] = kk_odeme_map.get(key, 0) + 1

    # Kesinti (Bank Fees) from Odeme - usually recorded on the day it hits the bank
    kesinti_odeme_map = {}
    for r in odeme_records:
        if r.Kategori_ID == kesinti_kat_id:
            # Bank fees are usually negative in database if it's an 'Odeme' but here we want positive for display
            kesinti_odeme_map[r.Tarih] = kesinti_odeme_map.get(r.Tarih, Decimal('0')) + abs(r.Tutar)

    # 3. Process Matching
    # Re-process POS Hareketleri for Odeme matching based on Hesaba_Gecis
    for r in pos_h_records:
        key = (r.Hesaba_Gecis, r.Islem_Tutari)
        if key in kk_odeme_map and kk_odeme_map[key] > 0:
            pos_h_map[r.Islem_Tarihi]['matched_odeme'] += r.Islem_Tutari
            kk_odeme_map[key] -= 1

    # 4. Generate Daily Response
    results = []
    curr = start_date
    ok_count = 0
    fail_count = 0
    
    while curr <= end_date:
        g_pos = gelir_map.get(curr, Decimal('0'))
        p_data = pos_h_map.get(curr, {
            'islem': Decimal('0'),
            'kesinti': Decimal('0'),
            'net': Decimal('0'),
            'matched_odeme': Decimal('0')
        })
        
        # In the report, 'Odeme' field usually shows what bank sent vs what arrived
        # But per the logic, the 'Odeme' column in the dashboard is the sum of matched KK payments
        o_val = p_data['matched_odeme']
        
        # Bank fees for the NEXT day (as per legacy logic, fees might be logged differently)
        # Actually legacy logic used: next_day = date + timedelta(days=1)
        next_day = curr + timedelta(days=1)
        o_kesinti = kesinti_odeme_map.get(next_day, Decimal('0'))
        
        # Kontrol POS: Gelir POS == POS Hareketleri
        k_pos = "OK" if abs(g_pos - p_data['islem']) < Decimal('0.05') else "FAIL"
        
        # Kontrol Kesinti: POS Kesinti == Odeme Kesinti
        k_kesinti = "OK" if abs(p_data['kesinti'] - o_kesinti) < Decimal('0.05') else "FAIL"
        
        if k_pos == "OK" and k_kesinti == "OK":
            ok_count += 1
        else:
            fail_count += 1

        results.append({
            'Tarih': curr,
            'Gelir_POS': g_pos,
            'POS_Hareketleri': p_data['islem'],
            'POS_Kesinti': p_data['kesinti'],
            'POS_Net': p_data['net'],
            'Odeme': o_val,
            'Odeme_Kesinti': o_kesinti,
            'Odeme_Net': o_val - o_kesinti,
            'Kontrol_POS': k_pos,
            'Kontrol_Kesinti': k_kesinti
        })
        curr += timedelta(days=1)

    success_rate = (ok_count / len(results)) * 100 if results else 0
    
    return {
        'data': results,
        'summary': {
            'total': len(results),
            'ok': ok_count,
            'fail': fail_count,
            'success_rate': f"{success_rate:.1f}%"
        }
    }

def get_online_kontrol_dashboard_data(db: Session, sube_id: int, donem: int):
    """
    Get Online platform reconciliation data.
    Matches Gelir (System) vs B2BEkstre (Bank/Platform Virman) vs EFatura (Commission).
    """
    from datetime import date
    from decimal import Decimal
    from sqlalchemy import and_, or_
    import calendar

    # Date range
    year = 2000 + (donem // 100)
    month = donem % 100
    _, last_day_num = calendar.monthrange(year, month)
    start_date = date(year, month, 1)
    end_date = date(year, month, last_day_num)

    platforms = [
        {"id": "yemeksepeti", "label": "Yemek Sepeti Online", "keywords": ["Yemek Sepeti", "Yemeksepeti"]},
        {"id": "trendyol", "label": "Trendyol Online", "keywords": ["Trendyol"]},
        {"id": "getir", "label": "Getir Online", "keywords": ["Getir"]},
        {"id": "migros", "label": "Migros Yemek Online", "keywords": ["Migros Yemek", "MigrosYemek", "Migros"]},
    ]

    results = []

    for p in platforms:
        # 1. Gelir Toplam
        # Search for categories including platform keywords
        p_keywords = p["keywords"]
        kat_filters = or_(*[Kategori.Kategori_Adi.ilike(f"%{k}%") for k in p_keywords])
        
        stmt_gelir = select(func.sum(Gelir.Tutar)).join(Kategori).where(
            and_(
                Gelir.Sube_ID == sube_id,
                Gelir.Tarih >= start_date,
                Gelir.Tarih <= end_date,
                kat_filters
            )
        )
        gelir_toplam = db.execute(stmt_gelir).scalar() or Decimal('0')

        # 2. Virman (B2BEkstre.Alacak < 0)
        # Search for negative Alacak entries where description contains platform keywords
        # Using platform keywords to match records like "Yemek Sepeti Online Alacak Virmanları"
        # We search specifically for "Virman" and the keyword.
        ekstre_filters = or_(*[B2BEkstre.Aciklama.ilike(f"%{k}%") for k in p_keywords])
        stmt_virman = select(B2BEkstre).where(
            and_(
                B2BEkstre.Sube_ID == sube_id,
                B2BEkstre.Tarih >= start_date,
                B2BEkstre.Tarih <= end_date,
                B2BEkstre.Alacak < 0,
                ekstre_filters,
                B2BEkstre.Aciklama.ilike('%Virman%')
            )
        )
        virman_records = db.scalars(stmt_virman).all()
        # Sum absolute value of negative Alacak
        toplam_virman = sum((abs(r.Alacak) for r in virman_records), Decimal('0'))
        # Get the day of the last transfer record
        virman_son_gun = max((r.Tarih.day for r in virman_records), default=None)

        # 3. Kısmi Gelir
        # Based on legacy screenshot, Kısmi Gelir often matches Gelir Toplam
        kismi_gelir = gelir_toplam 

        # 4. Komisyon (Check B2BEkstre Borc first, then EFatura)
        # B2BEkstre Borc often contains "Komisyon Yansıtma"
        stmt_borc_komisyon = select(func.sum(B2BEkstre.Borc)).where(
            and_(
                B2BEkstre.Sube_ID == sube_id,
                B2BEkstre.Tarih >= start_date,
                B2BEkstre.Tarih <= end_date,
                B2BEkstre.Aciklama.ilike('%Komisyon%'),
                ekstre_filters
            )
        )
        komisyon_b2b = db.execute(stmt_borc_komisyon).scalar() or Decimal('0')

        # Add EFatura if not redundant (usually they are processed into B2B but let's check)
        # If we already have B2B commissions, we trust them as the final yansıtma
        if komisyon_b2b > 0:
            komisyon_toplam = komisyon_b2b
        else:
            # Fallback to EFatura
            stmt_komisyon_ef = select(func.sum(EFatura.Tutar)).where(
                and_(
                    EFatura.Sube_ID == sube_id,
                    EFatura.Donem == donem,
                    EFatura.Giden_Fatura == False,
                    EFatura.Aciklama.ilike('%Komisyon%'),
                    or_(*[EFatura.Aciklama.ilike(f"%{k}%") for k in p_keywords])
                )
            )
            komisyon_toplam = db.execute(stmt_komisyon_ef).scalar() or Decimal('0')

        # Calculations
        fark = toplam_virman - kismi_gelir
        komisyon_yuzde = (komisyon_toplam / gelir_toplam * 100) if gelir_toplam > 0 else Decimal('0')

        results.append({
            'platform': p['label'],
            'gelir_toplam': gelir_toplam,
            'virman_son_gun': virman_son_gun or 'N/A',
            'toplam_virman': toplam_virman,
            'kismi_gelir': kismi_gelir,
            'fark': fark,
            'komisyon_toplam': komisyon_toplam,
            'komisyon_yuzde': komisyon_yuzde,
            'yuzde': (toplam_virman / gelir_toplam * 100) if gelir_toplam > 0 else Decimal('0')
        })

    # Summary Row (Genel Toplam)
    genel_toplam = {
        'platform': 'GENEL TOPLAM',
        'gelir_toplam': sum((r['gelir_toplam'] for r in results), Decimal('0')),
        'virman_son_gun': 'N/A',
        'toplam_virman': sum((r['toplam_virman'] for r in results), Decimal('0')),
        'kismi_gelir': sum((r['kismi_gelir'] for r in results), Decimal('0')),
        'fark': sum((r['fark'] for r in results), Decimal('0')),
        'komisyon_toplam': sum((r['komisyon_toplam'] for r in results), Decimal('0')),
        'komisyon_yuzde': Decimal('0'),
        'yuzde': Decimal('0')
    }
    if genel_toplam['gelir_toplam'] > 0:
        genel_toplam['komisyon_yuzde'] = (genel_toplam['komisyon_toplam'] / genel_toplam['gelir_toplam'] * 100)
        genel_toplam['yuzde'] = (genel_toplam['toplam_virman'] / genel_toplam['gelir_toplam'] * 100)

    return {
        'data': results,
        'summary': genel_toplam
    }


def get_yemek_ceki_kontrol_dashboard_data(db: Session, sube_id: int, donem: int):
    """
    Get Yemek Çeki (Meal Voucher) reconciliation data.
    Matches legacy logic exactly:
    - Period split (Onceki/Sonraki donem)
    - YemekCeki model as base
    - Cari/EFatura matching
    """
    from datetime import date
    from decimal import Decimal
    from sqlalchemy import and_, or_, func, select, text
    import calendar
    from app.models import Kategori, Gelir, EFatura, Odeme, Cari, YemekCeki

    # Date range
    year = 2000 + (donem // 100)
    month = donem % 100
    _, last_day_num = calendar.monthrange(year, month)
    period_start = date(year, month, 1)
    period_end = date(year, month, last_day_num)

    # 1. Target Categories (UstKategori ID 3: Yemek Çeki)
    # Fetch all categories under UK 3
    stmt_kats = select(Kategori).where(Kategori.Ust_Kategori_ID == 3)
    kategoriler = db.scalars(stmt_kats).all()

    # Generic Summary Stats
    total_gelir = Decimal('0')
    total_donem_tutar = Decimal('0')
    kontrol_edilen_kayit = 0

    results = []

    for kat in kategoriler:
        # 1a. Aylık Gelir for this category
        stmt_gelir = select(func.sum(Gelir.Tutar)).where(
            and_(
                Gelir.Sube_ID == sube_id,
                Gelir.Kategori_ID == kat.Kategori_ID,
                Gelir.Tarih >= period_start,
                Gelir.Tarih <= period_end
            )
        )
        grup_aylik_gelir = db.execute(stmt_gelir).scalar() or Decimal('0')

        # 1b. Linked EFatura Candidates (via Cari/OdemeReferans)
        # Find Cari names associated with this category via OdemeReferans
        stmt_refs = select(Cari.Alici_Unvani).join(OdemeReferans, Cari.Referans_ID == OdemeReferans.Referans_ID).where(
            OdemeReferans.Kategori_ID == kat.Kategori_ID
        )
        related_unvans = db.scalars(stmt_refs).all()

        # 1c. Cekler (YemekCeki records overlapping period)
        stmt_cekler = select(YemekCeki).where(
            and_(
                YemekCeki.Sube_ID == sube_id,
                YemekCeki.Kategori_ID == kat.Kategori_ID,
                YemekCeki.Ilk_Tarih <= period_end,
                YemekCeki.Son_Tarih >= period_start
            )
        )
        cekler = db.scalars(stmt_cekler).all()

        cek_rows = []
        grup_donem_tutar_total = Decimal('0')

        for cek in cekler:
            # Proportional Distribution Logic (User requested fix)
            
            # 1. Önceki Dönem Gelir
            stmt_onceki = select(func.sum(Gelir.Tutar)).where(
                and_(
                    Gelir.Kategori_ID == kat.Kategori_ID,
                    Gelir.Sube_ID == sube_id,
                    Gelir.Tarih >= cek.Ilk_Tarih,
                    Gelir.Tarih < period_start
                )
            )
            onceki_gelir = db.execute(stmt_onceki).scalar() or Decimal('0')

            # 2. Mevcut Dönem Gelir (Overlapping part of voucher with report month)
            overlap_start = max(cek.Ilk_Tarih, period_start)
            overlap_end = min(cek.Son_Tarih, period_end)
            stmt_mevcut = select(func.sum(Gelir.Tutar)).where(
                and_(
                    Gelir.Kategori_ID == kat.Kategori_ID,
                    Gelir.Sube_ID == sube_id,
                    Gelir.Tarih >= overlap_start,
                    Gelir.Tarih <= overlap_end
                )
            )
            mevcut_gelir = db.execute(stmt_mevcut).scalar() or Decimal('0')

            # 3. Sonraki Dönem Gelir
            stmt_sonraki = select(func.sum(Gelir.Tutar)).where(
                and_(
                    Gelir.Kategori_ID == kat.Kategori_ID,
                    Gelir.Sube_ID == sube_id,
                    Gelir.Tarih > period_end,
                    Gelir.Tarih <= cek.Son_Tarih
                )
            )
            sonraki_gelir = db.execute(stmt_sonraki).scalar() or Decimal('0')

            toplam_donem_geliri = onceki_gelir + mevcut_gelir + sonraki_gelir
            
            onceki_donem_tutar = Decimal('0')
            sonraki_donem_tutar = Decimal('0')
            donem_tutar = Decimal('0')

            if toplam_donem_geliri > 0:
                # Proportional distribution
                onceki_donem_tutar = (onceki_gelir / toplam_donem_geliri) * cek.Tutar
                sonraki_donem_tutar = (sonraki_gelir / toplam_donem_geliri) * cek.Tutar
                # Round to 2 decimals
                onceki_donem_tutar = onceki_donem_tutar.quantize(Decimal('0.01'))
                sonraki_donem_tutar = sonraki_donem_tutar.quantize(Decimal('0.01'))
                # Remainder goes to current period
                donem_tutar = cek.Tutar - onceki_donem_tutar - sonraki_donem_tutar
            else:
                # Fallback: Equal distribution among active periods
                has_onceki = (cek.Ilk_Tarih < period_start)
                has_sonraki = (cek.Son_Tarih > period_end)
                num_periods = (1 if has_onceki else 0) + 1 + (1 if has_sonraki else 0)
                
                base_val = (cek.Tutar / num_periods).quantize(Decimal('0.01'))
                if has_onceki: onceki_donem_tutar = base_val
                if has_sonraki: sonraki_donem_tutar = base_val
                donem_tutar = cek.Tutar - onceki_donem_tutar - sonraki_donem_tutar

            # Fatura Status Check
            # Match EFatura (Giden=True) with exact Tutar and date condition:
            # (Fatura_Tarihi - 5 days) <= (Son_Tarih + 90 days)
            stmt_fatura = select(EFatura).where(
                and_(
                    EFatura.Sube_ID == sube_id,
                    EFatura.Giden_Fatura == True,
                    EFatura.Tutar == cek.Tutar,
                    func.date_sub(EFatura.Fatura_Tarihi, text("INTERVAL 5 DAY")) <= func.date_add(cek.Son_Tarih, text("INTERVAL 90 DAY"))
                )
            )
            fat_match = db.scalars(stmt_fatura).first()

            # Odeme Check
            # Search for Odeme with "Ödemesi" category matching platform name
            stmt_odeme_kat = select(Kategori.Kategori_ID).where(
                and_(
                    Kategori.Kategori_Adi.ilike(f"%{kat.Kategori_Adi}%"),
                    Kategori.Kategori_Adi.ilike("%Ödemesi%")
                )
            )
            odeme_kat_id = db.execute(stmt_odeme_kat).scalar()
            
            odeme_tutari = Decimal('0')
            if odeme_kat_id:
                stmt_odeme = select(Odeme.Tutar).where(
                    and_(
                        Odeme.Sube_ID == sube_id,
                        Odeme.Kategori_ID == odeme_kat_id,
                        Odeme.Tarih == cek.Odeme_Tarih
                    )
                )
                odeme_tutari = db.execute(stmt_odeme).scalar() or Decimal('0')

            # Gelir Tutar Check (User requested new column)
            # Sum of all income for this category within the voucher's date range
            stmt_gelir_range = select(func.sum(Gelir.Tutar)).where(
                and_(
                    Gelir.Sube_ID == sube_id,
                    Gelir.Kategori_ID == kat.Kategori_ID,
                    Gelir.Tarih >= cek.Ilk_Tarih,
                    Gelir.Tarih <= cek.Son_Tarih
                )
            )
            gelir_tutar = db.execute(stmt_gelir_range).scalar() or Decimal('0')

            cek_rows.append({
                'id': cek.ID,
                'label': cek.Imaj_Adi if cek.Imaj_Adi else '-',
                'gelir_tutar': gelir_tutar,
                'ilk_tarih': cek.Ilk_Tarih,
                'son_tarih': cek.Son_Tarih,
                'tutar': cek.Tutar,
                'onceki_donem': onceki_donem_tutar,
                'sonraki_donem': sonraki_donem_tutar,
                'donem_tutar': donem_tutar,
                'fark': Decimal('0'),
                'fatura_durumu': 'KESİLDİ' if fat_match else 'BEKLEMEDE',
                'fatura_tarihi': fat_match.Fatura_Tarihi if fat_match else None,
                'odeme_tarihi': cek.Odeme_Tarih,
                'odeme_tutari': odeme_tutari,
                'is_total_row': False
            })
            grup_donem_tutar_total += donem_tutar
            kontrol_edilen_kayit += 1

        # Platform Summary row (Header)
        platform_summary = {
            'label': kat.Kategori_Adi,
            'ilk_tarih': None,
            'son_tarih': None,
            'tutar': grup_aylik_gelir,
            'onceki_donem': Decimal('0'),
            'sonraki_donem': Decimal('0'),
            'donem_tutar': grup_donem_tutar_total,
            'fark': grup_donem_tutar_total - grup_aylik_gelir,
            'fatura_durumu': '-',
            'fatura_tarihi': None,
            'odeme_tarihi': None,
            'odeme_tutari': Decimal('0'),
            'is_total_row': True
        }

        if cek_rows or grup_aylik_gelir > 0:
            results.append([platform_summary] + cek_rows)
            total_gelir += grup_aylik_gelir
            total_donem_tutar += grup_donem_tutar_total

    total_fark = total_donem_tutar - total_gelir

    return {
        'platforms': results,
        'stats': {
            'total_gelir': total_gelir,
            'total_donem_tutar': total_donem_tutar,
            'total_fark': total_fark,
            'kontrol_edilen_kayit': kontrol_edilen_kayit
        }
    }


def get_vps_dashboard_data(db, sube_id, donem):
    """
    Calculates VPS Dashboard data based on legacy logic.
    """
    from datetime import date
    from decimal import Decimal
    from sqlalchemy import and_, or_
    import calendar
    from app.models import Calisan, Puantaj, PuantajSecimi, GelirEkstra

    # Date range
    year = 2000 + (donem // 100)
    month = donem % 100
    _, last_day = calendar.monthrange(year, month)
    
    dates = [date(year, month, d) for d in range(1, last_day + 1)]
    
    # 1. Fetch relevant records
    first_day_dt = date(year, month, 1)
    last_day_dt = date(year, month, last_day)
    
    calisanlar = db.query(Calisan).filter(
        Calisan.Sube_ID == sube_id,
        Calisan.Sigorta_Giris <= last_day_dt,
        or_(Calisan.Sigorta_Cikis == None, Calisan.Sigorta_Cikis >= first_day_dt)
    ).all()
    
    puantaj_records = db.query(Puantaj).filter(
        Puantaj.Sube_ID == sube_id,
        Puantaj.Tarih.between(first_day_dt, last_day_dt)
    ).all()
    
    secimler = db.query(PuantajSecimi).filter(PuantajSecimi.Aktif_Pasif == True).all()
    secim_map = {s.Secim_ID: s for s in secimler}
    
    extras = db.query(GelirEkstra).filter(
        GelirEkstra.Sube_ID == sube_id,
        GelirEkstra.Tarih.between(first_day_dt, last_day_dt)
    ).all()
    extra_map = {e.Tarih: e.Tabak_Sayisi for e in extras}
    
    # 2. Daily Processing
    calisan_counts = []
    aktif_counts = []
    izinli_counts = []
    puantaj_gunu_values = []
    tabak_counts = []
    vps_values = []
    
    score_data_map = {s.Secim_ID: [0] * last_day for s in secimler}
    
    for i, d in enumerate(dates):
        # Çalışan Sayısı
        day_calisan_count = sum(1 for c in calisanlar if c.Sigorta_Giris <= d and (c.Sigorta_Cikis == None or c.Sigorta_Cikis >= d))
        calisan_counts.append(day_calisan_count)
        
        # Daily Puantaj Processing
        day_puantaj = [p for p in puantaj_records if p.Tarih == d]
        
        day_aktif = 0
        day_izinli = 0
        day_puantaj_gunu = Decimal('0.0')
        
        for p in day_puantaj:
            s = secim_map.get(p.Secim_ID)
            if s:
                if 'Çalışma' in s.Secim:
                    day_aktif += 1
                if 'İzin' in s.Secim or 'Rapor' in s.Secim:
                    day_izinli += 1
                
                day_puantaj_gunu += Decimal(str(s.Degeri))
                
                if s.Secim_ID in score_data_map:
                    score_data_map[s.Secim_ID][i] += 1
        
        aktif_counts.append(day_aktif)
        izinli_counts.append(day_izinli)
        puantaj_gunu_values.append(float(day_puantaj_gunu))
        
        tabak = extra_map.get(d, 0)
        tabak_counts.append(tabak)
        
        vps = round(tabak / day_calisan_count, 2) if day_calisan_count > 0 else 0
        vps_values.append(vps)
        
    # 3. Monthly Aggregates & Stats
    total_calisan = sum(calisan_counts)
    total_tabak = sum(tabak_counts)
    
    stats = {
        'calisan_ort': round(total_calisan / last_day, 1) if last_day > 0 else 0.0,
        'aktif_ort': round(sum(aktif_counts) / last_day, 1) if last_day > 0 else 0.0,
        'izinli_ort': round(sum(izinli_counts) / last_day, 1) if last_day > 0 else 0.0,
        'ise_giren': sum(1 for c in calisanlar if c.Sigorta_Giris >= first_day_dt and c.Sigorta_Giris <= last_day_dt),
        'isten_cikan': sum(1 for c in calisanlar if c.Sigorta_Cikis and c.Sigorta_Cikis >= first_day_dt and c.Sigorta_Cikis <= last_day_dt),
        'total_tabak': total_tabak,
        'total_puantaj_gunu': round(float(sum(puantaj_gunu_values)), 1),
        'total_vps': round(total_tabak / total_calisan, 2) if total_calisan > 0 else 0.0
    }
    
    # 4. Final Data Structure
    main_rows = [
        {'label': 'Çalışan Ortalaması', 'data_points': calisan_counts, 'total': stats['calisan_ort'], 'color': 'from-blue-500 to-blue-600', 'icon': 'users', 'avg': stats['calisan_ort']},
        {'label': 'Aktif Çalışan Ortalaması', 'data_points': aktif_counts, 'total': stats['aktif_ort'], 'color': 'from-green-500 to-green-600', 'icon': 'activity', 'avg': stats['aktif_ort']},
        {'label': 'İzinli Çalışan Ortalaması', 'data_points': izinli_counts, 'total': stats['izinli_ort'], 'color': 'from-yellow-500 to-yellow-600', 'icon': 'clock', 'avg': stats['izinli_ort']},
        {'label': 'Puantaj Günü', 'data_points': puantaj_gunu_values, 'total': stats['total_puantaj_gunu'], 'color': 'from-purple-500 to-purple-600', 'icon': 'calendar'},
        {'label': 'Tabak Sayısı', 'data_points': tabak_counts, 'total': stats['total_tabak'], 'color': 'from-orange-500 to-orange-600', 'icon': 'target'},
        {'label': 'VPS', 'data_points': vps_values, 'total': stats['total_vps'], 'color': 'from-indigo-500 to-indigo-600', 'icon': 'bar-chart-3'}
    ]
    
    puantaj_ozeti = []
    for s in secimler:
        puantaj_ozeti.append({
            'label': s.Secim,
            'multiplier': f"{s.Degeri:g}x",
            'counts': score_data_map[s.Secim_ID],
            'total': sum(score_data_map[s.Secim_ID]),
            'color': s.Renk_Kodu
        })
        
    return {
        'dates': [d.day for d in dates],
        'stats': stats,
        'main_rows': main_rows,
        'puantaj_ozeti': puantaj_ozeti,
        'days_in_month': last_day,
        'year': year,
        'month': month
    }


# ============================================================================
# MUTABAKAT (RECONCILIATION) QUERIES
# ============================================================================

def get_mutabakatlar(
    db: Session,
    skip: int = 0,
    limit: int = 100,
    cari_id: Optional[int] = None,
    sube_id: Optional[int] = None,
    search: Optional[str] = None
) -> List[Mutabakat]:
    """Get reconciliation records with optional filtering."""
    stmt = select(Mutabakat).join(Cari, Mutabakat.Cari_ID == Cari.Cari_ID)
    
    if cari_id is not None:
        stmt = stmt.where(Mutabakat.Cari_ID == cari_id)
        
    if sube_id is not None:
        stmt = stmt.where(Mutabakat.Sube_ID == sube_id)
        
    if search:
        search_filter = f"%{search}%"
        stmt = stmt.where(Cari.Alici_Unvani.ilike(search_filter))
        
    stmt = stmt.order_by(Mutabakat.Mutabakat_Tarihi.desc())
    stmt = stmt.offset(skip).limit(limit)
    return db.scalars(stmt).all()


def create_mutabakat(
    db: Session,
    cari_id: int,
    sube_id: int,
    tarih: date,
    tutar: float
) -> Mutabakat:
    """Create a new reconciliation record."""
    new_m = Mutabakat(
        Cari_ID=cari_id,
        Sube_ID=sube_id,
        Mutabakat_Tarihi=tarih,
        Tutar=tutar
    )
    db.add(new_m)
    db.commit()
    db.refresh(new_m)
    return new_m


def update_mutabakat(
    db: Session,
    mutabakat_id: int,
    tarih: Optional[date] = None,
    tutar: Optional[float] = None
) -> Optional[Mutabakat]:
    """Update an existing reconciliation record."""
    m = db.get(Mutabakat, mutabakat_id)
    if not m:
        return None
        
    if tarih is not None:
        if isinstance(tarih, str):
            tarih = date.fromisoformat(tarih)
        m.Mutabakat_Tarihi = tarih
    if tutar is not None:
        m.Tutar = tutar
        
    db.commit()
    db.refresh(m)
    return m


def delete_mutabakat(db: Session, mutabakat_id: int) -> bool:
    """Delete a reconciliation record."""
    m = db.get(Mutabakat, mutabakat_id)
    if not m:
        return False
    db.delete(m)
    db.commit()
    return True
