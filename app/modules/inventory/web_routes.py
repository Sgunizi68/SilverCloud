from datetime import datetime, date
from flask import Blueprint, render_template, session, redirect, url_for, request, flash, jsonify
from functools import wraps
from app.modules.auth import queries as auth_queries
from app.modules.reference import queries as ref_queries
from app.modules.inventory import queries as inventory_queries
from app.common.database import get_db_session

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return redirect(url_for('web_auth.login', next=request.url))
        return f(*args, **kwargs)
    return decorated_function

web_inventory_bp = Blueprint("web_inventory", __name__)

@web_inventory_bp.route("/stok-tanimlama", methods=["GET"])
@login_required
def stok_tanimlama():
    """
    Stok Tanımlama (Stock Definition) page.
    """
    db_session = get_db_session()
    user = auth_queries.get_kullanici_by_id(db_session, session['user_id'])
    
    if not user:
        db_session.close()
        return redirect(url_for('web_auth.login'))
        
    # Permission check
    if not auth_queries.has_permission(db_session, user.Kullanici_ID, "Stok Tanımlama Ekranı Görüntüleme"):
        db_session.close()
        flash("Bu sayfayı görüntüleme yetkiniz yok.", "danger")
        return redirect(url_for("main.dashboard"))

    # Simple admin check
    is_admin = (user.Kullanici_Adi and user.Kullanici_Adi.lower() == 'admin')
    if not is_admin:
        roles = auth_queries.get_user_roles(db_session, user.Kullanici_ID)
        is_admin = 'admin' in [r.lower() for r in roles]

    # Fetch initial stock list (first 1000)
    stoklar = inventory_queries.get_stoklar(db_session, limit=1000)
    
    # Get distinct product groups for filtering/adding
    urun_grupları = sorted(list(set([s.Urun_Grubu for s in stoklar if s.Urun_Grubu]))) if stoklar else []
    birimler = sorted(list(set([s.Birimi for s in stoklar if s.Birimi]))) if stoklar else ["AD", "KG", "LT", "PK"]
    siniflar = sorted(list(set([s.Sinif for s in stoklar if s.Sinif]))) if stoklar else []

    db_session.close()
    
    return render_template(
        "stok_tanimlama.html",
        user=user,
        stoklar=stoklar,
        urun_grupları=urun_grupları,
        birimler=birimler,
        siniflar=siniflar,
        is_admin=is_admin
    )

@web_inventory_bp.route("/stok-fiyat-tanimlama", methods=["GET"])
@login_required
def stok_fiyat_tanimlama():
    """
    Stok Fiyat Tanımlama (Stock Price Definition) page.
    """
    db_session = get_db_session()
    user = auth_queries.get_kullanici_by_id(db_session, session['user_id'])
    
    if not user:
        db_session.close()
        return redirect(url_for('web_auth.login'))
        
    # Permission check
    if not auth_queries.has_permission(db_session, user.Kullanici_ID, "Stok Fiyat Tanımlama Ekranı Görüntüleme"):
        db_session.close()
        flash("Bu sayfayı görüntüleme yetkiniz yok.", "danger")
        return redirect(url_for("main.dashboard"))

    # Branch authorization check
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
        flash("Yetkiniz olan şube bulunamadı.", "warning")
        return redirect(url_for("main.dashboard"))

    # Selected branch
    sube_id = request.args.get('sube_id', type=int)
    if not sube_id or sube_id not in [s.Sube_ID for s in auth_suber]:
        sube_id = auth_suber[0].Sube_ID

    # Fetch prices for selected branch
    fiyatlar = inventory_queries.get_stok_fiyatlar(db_session, sube_id=sube_id, limit=2000)
    
    # Fetch all stocks to map Material Code -> Description
    stoklar = inventory_queries.get_stoklar(db_session, limit=2000)
    stok_map = {s.Malzeme_Kodu: s.Malzeme_Aciklamasi for s in stoklar}

    db_session.close()
    
    return render_template(
        "stok_fiyat_tanimlama.html",
        user=user,
        subeler=auth_suber,
        secili_sube_id=sube_id,
        fiyatlar=fiyatlar,
        stok_map=stok_map,
        stoklar=stoklar, # For the select list in modal
        is_admin=is_admin
    )

