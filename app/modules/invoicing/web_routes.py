from flask import Blueprint, render_template, session, redirect, url_for, request
from sqlalchemy import func
from app.common.decorators import login_required, permission_required

from app.modules.auth import queries as auth_queries
from app.modules.reference import queries as ref_queries
from app.modules.invoicing import queries as invoicing_queries
from app.common.database import get_db_session
from app.models import Kullanici, Cari, Gelir, EFatura, DigerHarcama

web_invoicing_bp = Blueprint("web_invoicing", __name__)

@web_invoicing_bp.route("/fatura-yukleme", methods=["GET"])
@login_required
@permission_required("Fatura Yükleme Ekranı Görüntüleme")
def fatura_yukleme():
    """
    Fatura Yükleme (Invoice Upload) page.
    """
    db_session = get_db_session()
    user = auth_queries.get_kullanici_by_id(db_session, session['user_id'])
    
    if not user:
        db_session.close()
        return redirect(url_for('web_auth.login'))
        
    all_suber = ref_queries.get_suber(db_session, limit=1000)
    
    # Simple admin check
    is_admin = (user.Kullanici_Adi and user.Kullanici_Adi.lower() == 'admin')
    if not is_admin:
        roles = auth_queries.get_user_roles(db_session, user.Kullanici_ID)
        is_admin = 'admin' in [r.lower() for r in roles]

    auth_suber = all_suber if is_admin else [
        s for s in all_suber if s.Sube_ID in auth_queries.get_user_branches(db_session, user.Kullanici_ID)
    ]
    
    db_session.close()
    
    return render_template(
        "fatura_yukleme.html",
        user=user,
        subeler=auth_suber
    )

def turkish_sort_key(s):
    """
    Custom sort key for Turkish alphabetical order (A-Z, case-insensitive).
    """
    if not s:
        return []
    
    s = str(s).strip()
    # Manual Turkish replacement to handle i/İ and ı/I correctly before lowercasing
    map_chars = {'İ': 'i', 'I': 'ı', 'Ç': 'ç', 'Ğ': 'ğ', 'Ö': 'ö', 'Ş': 'ş', 'Ü': 'ü'}
    s_lower = ""
    for char in s:
        if char in map_chars:
            s_lower += map_chars[char]
        else:
            s_lower += char.lower()
    
    alphabet = "abcçdefgğhıijklmnoöprsştuüvyz"
    order = {char: i for i, char in enumerate(alphabet)}
    
    key = []
    for char in s_lower:
        if char in order:
            key.append(order[char])
        else:
            # Punctuation/Spaces come before alphabet letters (0-28)
            key.append(ord(char) - 1000)
    return key

@web_invoicing_bp.route("/fatura-kategori-atama", methods=["GET"])
@login_required
@permission_required("Fatura Kategori Atama Ekranı Görüntüleme")
def fatura_kategori_atama():
    """
    Fatura Kategori Atama (Invoice Category Assignment) page.
    """
    db_session = get_db_session()
    user = auth_queries.get_kullanici_by_id(db_session, session['user_id'])
    
    if not user:
        db_session.close()
        return redirect(url_for('web_auth.login'))
        
    all_suber = ref_queries.get_suber(db_session, limit=1000)
    
    # Simple admin check
    is_admin = (user.Kullanici_Adi and user.Kullanici_Adi.lower() == 'admin')
    if not is_admin:
        roles = auth_queries.get_user_roles(db_session, user.Kullanici_ID)
        is_admin = 'admin' in [r.lower() for r in roles]

    auth_suber = all_suber if is_admin else [
        s for s in all_suber if s.Sube_ID in auth_queries.get_user_branches(db_session, user.Kullanici_ID)
    ]
    
    # Check Gizli permission
    has_gizli_permission = auth_queries.has_permission(db_session, user.Kullanici_ID, "Gizli Kategori Veri Erişimi")
    can_view_gizli = is_admin or has_gizli_permission
    
    # Fetch categories for filtering and assignment
    raw_kategoriler = ref_queries.get_kategoriler(db_session, tip='Gider', limit=1000, can_view_gizli=can_view_gizli)
    kategoriler = sorted(raw_kategoriler, key=lambda k: turkish_sort_key(k.Kategori_Adi))
    
    import json
    kategoriler_json = json.dumps([
        {"id": k.Kategori_ID, "name": k.Kategori_Adi}
        for k in kategoriler
    ], ensure_ascii=False)
    
    db_session.close()
    
    return render_template(
        "fatura_kategori_atama.html",
        user=user,
        subeler=auth_suber,
        kategoriler=kategoriler,
        kategoriler_json=kategoriler_json,
        has_gizli_permission=can_view_gizli
    )

@web_invoicing_bp.route("/b2b-ekstre-yukleme", methods=["GET"])
@login_required
@permission_required("B2B Ekstre Yükleme Ekranı Görüntüleme")
def b2b_ekstre_yukleme():
    """
    B2B Ekstre Yükleme (B2B Statement Upload) page.
    """
    db_session = get_db_session()
    user = auth_queries.get_kullanici_by_id(db_session, session['user_id'])
    
    if not user:
        db_session.close()
        return redirect(url_for('web_auth.login'))
        
    all_suber = ref_queries.get_suber(db_session, limit=1000)
    
    is_admin = (user.Kullanici_Adi and user.Kullanici_Adi.lower() == 'admin')
    if not is_admin:
        roles = auth_queries.get_user_roles(db_session, user.Kullanici_ID)
        is_admin = 'admin' in [r.lower() for r in roles]

    auth_suber = all_suber if is_admin else [
        s for s in all_suber if s.Sube_ID in auth_queries.get_user_branches(db_session, user.Kullanici_ID)
    ]
    
    db_session.close()
    
    return render_template(
        "b2b_ekstre_yukleme.html",
        user=user,
        subeler=auth_suber
    )


@web_invoicing_bp.route("/robotpos-gelir-yukleme", methods=["GET"])
@login_required
@permission_required("Robotpos Gelir Yükleme Ekranı Görüntüleme")
def robotpos_gelir_yukleme():
    """
    Robotpos Gelir Yükleme page.
    Permission ID: 65
    """
    db_session = get_db_session()
    user = auth_queries.get_kullanici_by_id(db_session, session['user_id'])
    
    if not user:
        db_session.close()
        return redirect(url_for('web_auth.login'))
        
    all_suber = ref_queries.get_suber(db_session, limit=1000)
    
    is_admin = (user.Kullanici_Adi and user.Kullanici_Adi.lower() == 'admin')
    if not is_admin:
        roles = auth_queries.get_user_roles(db_session, user.Kullanici_ID)
        is_admin = 'admin' in [r.lower() for r in roles]

    auth_suber = all_suber if is_admin else [
        s for s in all_suber if s.Sube_ID in auth_queries.get_user_branches(db_session, user.Kullanici_ID)
    ]
    
    db_session.close()
    
    return render_template(
        "robotpos_gelir_yukleme.html",
        user=user,
        subeler=auth_suber
    )

@web_invoicing_bp.route("/odeme-yukleme", methods=["GET"])
@login_required
@permission_required("Ödeme Yükleme Ekranı Görüntüleme")
def odeme_yukleme():
    """
    Ödeme Yükleme (Payment Upload) page.
    """
    db_session = get_db_session()
    user = auth_queries.get_kullanici_by_id(db_session, session['user_id'])
    
    if not user:
        db_session.close()
        return redirect(url_for('web_auth.login'))
        
    all_suber = ref_queries.get_suber(db_session, limit=1000)
    
    is_admin = (user.Kullanici_Adi and user.Kullanici_Adi.lower() == 'admin')
    if not is_admin:
        roles = auth_queries.get_user_roles(db_session, user.Kullanici_ID)
        is_admin = 'admin' in [r.lower() for r in roles]

    auth_suber = all_suber if is_admin else [
        s for s in all_suber if s.Sube_ID in auth_queries.get_user_branches(db_session, user.Kullanici_ID)
    ]
    
    db_session.close()
    
    return render_template(
        "odeme_yukleme.html",
        user=user,
        subeler=auth_suber
    )

