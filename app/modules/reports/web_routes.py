from flask import render_template, session, redirect, url_for, request
from . import reports_bp
from app.modules.auth import queries as auth_queries
from app.modules.reference import queries as ref_queries
from . import queries as report_queries
from app.common.database import get_db_session
from app.common.decorators import login_required, permission_required
from datetime import date

@reports_bp.route("/bayi-karlilik-raporu", methods=["GET"])
@login_required
@permission_required("Bayi Karlılık Raporu Görüntüleme")
def bayi_karlilik_raporu():
    """
    Bayi Karlılık Raporu page.
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
    
    # Filter params
    sube_id = request.args.get('sube_id', None, type=int)
    if sube_id is None and auth_suber:
        sube_id = auth_suber[0].Sube_ID
        
    year = request.args.get('year', date.today().year, type=int)
    
    # Year range (e.g., last 5 years)
    current_year = date.today().year
    years = list(range(current_year, current_year - 6, -1))
    
    report_data = None
    if sube_id:
        report_data = report_queries.get_bayi_karlilik_raporu(year=year, sube_id=sube_id)
        
    db_session.close()
    
    return render_template(
        "bayi_karlilik_raporu.html",
        user=user,
        subeler=auth_suber,
        report_data=report_data,
        secili_sube_id=sube_id,
        secili_year=year,
        years=years
    )

@reports_bp.route("/ozet-kontrol-raporu", methods=["GET"])
@login_required
@permission_required("Özet Kontrol Raporu Görüntüleme")
def ozet_kontrol_raporu():
    """
    Özet Kontrol Raporu page.
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
    
    # Filter params
    sube_id = request.args.get('sube_id', None, type=int)
    if sube_id is None and auth_suber:
        sube_id = auth_suber[0].Sube_ID
        
    donem = request.args.get('donem', None, type=int)
    from datetime import date
    if donem is None:
        today = date.today()
        # Default to previous month if not specified, or current month
        # Using YYMM format
        donem = int(f"{today.year % 100:02d}{today.month:02d}")
    
    # Generate donem list backwards from current month
    today = date.today()
    donem_list = []
    y = today.year % 100
    m = today.month
    for _ in range(24): # Last 24 months
        donem_val = int(f"{y:02d}{m:02d}")
        # Format for display: YYMM - Month YYYY
        month_names = ["", "Ocak", "Şubat", "Mart", "Nisan", "Mayıs", "Haziran", "Temmuz", "Ağustos", "Eylül", "Ekim", "Kasım", "Aralık"]
        display_str = f"{donem_val} - {month_names[m]} 20{y:02d}"
        donem_list.append({"value": donem_val, "display": display_str})
        
        m -= 1
        if m == 0:
            m = 12
            y -= 1
    
    report_data = None
    if sube_id and donem:
        # Determine if user can see Gizli (hidden) categories
        show_gizli = (user.Kullanici_Adi and user.Kullanici_Adi.lower() == 'admin')
        if not show_gizli:
            roles = auth_queries.get_user_roles(db_session, user.Kullanici_ID)
            show_gizli = 'admin' in [r.lower() for r in roles]
        
        if not show_gizli:
            show_gizli = auth_queries.has_permission(db_session, user.Kullanici_ID, "Gizli Kategori Veri Erişimi")

        report_data = report_queries.get_ozet_kontrol_raporu(db_session, sube_id=sube_id, donem=donem, show_gizli=show_gizli)
        
    db_session.close()
    
    return render_template(
        "ozet_kontrol_raporu.html",
        user=user,
        subeler=auth_suber,
        report_data=report_data,
        secili_sube_id=sube_id,
        secili_donem=donem,
        donem_list=donem_list,
        show_gizli=show_gizli
    )