@web_inventory_bp.route("/stok-sayimi", methods=["GET"])
@login_required
def stok_sayimi():
    """
    Stok Sayımı (Stock Count) page - grouped by Urun_Grubu.
    """
    db_session = get_db_session()
    user = auth_queries.get_kullanici_by_id(db_session, session['user_id'])
    
    if not user:
        db_session.close()
        return redirect(url_for('web_auth.login'))
        
    if not auth_queries.has_permission(db_session, user.Kullanici_ID, "Stok Sayım Ekranı Görüntüleme"):
        db_session.close()
        flash("Bu sayfayı görüntüleme yetkiniz yok.", "danger")
        return redirect(url_for("main.dashboard"))

    # Branch authorization
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
        flash("Yetkiniz olan şube bulunamadı.", "warning")
        return redirect(url_for("main.dashboard"))

    sube_id = request.args.get('sube_id', type=int)
    if not sube_id or sube_id not in [s.Sube_ID for s in auth_suber]:
        sube_id = auth_suber[0].Sube_ID

    # Find selected branch name
    sube_adi = next((s.Sube_Adi for s in auth_suber if s.Sube_ID == sube_id), "")

    from datetime import datetime
    now = datetime.now()
    default_donem = int(f"{now.strftime('%y')}{now.strftime('%m')}")
    secili_donem = request.args.get("donem", default_donem, type=int)

    # Fetch counts for branch+period
    sayimlar = inventory_queries.get_stok_sayimlar(
        db_session, sube_id=sube_id, donem=secili_donem, limit=5000
    )
    sayim_map = {s.Malzeme_Kodu: float(s.Miktar) for s in sayimlar}

    # All active stocks
    stoklar = inventory_queries.get_stoklar(db_session, limit=5000)
    aktif_stoklar = [s for s in stoklar if s.Aktif_Pasif]

    # Calculate end of period date
    yy = secili_donem // 100
    mm = secili_donem % 100
    import calendar
    _, last_day = calendar.monthrange(2000 + yy, mm)
    period_end_date = date(2000 + yy, mm, last_day)

    # Prices for this branch (most recent active price per material as of period end)
    fiyatlar = inventory_queries.get_stok_fiyatlar(
        db_session, 
        sube_id=sube_id, 
        aktif_pasif=True, 
        baslangic_tarihine=period_end_date,
        limit=5000
    )
    fiyat_map = {}
    for f in fiyatlar:
        if f.Malzeme_Kodu not in fiyat_map:
            fiyat_map[f.Malzeme_Kodu] = float(f.Fiyat)

    db_session.close()

    # Group stocks by Urun_Grubu, sorted
    from collections import OrderedDict
    gruplu_stoklar = OrderedDict()
    sorted_stoklar = sorted(aktif_stoklar, key=lambda s: (s.Urun_Grubu or "", s.Malzeme_Kodu))
    for stok in sorted_stoklar:
        grup = stok.Urun_Grubu or "DİĞER"
        if grup not in gruplu_stoklar:
            gruplu_stoklar[grup] = []
        miktar = sayim_map.get(stok.Malzeme_Kodu, 0.0)
        fiyat = fiyat_map.get(stok.Malzeme_Kodu, 0.0)
        gruplu_stoklar[grup].append({
            "Malzeme_Kodu": stok.Malzeme_Kodu,
            "Malzeme_Aciklamasi": stok.Malzeme_Aciklamasi,
            "Birimi": stok.Birimi,
            "Miktar": miktar,
            "Fiyat": fiyat,
            "Tutar": miktar * fiyat,
        })

    # Calculate group subtotals and grand total
    genel_toplam = 0.0
    grup_toplamlar = {}
    for grup, items in gruplu_stoklar.items():
        grp_total = sum(item["Tutar"] for item in items)
        grup_toplamlar[grup] = grp_total
        genel_toplam += grp_total

    # Build period list
    donem_listesi = []
    curr_y = now.year
    curr_m = now.month
    for _ in range(12):
        d_val = int(f"{str(curr_y)[-2:]}{curr_m:02d}")
        months = ["", "Ocak", "Şubat", "Mart", "Nisan", "Mayıs", "Haziran", "Temmuz", "Ağustos", "Eylül", "Ekim", "Kasım", "Aralık"]
        d_label = f"{months[curr_m]} {curr_y} ({d_val})"
        donem_listesi.append({"val": d_val, "label": d_label})
        curr_m -= 1
        if curr_m == 0:
            curr_m = 12
            curr_y -= 1

    return render_template(
        "stok_sayimi.html",
        user=user,
        subeler=auth_suber,
        sube_adi=sube_adi,
        secili_sube_id=sube_id,
        secili_donem=secili_donem,
        donem_listesi=donem_listesi,
        gruplu_stoklar=gruplu_stoklar,
        grup_toplamlar=grup_toplamlar,
        genel_toplam=genel_toplam,
        is_admin=is_admin,
        current_donem=default_donem
    )


@web_inventory_bp.route("/stok-sayimi/kaydet", methods=["POST"])
@login_required
def stok_sayimi_kaydet():
    """Bulk save all stock counts from the form."""
    try:
        donem = int(request.form.get("donem", 0))
        sube_id = int(request.form.get("sube_id", 0))

        if not donem or not sube_id:
            flash("Dönem veya Şube bilgisi eksik.", "danger")
            return redirect(url_for("web_inventory.stok_sayimi", sube_id=sube_id, donem=donem))

        db_session = get_db_session()
        saved_count = 0

        for key, value in request.form.items():
            if key.startswith("miktar_"):
                malzeme_kodu = key.replace("miktar_", "")
                val_str = value.strip().replace(",", ".")
                if val_str == "":
                    continue
                try:
                    miktar = float(val_str)
                except ValueError:
                    continue
                inventory_queries.upsert_stok_sayim(
                    db_session,
                    malzeme_kodu=malzeme_kodu,
                    donem=donem,
                    miktar=miktar,
                    sube_id=sube_id
                )
                saved_count += 1

        db_session.close()
        flash(f"{saved_count} stok sayım kaydı başarıyla güncellendi.", "success")
        return redirect(url_for("web_inventory.stok_sayimi", sube_id=sube_id, donem=donem))
    except Exception as e:
        flash(f"Kayıt hatası: {str(e)}", "danger")
        return redirect(url_for("web_inventory.stok_sayimi"))