@web_invoicing_bp.route("/odeme-kategori-atama", methods=["GET"])
@login_required
@permission_required("Ödeme Kategori Atama Ekranı Görüntüleme")
def odeme_kategori_atama():
    """
    Ödeme Kategori Atama (Payment Category Assignment) page.
    """
    db_session = get_db_session()
    user = auth_queries.get_kullanici_by_id(db_session, session['user_id'])
    
    if not user:
        db_session.close()
        return redirect(url_for('web_auth.login'))
        
    all_suber = ref_queries.get_suber(db_session, limit=1000)
    
    is_admin = (user.Kullanici_Adi and user.Kullanici_Adi.lower() == 'admin')
    if not is_admin:
        roles = auth_queries.get_user_roles(db_session, user.Kullanici_ID)
        is_admin = 'admin' in [r.lower() for r in roles]

    auth_suber = all_suber if is_admin else [
        s for s in all_suber if s.Sube_ID in auth_queries.get_user_branches(db_session, user.Kullanici_ID)
    ]
    
    # Kategori list - 'Ödeme Sistemleri' and 'Bilgi' Parent Categories
    all_categories = ref_queries.get_kategoriler(db_session, limit=1000)
    payment_categories = []
    
    # We need to find the UstKategori IDs for 'Ödeme Sistemleri' and 'Bilgi'
    ust_kat_odeme = None
    ust_kat_bilgi = None
    
    ust_kategoriler = ref_queries.get_ust_kategoriler(db_session, limit=1000)
    for uk in ust_kategoriler:
        if uk.UstKategori_Adi == 'Ödeme Sistemleri':
            ust_kat_odeme = uk.UstKategori_ID
        elif uk.UstKategori_Adi == 'Bilgi':
            ust_kat_bilgi = uk.UstKategori_ID
            
    for kat in all_categories:
        if kat.Aktif_Pasif and kat.Ust_Kategori_ID in [ust_kat_odeme, ust_kat_bilgi]:
            payment_categories.append({
                "Kategori_ID": kat.Kategori_ID,
                "Kategori_Adi": kat.Kategori_Adi
            })
            
    # Sort categories alphabetically
    payment_categories.sort(key=lambda x: x["Kategori_Adi"])
    
    # Fetch user permissions for server-side check in template
    user_permissions = auth_queries.get_user_permissions(db_session, user.Kullanici_ID)
    
    db_session.close()
    
    return render_template(
        "odeme_kategori_atama.html",
        user=user,
        subeler=auth_suber,
        kategoriler=payment_categories,
        user_permissions=user_permissions
    )

@web_invoicing_bp.route("/diger-harcamalar", methods=["GET"])
@login_required
@permission_required("Diğer Harcamalar Ekranı Görüntüleme")
def diger_harcamalar():
    """
    Diğer Harcamalar (Other Expenses) page.
    """
    db_session = get_db_session()
    user = auth_queries.get_kullanici_by_id(db_session, session['user_id'])
    
    if not user:
        db_session.close()
        return redirect(url_for('web_auth.login'))
        
    all_suber = ref_queries.get_suber(db_session, limit=1000)
    
    is_admin = (user.Kullanici_Adi and user.Kullanici_Adi.lower() == 'admin')
    if not is_admin:
        roles = auth_queries.get_user_roles(db_session, user.Kullanici_ID)
        is_admin = 'admin' in [r.lower() for r in roles]

    auth_suber = all_suber if is_admin else [
        s for s in all_suber if s.Sube_ID in auth_queries.get_user_branches(db_session, user.Kullanici_ID)
    ]
    
    # Check for "Gizli Kategori Veri Erişimi" permission
    can_view_gizli = is_admin or auth_queries.has_permission(db_session, user.Kullanici_ID, "Gizli Kategori Veri Erişimi")
    
    # Fetch categories for the add/edit modal
    kategoriler_raw = ref_queries.get_kategoriler(db_session, limit=1000, can_view_gizli=can_view_gizli)
    
    # Serialize kategoriler to plain dicts so tojson filter works in template
    kategoriler = [
        {'Kategori_ID': k.Kategori_ID, 'Kategori_Adi': k.Kategori_Adi}
        for k in kategoriler_raw
    ]
    
    # Get filter params from query string
    sube_id = request.args.get('sube_id', None, type=int)
    harcama_tipi = request.args.get('harcama_tipi', None, type=str)
    
    # Default to first branch if not specified
    if sube_id is None and auth_suber:
        sube_id = auth_suber[0].Sube_ID

    # Calculate current period (YYMM) as default — current date: 2026-02-28 → 2602
    from datetime import date as _date
    _today = _date.today()
    current_donem = int(str(_today.year)[-2:] + str(_today.month).zfill(2))

    # If donem not provided in query string, default to current period
    donem_str = request.args.get('donem', None)
    if donem_str is not None:
        try:
            donem = int(donem_str)
        except ValueError:
            donem = current_donem
    else:
        donem = current_donem

    # Fetch distinct donem list from DB (all branches), sorted descending (newest first)
    try:
        from app.models import DigerHarcama as _DH
        from sqlalchemy import select as _select, distinct as _distinct
        _stmt = _select(_distinct(_DH.Donem)).order_by(_DH.Donem.desc())
        donem_listesi = [row[0] for row in db_session.execute(_stmt).fetchall() if row[0] is not None]
    except Exception:
        donem_listesi = []

    # Ensure current_donem is in the list even if no records exist for it
    if current_donem not in donem_listesi:
        donem_listesi = [current_donem] + donem_listesi

    # Ensure selected donem is in the list
    if donem not in donem_listesi:
        donem_listesi = sorted([donem] + donem_listesi, reverse=True)
    
    # Fetch harcamalar server-side
    import base64 as b64
    raw_harcamalar = invoicing_queries.get_diger_harcamalar(
        db_session,
        sube_id=sube_id,
        donem=donem,
        harcama_tipi=harcama_tipi,
        limit=1000,
        can_view_gizli=can_view_gizli
    )
    
    # Serialize for template
    harcamalar_list = []
    for h in raw_harcamalar:
        item = {
            'Harcama_ID': h.Harcama_ID,
            'Alici_Adi': h.Alici_Adi or '',
            'Belge_Numarasi': h.Belge_Numarasi or '',
            'Belge_Tarihi': h.Belge_Tarihi.strftime('%d.%m.%Y') if h.Belge_Tarihi else '',
            'Belge_Tarihi_Input': h.Belge_Tarihi.strftime('%Y-%m-%d') if h.Belge_Tarihi else '',
            'Donem': h.Donem,
            'Tutar': float(h.Tutar) if h.Tutar else 0.0,
            'Kategori_ID': h.Kategori_ID,
            'Harcama_Tipi': h.Harcama_Tipi or '',
            'Gunluk_Harcama': bool(h.Gunluk_Harcama),
            'Sube_ID': h.Sube_ID,
            'Aciklama': h.Açıklama or '',
            'Imaj_Adi': h.Imaj_Adi or '',
            'has_imaj': bool(h.Imaj),
            'Imaj_Base64': b64.b64encode(h.Imaj).decode('utf-8') if h.Imaj else '',
        }
        harcamalar_list.append(item)
    
    # Build kategori map (id -> name) for server-side rendering
    kategori_map = {k['Kategori_ID']: k['Kategori_Adi'] for k in kategoriler}
    
    db_session.close()
    
    return render_template(
        "diger_harcamalar.html",
        user=user,
        subeler=auth_suber,
        kategoriler=kategoriler,
        harcamalar=harcamalar_list,
        secili_sube_id=sube_id,
        kategori_map=kategori_map,
        donem_listesi=donem_listesi,
        secili_donem=donem,
        current_donem=current_donem,
    )