@reports_bp.route("/nakit-akis-gelir-raporu", methods=["GET"])
@login_required
@permission_required("Nakit Akış - Gelir Raporu Görüntüleme")
def nakit_akis_gelir_raporu():
    """
    Nakit Akış - Gelir Raporu page.
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
    
    # Filter params
    sube_id = request.args.get('sube_id', None, type=int)
    if sube_id is None and auth_suber:
        sube_id = auth_suber[0].Sube_ID
        
    from datetime import date, timedelta
    today = date.today()
    start_of_month = today.replace(day=1)
    
    start_date = request.args.get('start_date', start_of_month.strftime('%Y-%m-%d'))
    end_date = request.args.get('end_date', today.strftime('%Y-%m-%d'))
    
    report_data = None
    if sube_id:
        report_data = report_queries.get_nakit_akis_gelir_raporu(
            start_date=start_date, 
            end_date=end_date, 
            sube_id=sube_id
        )
        
    db_session.close()
    
    return render_template(
        "nakit_akis_gelir_raporu.html",
        user=user,
        subeler=auth_suber,
        report_data=report_data,
        secili_sube_id=sube_id,
        start_date=start_date,
        end_date=end_date
    )

@reports_bp.route("/cari-borc-takip-sistemi", methods=["GET"])
@login_required
@permission_required("Cari Borç Takip Sistemi Görüntüleme")
def cari_borc_takip_sistemi():
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
    
    # Filter params
    sube_id = request.args.get('sube_id', None, type=int)
    if sube_id is None and auth_suber:
        sube_id = auth_suber[0].Sube_ID
        
    tip = request.args.get('tip', 'Açik Hesap')
    
    report_data = None
    if sube_id:
        report_data = report_queries.get_cari_borc_takip_raporu(
            sube_id=sube_id,
            tip=tip
        )
        
    db_session.close()
    
    tip_list = [
        "Tümü", "Açik Hesap", "Cari", "Nakit", "Kredi Karti", 
        "Havale/EFT", "Çek", "Senet", "Diger"
    ]
    
    return render_template(
        "cari_borc_takip.html",
        user=user,
        subeler=auth_suber,
        report_data=report_data,
        secili_sube_id=sube_id,
        secili_tip=tip,
        tip_list=tip_list
    )


@reports_bp.route("/gelir-girisi-kontrol", methods=["GET"])
@login_required
@permission_required("Gelir Girişi Kontrol Raporu Görüntüleme")
def gelir_girisi_kontrol():
    """Gelir Girişi Kontrol Raporu – compares Robotpos_Gelir vs Gelir (pivot: kategori x day)."""
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

    sube_id = request.args.get('sube_id', None, type=int)
    if sube_id is None and auth_suber:
        sube_id = auth_suber[0].Sube_ID

    today = date.today()
    donem = request.args.get('donem', None, type=int)
    if donem is None:
        donem = int(f"{today.year % 100:02d}{today.month:02d}")

    month_names = ["", "Ocak", "Şubat", "Mart", "Nisan", "Mayıs", "Haziran",
                   "Temmuz", "Ağustos", "Eylül", "Ekim", "Kasım", "Aralık"]
    donem_list = []
    y, m = today.year % 100, today.month
    for _ in range(24):
        donem_val = int(f"{y:02d}{m:02d}")
        donem_list.append({"value": donem_val, "display": f"{month_names[m]} 20{y:02d}"})
        m -= 1
        if m == 0:
            m = 12
            y -= 1

    # Build pivot data
    pivot = None
    summary = None
    if sube_id and donem:
        raw = report_queries.get_gelir_kontrol_raporu(db_session, sube_id=sube_id, donem=donem)

        # Collect unique days and categories
        days_set = set()
        cats_set = []  # ordered, no dup
        cats_seen = set()
        for row in raw["rows"]:
            # row["Tarih"] is like "01.03.2026" -> extract day
            try:
                day_num = int(row["Tarih"].split(".")[0])
            except Exception:
                day_num = 0
            days_set.add(day_num)
            if row["Kategori_Adi"] not in cats_seen:
                cats_seen.add(row["Kategori_Adi"])
                cats_set.append(row["Kategori_Adi"])

        days = sorted(days_set)

        # pivot[kategori][day] = {r, g, f}
        pivot_data = {cat: {d: {"r": 0.0, "g": 0.0, "f": 0.0} for d in days} for cat in cats_set}
        day_totals = {d: {"r": 0.0, "g": 0.0, "f": 0.0} for d in days}
        row_totals = {cat: {"r": 0.0, "g": 0.0, "f": 0.0} for cat in cats_set}
        grand = {"r": 0.0, "g": 0.0, "f": 0.0}

        for row in raw["rows"]:
            try:
                day_num = int(row["Tarih"].split(".")[0])
            except Exception:
                continue
            cat = row["Kategori_Adi"]
            r = row["Robotpos_Tutar"]
            g = row["Gelir_Tutar"]
            f = row["Fark"]
            pivot_data[cat][day_num]["r"] += r
            pivot_data[cat][day_num]["g"] += g
            pivot_data[cat][day_num]["f"] += f
            day_totals[day_num]["r"] += r
            day_totals[day_num]["g"] += g
            day_totals[day_num]["f"] += f
            row_totals[cat]["r"] += r
            row_totals[cat]["g"] += g
            row_totals[cat]["f"] += f
            grand["r"] += r
            grand["g"] += g
            grand["f"] += f

        # Process manual RobotPos entries from GelirEkstra
        manual_dp = raw.get("manual_robotpos", {})
        pivot_manual = {d: manual_dp.get(d, 0.0) for d in days}
        pivot_manual_diff = {d: pivot_manual[d] - day_totals[d]["r"] for d in days}
        
        # Calculate totals for these rows
        total_manual = sum(pivot_manual.values())
        total_manual_diff = total_manual - grand["r"]

        pivot = {
            "days": days,
            "categories": cats_set,
            "data": pivot_data,
            "day_totals": day_totals,
            "row_totals": row_totals,
            "grand": grand,
            "manual_robotpos": pivot_manual,
            "manual_diff": pivot_manual_diff,
            "total_manual": total_manual,
            "total_manual_diff": total_manual_diff,
        }
        summary = raw["summary"]

    db_session.close()

    return render_template(
        "gelir_girisi_kontrol.html",
        user=user,
        subeler=auth_suber,
        pivot=pivot,
        summary=summary,
        secili_sube_id=sube_id,
        secili_donem=donem,
        donem_list=donem_list
    )
