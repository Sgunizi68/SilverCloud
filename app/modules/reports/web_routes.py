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
        
    from datetime import date
    today = date.today()
    start_date = request.args.get('start_date', today.strftime('%Y-%m-%d'))
    
    report_data = None
    if sube_id:
        report_data = report_queries.get_cari_borc_takip_raporu(
            start_date=start_date, 
            sube_id=sube_id
        )
        
    db_session.close()
    
    return render_template(
        "cari_borc_takip.html",
        user=user,
        subeler=auth_suber,
        report_data=report_data,
        secili_sube_id=sube_id,
        start_date=start_date
    )


@reports_bp.route("/gelir-girisi-kontrol", methods=["GET"])
@login_required
@permission_required("Gelir Girişi Kontrol Raporu Görüntüleme")
def gelir_girisi_kontrol():
    """Gelir Girişi Kontrol Raporu – compares Robotpos_Gelir vs Gelir."""
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

    report_data = None
    if sube_id and donem:
        report_data = report_queries.get_gelir_kontrol_raporu(db_session, sube_id=sube_id, donem=donem)

    db_session.close()

    return render_template(
        "gelir_girisi_kontrol.html",
        user=user,
        subeler=auth_suber,
        report_data=report_data,
        secili_sube_id=sube_id,
        secili_donem=donem,
        donem_list=donem_list
    )