@web_invoicing_bp.route("/pos-hareketleri-yukleme", methods=["GET"])
@login_required
@permission_required("POS Hareketleri Yükleme Ekranı Görüntüleme")
def pos_hareketleri_yukleme():
    """
    POS Hareketleri Yükleme (POS Transactions Upload) page.
    """
    db_session = get_db_session()
    user = auth_queries.get_kullanici_by_id(db_session, session['user_id'])
    
    if not user:
        db_session.close()
        return redirect(url_for('web_auth.login'))
        
    all_suber = ref_queries.get_suber(db_session, limit=1000)
    
    is_admin = (user.Kullanici_Adi and user.Kullanici_Adi.lower() == 'admin')
    if not is_admin:
        roles = auth_queries.get_user_roles(db_session, user.Kullanici_ID)
        is_admin = 'admin' in [r.lower() for r in roles]

    auth_suber = all_suber if is_admin else [
        s for s in all_suber if s.Sube_ID in auth_queries.get_user_branches(db_session, user.Kullanici_ID)
    ]
    
    db_session.close()
    
    return render_template(
        "pos_hareketleri_yukleme.html",
        user=user,
        subeler=auth_suber
    )
@web_invoicing_bp.route("/tabak-sayisi-yukleme", methods=["GET"])
@login_required
@permission_required("Tabak Sayısı Yükleme Ekranı Görüntüleme")
def tabak_sayisi_yukleme():
    """
    Tabak Sayısı Yükleme (Plate Count Upload) page.
    """
    db_session = get_db_session()
    user = auth_queries.get_kullanici_by_id(db_session, session['user_id'])
    
    if not user:
        db_session.close()
        return redirect(url_for('web_auth.login'))
        
    all_suber = ref_queries.get_suber(db_session, limit=1000)
    
    is_admin = (user.Kullanici_Adi and user.Kullanici_Adi.lower() == 'admin')
    if not is_admin:
        roles = auth_queries.get_user_roles(db_session, user.Kullanici_ID)
        is_admin = 'admin' in [r.lower() for r in roles]

    auth_suber = all_suber if is_admin else [
        s for s in all_suber if s.Sube_ID in auth_queries.get_user_branches(db_session, user.Kullanici_ID)
    ]
    
    db_session.close()
    
    return render_template(
        "tabak_sayisi_yukleme.html",
        user=user,
        subeler=auth_suber
    )
@web_invoicing_bp.route("/yemek-ceki", methods=["GET"])
@login_required
@permission_required("Yemek Çeki Ekranı Görüntüleme")
def yemek_ceki():
    """
    Yemek Çeki (Meal Tickets) page.
    """
    db_session = get_db_session()
    user = auth_queries.get_kullanici_by_id(db_session, session['user_id'])
    
    if not user:
        db_session.close()
        return redirect(url_for('web_auth.login'))
        
    all_suber = ref_queries.get_suber(db_session, limit=1000)
    
    is_admin = (user.Kullanici_Adi and user.Kullanici_Adi.lower() == 'admin')
    if not is_admin:
        roles = auth_queries.get_user_roles(db_session, user.Kullanici_ID)
        is_admin = 'admin' in [r.lower() for r in roles]

    auth_suber = all_suber if is_admin else [
        s for s in all_suber if s.Sube_ID in auth_queries.get_user_branches(db_session, user.Kullanici_ID)
    ]
    
    # Get filter params
    sube_id = request.args.get('sube_id', None, type=int)
    if sube_id is None and auth_suber:
        sube_id = auth_suber[0].Sube_ID

    # Dönem hesaplama (YYMM)
    from datetime import date as _date
    _today = _date.today()
    current_donem = int(str(_today.year)[-2:] + str(_today.month).zfill(2))
    
    donem = request.args.get('donem', current_donem, type=int)

    # Fetch records
    raw_cekiler = invoicing_queries.get_yemek_cekileri(
        db_session,
        sube_id=sube_id,
        donem=donem,
        limit=1000
    )

    # Kategori haritası (Ödeme tipindekiler)
    kategoriler_raw = ref_queries.get_kategoriler(db_session, limit=1000)
    kategori_map = {k.Kategori_ID: k.Kategori_Adi for k in kategoriler_raw}
    
    # Serialize for template
    import base64 as b64
    cekiler_list = []
    for c in raw_cekiler:
        item = {
            'ID': c.ID,
            'Kategori_ID': c.Kategori_ID,
            'Kategori_Adi': kategori_map.get(c.Kategori_ID, 'Bilinmiyor'),
            'Tarih': c.Tarih.strftime('%Y-%m-%d') if c.Tarih else '',
            'Tutar': float(c.Tutar) if c.Tutar else 0.0,
            'Odeme_Tarih': c.Odeme_Tarih.strftime('%Y-%m-%d') if c.Odeme_Tarih else '',
            'Ilk_Tarih': c.Ilk_Tarih.strftime('%Y-%m-%d') if c.Ilk_Tarih else '',
            'Son_Tarih': c.Son_Tarih.strftime('%Y-%m-%d') if c.Son_Tarih else '',
            'Sube_ID': c.Sube_ID,
            'Imaj_Adi': c.Imaj_Adi or 'gorsel.jpeg',
            'has_imaj': bool(c.Imaj)
        }
        cekiler_list.append(item)

    # Donem listesi (son 12 ay)
    donem_listesi = []
    temp_date = _today
    for _ in range(12):
        d_val = int(str(temp_date.year)[-2:] + str(temp_date.month).zfill(2))
        donem_listesi.append(d_val)
        # One month back
        m = temp_date.month - 1
        y = temp_date.year
        if m == 0:
            m = 12
            y -= 1
        temp_date = _date(y, m, 1)

    # Kategori filtreleme: Üst kategorisi 'Yemek Çeki' olanları al
    from app.models import UstKategori
    ust_kat = db_session.query(UstKategori).filter(UstKategori.UstKategori_Adi == 'Yemek Çeki').first()
    ust_kat_id = ust_kat.UstKategori_ID if ust_kat else None

    db_session.close()
    
    return render_template(
        "yemek_ceki.html",
        user=user,
        subeler=auth_suber,
        cekiler=cekiler_list,
        secili_sube_id=sube_id,
        secili_donem=donem,
        donem_listesi=donem_listesi,
        all_kategoriler=[{'Kategori_ID': k.Kategori_ID, 'Kategori_Adi': k.Kategori_Adi} for k in kategoriler_raw if k.Ust_Kategori_ID == ust_kat_id]
    )

# ==========================================
# NAKIT GİRİŞİ WEB ROTASI
# ==========================================

@web_invoicing_bp.route("/nakit-girisi")
@login_required
@permission_required("Nakit Girişi Ekranı Görüntüleme")
def nakit_girisi():
    db_session = get_db_session()
    user = auth_queries.get_kullanici_by_id(db_session, session['user_id'])
    
    if not user:
        db_session.close()
        return redirect(url_for('web_auth.login'))
        
    all_suber = ref_queries.get_suber(db_session, limit=1000)
    
    is_admin = (user.Kullanici_Adi and user.Kullanici_Adi.lower() == 'admin')
    if not is_admin:
        roles = auth_queries.get_user_roles(db_session, user.Kullanici_ID)
        is_admin = 'admin' in [r.lower() for r in roles]

    auth_suber = all_suber if is_admin else [
        s for s in all_suber if s.Sube_ID in auth_queries.get_user_branches(db_session, user.Kullanici_ID)
    ]

    auth_sube_ids = [s.Sube_ID for s in auth_suber]

    sube_id_str = request.args.get("sube_id", "")
    sube_id = int(sube_id_str) if sube_id_str.isdigit() else auth_suber[0].Sube_ID

    if sube_id not in auth_sube_ids:
        sube_id = auth_suber[0].Sube_ID

    from datetime import date as _date
    _today = _date.today()
    current_donem = int(str(_today.year)[-2:] + str(_today.month).zfill(2))
    
    donem_str = request.args.get("donem", "")
    donem = int(donem_str) if donem_str.isdigit() else current_donem

    raw_nakitler = invoicing_queries.get_nakitler(
        db_session,
        sube_id=sube_id,
        donem=donem,
        limit=1000
    )
    
    import base64 as b64
    nakitler_list = []
    for n in raw_nakitler:
        item = {
            'Nakit_ID': n.Nakit_ID,
            'Tarih': n.Tarih.strftime('%Y-%m-%d') if n.Tarih else '',
            'Tarih_Formatli': n.Tarih.strftime('%d.%m.%Y') if n.Tarih else '',
            'Tutar': float(n.Tutar) if n.Tutar else 0.0,
            'Tip': n.Tip,
            'Donem': n.Donem,
            'Sube_ID': n.Sube_ID,
            'Kayit_Tarih': n.Kayit_Tarih.strftime('%d.%m.%Y') if n.Kayit_Tarih else ''
        }
        nakitler_list.append(item)

    donem_listesi = []
    temp_date = _today
    for _ in range(12):
        d_val = int(str(temp_date.year)[-2:] + str(temp_date.month).zfill(2))
        donem_listesi.append(d_val)
        m = temp_date.month - 1
        y = temp_date.year
        if m == 0:
            m = 12
            y -= 1
        temp_date = _date(y, m, 1)

    # İlgili nakit giriş tipleri örnekleri: 
    # Bu liste standartlaştırma ya da yeni kayıtlarda select listesini oluşturmak amaçlı tutulabilir:
    tipler = ["Bankaya Yatan", "Bankadan Çekilen", "Şube Kasasına Yatan", "Diğer Nakit"]

    from flask import make_response
    
    db_session.close()
    
    response = make_response(render_template(
        "nakit_girisi.html",
        user=user,
        subeler=auth_suber,
        nakitler=nakitler_list,
        secili_sube_id=sube_id,
        secili_donem=donem,
        donem_listesi=donem_listesi,
        tipler=tipler
    ))
    
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Expires"] = "0"
    
    return response

# ==========================================
# GELİR GİRİŞİ WEB ROTASI (Matrix / Pivot)
# ==========================================

import calendar

@web_invoicing_bp.route("/gelir-girisi")
@login_required
@permission_required("Gelir Girişi Ekranı Görüntüleme")
def gelir_girisi():
    db_session = get_db_session()
    user = auth_queries.get_kullanici_by_id(db_session, session['user_id'])
    
    if not user:
        db_session.close()
        return redirect(url_for('web_auth.login'))
        
    all_suber = ref_queries.get_suber(db_session, limit=1000)
    
    is_admin = (user.Kullanici_Adi and user.Kullanici_Adi.lower() == 'admin')
    if not is_admin:
        roles = auth_queries.get_user_roles(db_session, user.Kullanici_ID)
        is_admin = 'admin' in [r.lower() for r in roles]

    auth_suber = all_suber if is_admin else [
        s for s in all_suber if s.Sube_ID in auth_queries.get_user_branches(db_session, user.Kullanici_ID)
    ]
    
    if not auth_suber:
        db_session.close()
        flash("Yetkiniz olan hiçbir şube bulunamadı.", "warning")
        return redirect(url_for("main.dashboard"))

    auth_sube_ids = [s.Sube_ID for s in auth_suber]

    sube_id_str = request.args.get("sube_id", "")
    sube_id = int(sube_id_str) if sube_id_str.isdigit() else auth_suber[0].Sube_ID

    if sube_id not in auth_sube_ids:
        sube_id = auth_suber[0].Sube_ID

    from datetime import date as _date
    _today = _date.today()
    current_donem = int(str(_today.year)[-2:] + str(_today.month).zfill(2))
    
    donem_str = request.args.get("donem", "")
    donem = int(donem_str) if donem_str.isdigit() else current_donem

    # Dönem (YYMM) str parse -> Year (20YY), Month (MM)
    d_str = str(donem)
    if len(d_str) == 4:
        d_year = 2000 + int(d_str[:2])
        d_month = int(d_str[2:])
    else:
        d_year = _today.year
        d_month = _today.month

    import calendar
    # Ayın kaç gün çektiğini buluyoruz (Sütunlar) 28,29,30,31
    _, days_in_month = calendar.monthrange(d_year, d_month)
    gunler = list(range(1, days_in_month + 1))

    # Yetkiler ve Kısıtlamalar
    can_view_gizli = auth_queries.has_permission(db_session, user.Kullanici_ID, "Gizli Kategori Görme")
    can_access_history = auth_queries.has_permission(db_session, user.Kullanici_ID, "Gelir Geçmiş Veri Erişimi") 
    
    # Düzenleme Yetkisi Hesaplaması: (İlk 5 gün kuralı ve Admin Serbestisi)
    is_editing_disabled = False
    if not is_admin:
        if donem != current_donem:
            # Geçmiş Bir Dönem Görüntüleniyor
            prev_month = _today.month - 1
            prev_year = _today.year
            if prev_month == 0:
                prev_month = 12
                prev_year -= 1
            prev_donem = int(str(prev_year)[-2:] + str(prev_month).zfill(2))
            
            # Sadece "bir önceki aya" ayın ilk 5 günü müdahale edilebilir
            if donem == prev_donem and _today.day <= 5:
                is_editing_disabled = False
            else:
                is_editing_disabled = True
    
    # 1. Kategori (Satır başlıkları)
    kategoriler = invoicing_queries.get_gelir_kategorileri(db_session, can_view_gizli=can_view_gizli)
    
    # 2. Üst Kategorileri Çekip Hiyerarşiyi (Grouping) UI'da Oluşturmak İçin
    from app.models import UstKategori
    ust_kat_list = db_session.query(UstKategori).filter(UstKategori.Aktif_Pasif == True).all()
    ust_kat_dict = { u.UstKategori_ID: u.UstKategori_Adi for u in ust_kat_list }
    
    # 3. Matris datası (Tutar), { (Kat_ID, Gun) : Tutar }
    matrix_data = invoicing_queries.get_gelirler_by_donem(db_session, sube_id, d_year, d_month)
    
    # 4. GelirEkstra Datası (RobotPos, TabakSayisi)
    ekstra_data = invoicing_queries.get_gelir_ekstra_by_donem(db_session, sube_id, d_year, d_month)
    
    # 5. Günlük Harcamalar (FİŞ/FATURA read-only alanları için eFatura & Diger)
    harcama_data = invoicing_queries.get_gunluk_harcamalar_by_donem(db_session, sube_id, d_year, d_month)

    # Donem select box
    donem_listesi = []
    temp_date = _today
    for _ in range(12):
        d_val = int(str(temp_date.year)[-2:] + str(temp_date.month).zfill(2))
        donem_listesi.append(d_val)
        m = temp_date.month - 1
        y = temp_date.year
        if m == 0:
            m = 12
            y -= 1
        temp_date = _date(y, m, 1)

    from flask import make_response
    db_session.close()
    
    response = make_response(render_template(
        "gelir_girisi.html",
        user=user,
        subeler=auth_suber,
        secili_sube_id=sube_id,
        secili_donem=donem,
        current_donem=current_donem,
        donem_listesi=donem_listesi,
        gunler=gunler,
        kategoriler=kategoriler,
        ust_kategoriler=ust_kat_dict,
        matrix_data=matrix_data,
        ekstra_data=ekstra_data,
        harcama_data=harcama_data,
        d_year=d_year,
        d_month=d_month,
        is_editing_disabled=is_editing_disabled,
        can_access_history=can_access_history
    ))
    
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Pragma"] = "no-cache"
    response.headers["Expires"] = "0"
    
    return response


# ==========================================
# NAKİT YATIRMA KONTROL RAPORU WEB ROTASI
# ==========================================

@web_invoicing_bp.route("/nakit-yatirma-kontrol-raporu")
@login_required
@permission_required("Nakit Yatırma Kontrol Raporu Görüntüleme")
def nakit_yatirma_kontrol_raporu():
    db_session = get_db_session()
    user = auth_queries.get_kullanici_by_id(db_session, session['user_id'])
    
    if not user:
        db_session.close()
        return redirect(url_for('web_auth.login'))
        
    all_suber = ref_queries.get_suber(db_session, limit=1000)
    
    is_admin = (user.Kullanici_Adi and user.Kullanici_Adi.lower() == 'admin')
    if not is_admin:
        roles = auth_queries.get_user_roles(db_session, user.Kullanici_ID)
        is_admin = 'admin' in [r.lower() for r in roles]

    auth_suber = all_suber if is_admin else [
        s for s in all_suber if s.Sube_ID in auth_queries.get_user_branches(db_session, user.Kullanici_ID)
    ]

    auth_sube_ids = [s.Sube_ID for s in auth_suber]

    sube_id_str = request.args.get("sube_id", "")
    sube_id = int(sube_id_str) if sube_id_str.isdigit() else (auth_suber[0].Sube_ID if auth_suber else None)

    if sube_id not in auth_sube_ids and auth_suber:
        sube_id = auth_suber[0].Sube_ID

    from datetime import date as _date
    _today = _date.today()
    current_donem = int(str(_today.year)[-2:] + str(_today.month).zfill(2))
    
    donem_str = request.args.get("donem", "")
    donem = int(donem_str) if donem_str.isdigit() else current_donem

    # Dönem listesi (son 12 ay)
    donem_listesi = []
    temp_date = _today
    for _ in range(12):
        d_val = int(str(temp_date.year)[-2:] + str(temp_date.month).zfill(2))
        donem_listesi.append(d_val)
        m = temp_date.month - 1
        y = temp_date.year
        if m == 0:
            m = 12
            y -= 1
        temp_date = _date(y, m, 1)

    # Calculate date range for current donem (YYMM)
    s_donem = str(donem).zfill(4)
    yy = int(s_donem[:2])
    mm = int(s_donem[2:])
    year = 2000 + yy
    import calendar
    _, last_day = calendar.monthrange(year, mm)
    start_date = _date(year, mm, 1)
    end_date = _date(year, mm, last_day)

    # Fetch Bankaya Yatan from Odeme table (Kategori_ID=60) — matches old backend logic
    from app.models import Odeme, Kategori
    bankaya_yatan = db_session.query(Odeme).filter(
        Odeme.Sube_ID == sube_id,
        Odeme.Donem == donem,
        Odeme.Kategori_ID == 60
    ).all()

    # Fetch Nakit Girişi from Nakit table (all records for branch+donem) — matches old backend logic
    nakit_giris = invoicing_queries.get_nakitler(db_session, sube_id=sube_id, donem=donem, limit=5000)

    # Matching Logic: 1:1 matching with boolean arrays (ported from old TSX code)
    # Each bankaya record can match at most ONE nakit record, and vice versa.
    tolerance = 0.01  # 1 kuruş tolerance for floating point precision

    bankaya_matched = [False] * len(bankaya_yatan)
    nakit_matched = [False] * len(nakit_giris)

    # Single pass: for each bankaya record, find the first unmatched nakit record
    # with same Donem and Tutar (within tolerance)
    for b_idx, b_item in enumerate(bankaya_yatan):
        for n_idx, n_item in enumerate(nakit_giris):
            if nakit_matched[n_idx]:
                continue
            b_donem = b_item.Donem if b_item.Donem else donem
            n_donem = n_item.Donem if n_item.Donem else donem
            if b_donem == n_donem and abs(float(b_item.Tutar) - float(n_item.Tutar)) < tolerance:
                bankaya_matched[b_idx] = True
                nakit_matched[n_idx] = True
                break

    # Build Bankaya Yatan list with matched status (from Odeme)
    bankaya_yatan_list = []
    for idx, o in enumerate(bankaya_yatan):
        bankaya_yatan_list.append({
            'Nakit_ID': o.Odeme_ID,
            'Tarih': o.Tarih.strftime('%d.%m.%Y') if o.Tarih else '',
            'Donem': o.Donem if o.Donem else donem,
            'Tutar': float(o.Tutar) if o.Tutar else 0.0,
            'matched': bankaya_matched[idx]
        })

    # Build Nakit Girişi list with matched status (from Nakit)
    nakit_giris_list = []
    for idx, n in enumerate(nakit_giris):
        nakit_giris_list.append({
            'Nakit_ID': n.Nakit_ID,
            'Tarih': n.Tarih.strftime('%d.%m.%Y') if n.Tarih else '',
            'Donem': n.Donem if n.Donem else donem,
            'Tutar': float(n.Tutar) if n.Tutar else 0.0,
            'matched': nakit_matched[idx]
        })

    # Statistics
    eslesen = sum(1 for r in bankaya_yatan_list if r['matched'])
    bankaya_yatan_eslesmeyen = sum(1 for r in bankaya_yatan_list if not r['matched'])
    nakit_giris_eslesmeyen = sum(1 for r in nakit_giris_list if not r['matched'])
    toplam = len(bankaya_yatan_list) + nakit_giris_eslesmeyen
    esleme_orani = round((eslesen / toplam * 100)) if toplam > 0 else 100

    bankaya_yatan_toplam = sum(r['Tutar'] for r in bankaya_yatan_list)
    nakit_giris_toplam = sum(r['Tutar'] for r in nakit_giris_list)
    fark = bankaya_yatan_toplam - nakit_giris_toplam

    # Determine if user can see Gizli (hidden) categories (same as Ozet Kontrol Raporu logic)
    show_gizli = (user.Kullanici_Adi and user.Kullanici_Adi.lower() == 'admin')
    if not show_gizli:
        roles = auth_queries.get_user_roles(db_session, user.Kullanici_ID)
        show_gizli = 'admin' in [r.lower() for r in roles]
    if not show_gizli:
        show_gizli = auth_queries.has_permission(db_session, user.Kullanici_ID, "Gizli Kategori Veri Erişimi")

    # Fetch Gelir for Nakit category (matches Ozet Kontrol Raporu which uses k.Kategori_Adi LIKE '%Nakit%')
    # Use Kategori join to support Gizli filter
    gelir_nakit_query = db_session.query(func.sum(Gelir.Tutar)).join(Kategori, Gelir.Kategori_ID == Kategori.Kategori_ID).filter(
        Gelir.Sube_ID == sube_id,
        Gelir.Tarih >= start_date,
        Gelir.Tarih <= end_date,
        Kategori.Kategori_Adi.like('%Nakit%')
    )
    if not show_gizli:
        gelir_nakit_query = gelir_nakit_query.filter(Kategori.Gizli == 0)
    
    gelir_nakit_toplam = float(gelir_nakit_query.scalar() or 0.0)

    # Calculate Daily Expenses for "Kalan Nakit Bakiye" (matches Ozet Kontrol Raporu logic)
    ef_query = db_session.query(func.sum(EFatura.Tutar)).join(Kategori, EFatura.Kategori_ID == Kategori.Kategori_ID).filter(
        EFatura.Sube_ID == sube_id,
        EFatura.Donem == donem,
        EFatura.Gunluk_Harcama == 1,
        (EFatura.Giden_Fatura == 0) | (EFatura.Giden_Fatura == None)
    )
    if not show_gizli:
        ef_query = ef_query.filter(Kategori.Gizli == 0)
    gh_efatura = ef_query.scalar() or 0.0
    
    dh_query = db_session.query(func.sum(DigerHarcama.Tutar)).join(Kategori, DigerHarcama.Kategori_ID == Kategori.Kategori_ID).filter(
        DigerHarcama.Sube_ID == sube_id,
        DigerHarcama.Donem == donem,
        DigerHarcama.Gunluk_Harcama == 1
    )
    if not show_gizli:
        dh_query = dh_query.filter(Kategori.Gizli == 0)
    gh_diger = dh_query.scalar() or 0.0
    
    kalan_nakit_bakiye = gelir_nakit_toplam - (float(gh_efatura) + float(gh_diger))
    
    # Recalculate 'fark' based on Kalan Nakit Bakiye (matches Ozet Kontrol Raporu: Bankaya Yatan - Kalan Nakit)
    fark_bakiye = bankaya_yatan_toplam - kalan_nakit_bakiye

    sube_adi = next((s.Sube_Adi for s in auth_suber if s.Sube_ID == sube_id), '')
    
    from flask import make_response
    db_session.close()
    
    response = make_response(render_template(
        "nakit_yatirma_kontrol_raporu.html",
        user=user,
        subeler=auth_suber,
        secili_sube_id=sube_id,
        sube_adi=sube_adi,
        secili_donem=donem,
        current_donem=current_donem,
        donem_listesi=donem_listesi,
        bankaya_yatan=bankaya_yatan_list,
        nakit_giris=nakit_giris_list,
        eslesen=eslesen,
        bankaya_yatan_eslesmeyen=bankaya_yatan_eslesmeyen,
        nakit_giris_eslesmeyen=nakit_giris_eslesmeyen,
        esleme_orani=esleme_orani,
        bankaya_yatan_toplam=bankaya_yatan_toplam,
        nakit_giris_toplam=nakit_giris_toplam,
        fark=fark_bakiye,
        gelir_nakit_toplam=gelir_nakit_toplam,
        kalan_nakit_bakiye=kalan_nakit_bakiye
    ))
    
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Expires"] = "0"
    
    return response


@web_invoicing_bp.route("/odeme-rapor")
@login_required
@permission_required("Ödeme Rapor Görüntüleme")
def odeme_raporu():
    db_session = get_db_session()
    user = auth_queries.get_kullanici_by_id(db_session, session['user_id'])
    
    if not user:
        db_session.close()
        return redirect(url_for('web_auth.login'))
        
    all_suber = ref_queries.get_suber(db_session, limit=1000)
    is_admin = (user.Kullanici_Adi and user.Kullanici_Adi.lower() == 'admin')
    if not is_admin:
        roles = auth_queries.get_user_roles(db_session, user.Kullanici_ID)
        is_admin = 'admin' in [r.lower() for r in roles]

    auth_suber = all_suber if is_admin else [
        s for s in all_suber if s.Sube_ID in auth_queries.get_user_branches(db_session, user.Kullanici_ID)
    ]
    auth_sube_ids = [s.Sube_ID for s in auth_suber]

    sube_id_str = request.args.get("sube_id", "")
    sube_id = int(sube_id_str) if sube_id_str.isdigit() else (auth_suber[0].Sube_ID if auth_suber else None)

    if sube_id not in auth_sube_ids and auth_suber:
        sube_id = auth_suber[0].Sube_ID

    # Multi-select donem (comma separated or multiple args)
    donem_args = request.args.getlist("donem")
    if not donem_args and request.args.get("donem"):
        donem_args = request.args.get("donem").split(",")
    
    selected_donemler = [int(d) for d in donem_args if d.isdigit()]
    
    # Default to current period if none selected
    from datetime import date as _date
    _today = _date.today()
    current_donem = int(str(_today.year)[-2:] + str(_today.month).zfill(2))
    
    if not selected_donemler:
        selected_donemler = [current_donem]

    # Multi-select kategori
    kat_args = request.args.getlist("kategori")
    if not kat_args and request.args.get("kategori"):
        kat_args = request.args.get("kategori").split(",")
    selected_kategoriler = [int(k) for k in kat_args if k.isdigit()]

    # Period list (last 12 months)
    donem_listesi = []
    temp_date = _today
    for _ in range(12):
        d_val = int(str(temp_date.year)[-2:] + str(temp_date.month).zfill(2))
        donem_listesi.append(d_val)
        m = temp_date.month - 1
        y = temp_date.year
        if m == 0:
            m = 12
            y -= 1
        temp_date = _date(y, m, 1)

    # Fetch report data
    report_data = invoicing_queries.get_odeme_raporu_data(
        db_session, 
        sube_id=sube_id, 
        donem_list=selected_donemler,
        kategori_list=selected_kategoriler if selected_kategoriler else None
    )

    # Fetch all categories for filter
    all_kats = ref_queries.get_kategoriler(db_session, limit=1000)
    # Filter for 'Ödeme' type if possible, or just all
    payment_kats = sorted([
        {"id": k.Kategori_ID, "name": k.Kategori_Adi}
        for k in all_kats # if k.Tip == 'Ödeme'
    ], key=lambda x: x["name"])

    sube_adi = next((s.Sube_Adi for s in auth_suber if s.Sube_ID == sube_id), '')
    
    db_session.close()
    
    return render_template(
        "odeme_raporu.html",
        user=user,
        subeler=auth_suber,
        secili_sube_id=sube_id,
        sube_adi=sube_adi,
        secili_donemler=selected_donemler,
        secili_kategoriler=selected_kategoriler,
        donem_listesi=donem_listesi,
        kategoriler=payment_kats,
        report_data=report_data
    )


@web_invoicing_bp.route("/fatura-diger-harcama-rapor")
@login_required
@permission_required("Fatura & Diğer Harcama Rapor Görüntüleme")
def fatura_diger_harcama_raporu():
    """
    Combined report for EFatura and DigerHarcama.
    """
    db_session = get_db_session()
    user = auth_queries.get_kullanici_by_id(db_session, session['user_id'])
    
    if not user:
        db_session.close()
        return redirect(url_for('web_auth.login'))
        
    all_suber = ref_queries.get_suber(db_session, limit=1000)
    
    is_admin = (user.Kullanici_Adi and user.Kullanici_Adi.lower() == 'admin')
    if not is_admin:
        roles = auth_queries.get_user_roles(db_session, user.Kullanici_ID)
        is_admin = 'admin' in [r.lower() for r in roles]

    auth_suber = all_suber if is_admin else [
        s for s in all_suber if s.Sube_ID in auth_queries.get_user_branches(db_session, user.Kullanici_ID)
    ]
    
    if not auth_suber:
        db_session.close()
        return redirect(url_for('main.dashboard'))

    # Selected Sube
    sube_id = request.args.get('sube_id', auth_suber[0].Sube_ID, type=int)
    
    # Get periods & categories (multi-select)
    selected_donemler = request.args.getlist('donem', type=int)
    selected_kategoriler = request.args.getlist('kategori', type=int)

    from datetime import date as _date
    _today = _date.today()
    current_donem = int(str(_today.year)[-2:] + str(_today.month).zfill(2))
    
    if not selected_donemler:
        selected_donemler = [current_donem]

    # Fetch report data
    report_data = invoicing_queries.get_fatura_diger_harcama_rapor(
        db_session,
        sube_id=sube_id,
        donem_list=selected_donemler,
        kategori_list=selected_kategoriler if selected_kategoriler else None
    )

    # Categories for filter
    all_kats = ref_queries.get_kategoriler(db_session, limit=1000)
    kategoriler = sorted([
        {"id": k.Kategori_ID, "name": k.Kategori_Adi}
        for k in all_kats
    ], key=lambda x: x["name"])
    
    # Periods for filter (last 12 months)
    donem_listesi = []
    temp_date = _today
    for _ in range(12):
        d_val = int(str(temp_date.year)[-2:] + str(temp_date.month).zfill(2))
        donem_listesi.append(d_val)
        m = temp_date.month - 1
        y = temp_date.year
        if m == 0: m = 12; y -= 1
        temp_date = _date(y, m, 1)

    sube_adi = next((s.Sube_Adi for s in auth_suber if s.Sube_ID == sube_id), '')
    
    db_session.close()
    
    return render_template(
        "fatura_diger_harcama_raporu.html",
        user=user,
        subeler=auth_suber,
        secili_sube_id=sube_id,
        sube_adi=sube_adi,
        secili_donemler=selected_donemler,
        secili_kategoriler=selected_kategoriler,
        donem_listesi=donem_listesi,
        kategoriler=kategoriler,
        report_data=report_data
    )


@web_invoicing_bp.route("/pos-kontrol-dashboard")
@login_required
@permission_required("POS Kontrol Dashboard Görüntüleme")
def pos_kontrol_dashboard():
    """
    POS Reconciliation Dashboard.
    Matches Gelir (POS) with POSHareketleri and Odeme records.
    """
    db_session = get_db_session()
    user = auth_queries.get_kullanici_by_id(db_session, session['user_id'])
    
    if not user:
        db_session.close()
        return redirect(url_for('web_auth.login'))
        
    all_suber = ref_queries.get_suber(db_session, limit=1000)
    
    is_admin = (user.Kullanici_Adi and user.Kullanici_Adi.lower() == 'admin')
    if not is_admin:
        roles = auth_queries.get_user_roles(db_session, user.Kullanici_ID)
        is_admin = 'admin' in [r.lower() for r in roles]

    auth_suber = all_suber if is_admin else [
        s for s in all_suber if s.Sube_ID in auth_queries.get_user_branches(db_session, user.Kullanici_ID)
    ]
    
    if not auth_suber:
        db_session.close()
        return redirect(url_for('main.dashboard'))

    # Selected Sube & Donem
    sube_id = request.args.get('sube_id', auth_suber[0].Sube_ID, type=int)
    
    from datetime import date as _date
    _today = _date.today()
    current_donem = int(str(_today.year)[-2:] + str(_today.month).zfill(2))
    donem = request.args.get('donem', current_donem, type=int)

    # Periods for filter (last 12 months)
    donem_listesi = []
    temp_date = _today
    for _ in range(12):
        d_val = int(str(temp_date.year)[-2:] + str(temp_date.month).zfill(2))
        donem_listesi.append(d_val)
        m = temp_date.month - 1
        y = temp_date.year
        if m == 0: m = 12; y -= 1
        temp_date = _date(y, m, 1)

    # Fetch Dashboard Data
    dashboard_data = invoicing_queries.get_pos_kontrol_dashboard_data(
        db_session,
        sube_id=sube_id,
        donem=donem
    )

    sube_adi = next((s.Sube_Adi for s in auth_suber if s.Sube_ID == sube_id), '')

    db_session.close()
    
    return render_template(
        "pos_kontrol_dashboard.html",
        user=user,
        auth_suber=auth_suber,
        secili_sube_id=sube_id,
        sube_adi=sube_adi,
        secili_donem=donem,
        donem_listesi=donem_listesi,
        dashboard_data=dashboard_data
    )


@web_invoicing_bp.route("/online-kontrol-dashboard")
@login_required
@permission_required("Online Kontrol Dashboard Görüntüleme")
def online_kontrol_dashboard():
    """
    Online Platforms Reconciliation Dashboard.
    Matches Gelir (System) with B2BEkstre (Virman) and EFatura (Commission).
    """
    db_session = get_db_session()
    user = auth_queries.get_kullanici_by_id(db_session, session['user_id'])
    
    if not user:
        db_session.close()
        return redirect(url_for('web_auth.login'))
        
    all_suber = ref_queries.get_suber(db_session, limit=1000)
    
    is_admin = (user.Kullanici_Adi and user.Kullanici_Adi.lower() == 'admin')
    if not is_admin:
        roles = auth_queries.get_user_roles(db_session, user.Kullanici_ID)
        is_admin = 'admin' in [r.lower() for r in roles]

    auth_suber = all_suber if is_admin else [
        s for s in all_suber if s.Sube_ID in auth_queries.get_user_branches(db_session, user.Kullanici_ID)
    ]
    
    if not auth_suber:
        db_session.close()
        return redirect(url_for('main.dashboard'))

    # Selected Sube & Donem
    sube_id = request.args.get('sube_id', auth_suber[0].Sube_ID, type=int)
    
    from datetime import date as _date
    _today = _date.today()
    current_donem = int(str(_today.year)[-2:] + str(_today.month).zfill(2))
    donem = request.args.get('donem', current_donem, type=int)

    # Periods for filter (last 12 months)
    donem_listesi = []
    temp_date = _today
    for _ in range(12):
        d_val = int(str(temp_date.year)[-2:] + str(temp_date.month).zfill(2))
        donem_listesi.append(d_val)
        m = temp_date.month - 1
        y = temp_date.year
        if m == 0: m = 12; y -= 1
        temp_date = _date(y, m, 1)

    # Fetch Dashboard Data
    dashboard_data = invoicing_queries.get_online_kontrol_dashboard_data(
        db_session,
        sube_id=sube_id,
        donem=donem
    )

    sube_adi = next((s.Sube_Adi for s in auth_suber if s.Sube_ID == sube_id), '')

    db_session.close()
    
    return render_template(
        "online_kontrol_dashboard.html",
        user=user,
        auth_suber=auth_suber,
        secili_sube_id=sube_id,
        sube_adi=sube_adi,
        secili_donem=donem,
        donem_listesi=donem_listesi,
        dashboard_data=dashboard_data
    )


@web_invoicing_bp.route("/yemek-ceki-kontrol-dashboard")
@login_required
@permission_required("Yemek Çeki Kontrol Dashboard Görüntüleme")
def yemek_ceki_kontrol_dashboard():
    """
    Yemek Çeki (Meal Voucher) Reconciliation Dashboard.
    Matches Gelir (Voucher Sales) with EFatura and Odeme records.
    """
    db_session = get_db_session()
    user = auth_queries.get_kullanici_by_id(db_session, session['user_id'])
    
    if not user:
        db_session.close()
        return redirect(url_for('web_auth.login'))
        
    all_suber = ref_queries.get_suber(db_session, limit=1000)
    
    is_admin = (user.Kullanici_Adi and user.Kullanici_Adi.lower() == 'admin')
    if not is_admin:
        roles = auth_queries.get_user_roles(db_session, user.Kullanici_ID)
        is_admin = 'admin' in [r.lower() for r in roles]

    auth_suber = all_suber if is_admin else [
        s for s in all_suber if s.Sube_ID in auth_queries.get_user_branches(db_session, user.Kullanici_ID)
    ]
    
    if not auth_suber:
        db_session.close()
        return redirect(url_for('main.dashboard'))

    # Selected Sube & Donem
    sube_id = request.args.get('sube_id', auth_suber[0].Sube_ID, type=int)
    
    from datetime import date as _date
    _today = _date.today()
    current_donem = int(str(_today.year)[-2:] + str(_today.month).zfill(2))
    donem = request.args.get('donem', current_donem, type=int)

    # Periods for filter (last 12 months)
    donem_listesi = []
    temp_date = _today
    for _ in range(12):
        d_val = int(str(temp_date.year)[-2:] + str(temp_date.month).zfill(2))
        donem_listesi.append(d_val)
        m = temp_date.month - 1
        y = temp_date.year
        if m == 0: m = 12; y -= 1
        temp_date = _date(y, m, 1)

    # Fetch Dashboard Data
    dashboard_data = invoicing_queries.get_yemek_ceki_kontrol_dashboard_data(
        db_session,
        sube_id=sube_id,
        donem=donem
    )

    sube_adi = next((s.Sube_Adi for s in auth_suber if s.Sube_ID == sube_id), '')

    db_session.close()
    
    return render_template(
        "yemek_ceki_kontrol_dashboard.html",
        user=user,
        auth_suber=auth_suber,
        secili_sube_id=sube_id,
        sube_adi=sube_adi,
        secili_donem=donem,
        donem_listesi=donem_listesi,
        dashboard_data=dashboard_data
    )


@web_invoicing_bp.route("/fatura-rapor")
@login_required
@permission_required("Fatura Rapor Görüntüleme")
def fatura_raporu():
    db_session = get_db_session()
    user = auth_queries.get_kullanici_by_id(db_session, session['user_id'])
    
    if not user:
        db_session.close()
        return redirect(url_for('web_auth.login'))
        
    all_suber = ref_queries.get_suber(db_session, limit=1000)
    is_admin = (user.Kullanici_Adi and user.Kullanici_Adi.lower() == 'admin')
    if not is_admin:
        roles = auth_queries.get_user_roles(db_session, user.Kullanici_ID)
        is_admin = 'admin' in [r.lower() for r in roles]

    auth_suber = all_suber if is_admin else [
        s for s in all_suber if s.Sube_ID in auth_queries.get_user_branches(db_session, user.Kullanici_ID)
    ]
    auth_sube_ids = [s.Sube_ID for s in auth_suber]

    sube_id_str = request.args.get("sube_id", "")
    sube_id = int(sube_id_str) if sube_id_str.isdigit() else (auth_suber[0].Sube_ID if auth_suber else None)

    if sube_id not in auth_sube_ids and auth_suber:
        sube_id = auth_suber[0].Sube_ID

    # Multi-select donem
    donem_args = request.args.getlist("donem")
    if not donem_args and request.args.get("donem"):
        donem_args = request.args.get("donem").split(",")
    
    selected_donemler = [int(d) for d in donem_args if d.isdigit()]
    
    # Default to current period if none selected
    from datetime import date as _date
    _today = _date.today()
    current_donem = int(str(_today.year)[-2:] + str(_today.month).zfill(2))
    
    if not selected_donemler:
        selected_donemler = [current_donem]

    # Multi-select kategori
    kat_args = request.args.getlist("kategori")
    if not kat_args and request.args.get("kategori"):
        kat_args = request.args.get("kategori").split(",")
    selected_kategoriler = [int(k) for k in kat_args if k.isdigit()]

    # Period list (last 12 months)
    donem_listesi = []
    temp_date = _today
    for _ in range(12):
        d_val = int(str(temp_date.year)[-2:] + str(temp_date.month).zfill(2))
        donem_listesi.append(d_val)
        m = temp_date.month - 1
        y = temp_date.year
        if m == 0:
            m = 12
            y -= 1
        temp_date = _date(y, m, 1)

    # Fetch report data
    report_data = invoicing_queries.get_fatura_raporu_data(
        db_session, 
        sube_id=sube_id, 
        donem_list=selected_donemler,
        kategori_list=selected_kategoriler if selected_kategoriler else None
    )

    # Fetch and filter categories for e-Fatura
    all_kats = ref_queries.get_kategoriler(db_session, limit=1000)
    # The legacy code uses a specific filter for e-Fatura categories
    # Assuming Kategori has a Tip or similar, or based on UstKategori
    invoice_kats = sorted([
        {"id": k.Kategori_ID, "name": k.Kategori_Adi}
        for k in all_kats
    ], key=lambda x: x["name"])

    sube_adi = next((s.Sube_Adi for s in auth_suber if s.Sube_ID == sube_id), '')
    
    db_session.close()
    
    return render_template(
        "fatura_raporu.html",
        user=user,
        subeler=auth_suber,
        secili_sube_id=sube_id,
        sube_adi=sube_adi,
        secili_donemler=selected_donemler,
        secili_kategoriler=selected_kategoriler,
        donem_listesi=donem_listesi,
        kategoriler=invoice_kats,
        report_data=report_data
    )


@web_invoicing_bp.route("/vps-dashboard", methods=["GET"])
@login_required
@permission_required("VPS Dashboard Görüntüleme")
def vps_dashboard():
    """
    VPS Dashboard page.
    """
    db_session = get_db_session()
    user = auth_queries.get_kullanici_by_id(db_session, session['user_id'])
    
    if not user:
        db_session.close()
        return redirect(url_for('web_auth.login'))
        
    all_suber = ref_queries.get_suber(db_session, limit=1000)
    
    is_admin = (user.Kullanici_Adi and user.Kullanici_Adi.lower() == 'admin')
    if not is_admin:
        roles = auth_queries.get_user_roles(db_session, user.Kullanici_ID)
        is_admin = 'admin' in [r.lower() for r in roles]

    auth_suber = all_suber if is_admin else [
        s for s in all_suber if s.Sube_ID in auth_queries.get_user_branches(db_session, user.Kullanici_ID)
    ]
    
    if not auth_suber:
        db_session.close()
        return redirect(url_for('main.dashboard'))

    # Get filter params
    sube_id = request.args.get('sube_id', None, type=int)
    if sube_id is None and auth_suber:
        sube_id = auth_suber[0].Sube_ID
    
    # Calculate current period (YYMM)
    from datetime import date as _date
    _today = _date.today()
    current_donem = int(str(_today.year)[-2:] + str(_today.month).zfill(2))
    
    donem = request.args.get('donem', current_donem, type=int)

    # Fetch VPS data
    dashboard_data = invoicing_queries.get_vps_dashboard_data(db_session, sube_id, donem)

    # Donem listesi (son 12 ay)
    donem_listesi = []
    temp_date = _today
    for _ in range(12):
        d_val = int(str(temp_date.year)[-2:] + str(temp_date.month).zfill(2))
        donem_listesi.append(d_val)
        m = temp_date.month - 1
        y = temp_date.year
        if m == 0:
            m = 12
            y -= 1
        temp_date = _date(y, m, 1)

    db_session.close()
    
    return render_template(
        "vps_dashboard.html",
        user=user,
        auth_suber=auth_suber,
        secili_sube_id=sube_id,
        secili_donem=donem,
        donem_listesi=donem_listesi,
        dashboard_data=dashboard_data
    )
@web_invoicing_bp.route("/fatura-bolme-yonetimi", methods=["GET"])
@login_required
@permission_required("Fatura Bölme Yönetimi Ekranı Görüntüleme")
def fatura_bolme_yonetimi():
    """
    Fatura Bölme Yönetimi (Invoice Split Management) page.
    """
    db_session = get_db_session()
    user = auth_queries.get_kullanici_by_id(db_session, session['user_id'])
    
    if not user:
        db_session.close()
        return redirect(url_for('web_auth.login'))
        
    all_suber = ref_queries.get_suber(db_session, limit=1000)
    
    # Simple admin check
    is_admin = (user.Kullanici_Adi and user.Kullanici_Adi.lower() == 'admin')
    if not is_admin:
        roles = auth_queries.get_user_roles(db_session, user.Kullanici_ID)
        is_admin = 'admin' in [r.lower() for r in roles]

    auth_suber = all_suber if is_admin else [
        s for s in all_suber if s.Sube_ID in auth_queries.get_user_branches(db_session, user.Kullanici_ID)
    ]
    
    db_session.close()
    
    return render_template(
        "fatura_bolme_yonetimi.html",
        user=user,
        subeler=auth_suber
    )

@web_invoicing_bp.route("/mutabakat-yonetimi")
@login_required
@permission_required("Mutabakat Yönetimi Ekranı Görüntüleme")
def mutabakat_yonetimi():
    """Render Mutabakat Yönetimi screen."""
    db_session = get_db_session()
    user = db_session.get(Kullanici, session["user_id"])
        
    # Determine default authorized branch
    all_suber = ref_queries.get_suber(db_session, limit=1000)
    
    is_admin = (user.Kullanici_Adi and user.Kullanici_Adi.lower() == 'admin')
    if not is_admin:
        roles = auth_queries.get_user_roles(db_session, user.Kullanici_ID)
        is_admin = 'admin' in [r.lower() for r in roles]

    auth_suber = all_suber if is_admin else [
        s for s in all_suber if s.Sube_ID in auth_queries.get_user_branches(db_session, user.Kullanici_ID)
    ]
    
    # Default sube_id: First authorized branch
    secili_sube_id = auth_suber[0].Sube_ID if auth_suber else None
    
    # Get firms for the dropdown/modal
    cariler = db_session.query(Cari).filter(Cari.Aktif_Pasif == True).order_by(Cari.Alici_Unvani).all()
    
    db_session.close()
    return render_template(
        "mutabakat_yonetimi.html",
        user=user,
        cariler=cariler,
        subeler=auth_suber,
        secili_sube_id=secili_sube_id
    )
