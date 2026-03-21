"""
HR Web Routes (Server-Rendered)
Pages for HR domain such as Calisan Yonetimi.
"""

import json
from flask import Blueprint, render_template, session, redirect, url_for, request
from app.common.database import get_db_session
from app.modules.auth.web_routes import login_required
from app.modules.hr import queries
from app.modules.auth import queries as auth_queries
from app.modules.reference import queries as ref_queries

web_hr_bp = Blueprint("web_hr", __name__)

@web_hr_bp.route("/calisanlar", methods=["GET"])
@login_required
def calisanlar():
    """
    Calisan Yonetimi page.
    Shows the list of employees in a server-rendered table.
    """
    db_session = get_db_session()
    
    # Get current user
    user = auth_queries.get_kullanici_by_id(db_session, session['user_id'])
    
    if not user:
        db_session.close()
        return redirect(url_for('web_auth.login'))
        
    # Get sube_id from request args or default to user's first branch
    sube_id = request.args.get('sube_id', type=int)
    
    # Get all branches for topbar dropdown
    all_suber = ref_queries.get_suber(db_session, limit=1000)
    
    is_admin = False
    if user.Kullanici_Adi and user.Kullanici_Adi.lower() == 'admin':
        is_admin = True
    else:
        roles = auth_queries.get_user_roles(db_session, user.Kullanici_ID)
        if 'admin' in [r.lower() for r in roles]:
            is_admin = True
            
    if is_admin:
        auth_suber = all_suber
    else:
        authorized_branch_ids = auth_queries.get_user_branches(db_session, user.Kullanici_ID)
        auth_suber = [s for s in all_suber if s.Sube_ID in authorized_branch_ids]
    
    # If no sube_id provided, pick the first authorized one
    if sube_id is None and auth_suber:
        sube_id = auth_suber[0].Sube_ID
        
    # Get employees for the selected branch
    calisanlar_data = queries.get_calisanlar(db_session, sube_id=sube_id, limit=1000)
    
    calisanlar_list = []
    for c in calisanlar_data:
        calisanlar_list.append({
            "TC_No": c.TC_No,
            "Adi": c.Adi,
            "Soyadi": c.Soyadi,
            "Hesap_No": c.Hesap_No,
            "IBAN": c.IBAN,
            "Net_Maas": float(c.Net_Maas) if c.Net_Maas else 0.0,
            "Sigorta_Giris": c.Sigorta_Giris.isoformat() if c.Sigorta_Giris else "",
            "Sigorta_Cikis": c.Sigorta_Cikis.isoformat() if c.Sigorta_Cikis else "2099-01-01",
            "Aktif_Pasif": c.Aktif_Pasif,
            "Sube_ID": c.Sube_ID
        })
        
    subeler_list = [{"Sube_ID": s.Sube_ID, "Sube_Adi": s.Sube_Adi} for s in auth_suber]
    
    db_session.close()
    
    return render_template(
        "calisanlar.html",
        user=user,
        subeler=subeler_list,
        current_sube_id=sube_id,
        calisanlar=calisanlar_list
    )


@web_hr_bp.route("/puantaj-secim-yonetimi", methods=["GET"])
@login_required
def puantaj_secim_yonetimi():
    """
    Puantaj Secim Yonetimi page.
    Shows all attendance type selections in a server-rendered table.
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
        s for s in all_suber
        if s.Sube_ID in auth_queries.get_user_branches(db_session, user.Kullanici_ID)
    ]
    subeler_list = [{"Sube_ID": s.Sube_ID, "Sube_Adi": s.Sube_Adi} for s in auth_suber]

    # Get all puantaj secim records
    from app.modules.hr import queries
    secimler_data = queries.get_puantaj_secimler(db_session, skip=0, limit=1000)
    secimler_list = [
        {
            "Secim_ID": s.Secim_ID,
            "Secim": s.Secim,
            "Degeri": float(s.Degeri) if s.Degeri is not None else 0.0,
            "Renk_Kodu": s.Renk_Kodu or "#cccccc",
            "Aktif_Pasif": s.Aktif_Pasif,
        }
        for s in secimler_data
    ]

    db_session.close()

    return render_template(
        "puantaj_secim_yonetimi.html",
        user=user,
        subeler=subeler_list,
        secimler=secimler_list,
    )


@web_hr_bp.route("/puantaj-girisi", methods=["GET"])
@login_required
def puantaj_girisi():
    """
    Puantaj Girisi page.
    Shows an interactive grid: employees (rows) x days of period (columns).

    Business rules enforced:
    - Future dates cannot be entered (compared to today)
    - Çıkış selection blocks all subsequent days for that employee
    - Employees whose Sigorta_Cikis is before this period start are excluded
    - Non-admins can only see last 3 periods
    - Non-admins can edit the previous period only within the first 5 days of current month
    """
    import calendar
    import json
    from datetime import datetime as dt, date as date_type

    db_session = get_db_session()
    user = auth_queries.get_kullanici_by_id(db_session, session['user_id'])
    if not user:
        db_session.close()
        return redirect(url_for('web_auth.login'))

    # Admin check
    is_admin = (user.Kullanici_Adi and user.Kullanici_Adi.lower() == 'admin')
    if not is_admin:
        roles = auth_queries.get_user_roles(db_session, user.Kullanici_ID)
        is_admin = 'admin' in [r.lower() for r in roles]

    # Branch list
    all_suber = ref_queries.get_suber(db_session, limit=1000)
    auth_suber = all_suber if is_admin else [
        s for s in all_suber
        if s.Sube_ID in auth_queries.get_user_branches(db_session, user.Kullanici_ID)
    ]
    subeler_list = [{"Sube_ID": s.Sube_ID, "Sube_Adi": s.Sube_Adi} for s in auth_suber]

    sube_id = request.args.get('sube_id', type=int)
    if sube_id is None and auth_suber:
        sube_id = auth_suber[0].Sube_ID

    # Today's date for business rules
    today = dt.now().date()
    current_year  = today.year
    current_month = today.month
    today_day     = today.day
    # Current period code (YYMM)
    current_donem = int(f"{str(current_year)[2:]}{current_month:02d}")

    # Parse period from URL param
    donem_raw = request.args.get('donem', None)
    if not donem_raw:
        donem_raw = session.get('donem', str(current_donem))
    try:
        donem_int = int(donem_raw)
        year  = 2000 + (donem_int // 100)
        month = donem_int % 100
    except (ValueError, TypeError):
        year      = current_year
        month     = current_month
        donem_int = current_donem

    # ── Period access restrictions for non-admin ───────────────────────────
    # Build allowed donem codes: last 3 periods (current + 2 previous)
    def _prev_period(yr, mo, n):
        """Return (year, month) n months before the given (year, month)."""
        mo -= n
        while mo <= 0:
            mo += 12
            yr -= 1
        return yr, mo

    allowed_donems = set()
    yr_tmp, mo_tmp = current_year, current_month
    for i in range(3):
        yr_tmp2, mo_tmp2 = _prev_period(current_year, current_month, i)
        code = int(f"{str(yr_tmp2)[2:]}{mo_tmp2:02d}")
        allowed_donems.add(code)

    if not is_admin and donem_int not in allowed_donems:
        # Redirect to current period if non-admin tries to access older period
        donem_int = current_donem
        year  = current_year
        month = current_month

    # Can the current user edit this period?
    is_current_period  = (year == current_year and month == current_month)
    is_prev_period     = (year == current_year and month == current_month - 1) or \
                         (month == 12 and year == current_year - 1 and current_month == 1)
    # Non-admin can edit previous period only within first 5 days of current month
    can_edit_period = (
        is_admin or
        is_current_period or
        (is_prev_period and today_day <= 5)
    )

    _, num_days = calendar.monthrange(year, month)

    # ── Load puantaj seçim types ───────────────────────────────────────────
    secimler_data = queries.get_puantaj_secimler(db_session, skip=0, limit=1000)
    secimler_map  = {s.Secim_ID: s for s in secimler_data}
    secimler_list = [
        {
            "Secim_ID": s.Secim_ID,
            "Secim":    s.Secim,
            "Degeri":   float(s.Degeri) if s.Degeri else 0.0,
            "Renk_Kodu": s.Renk_Kodu or "#cccccc",
            "Aktif_Pasif": s.Aktif_Pasif,
        }
        for s in secimler_data if s.Aktif_Pasif
    ]

    # Identify the "Çıkış" seçim ID (exact name match, case-insensitive)
    cikis_secim_id = None
    for s in secimler_data:
        if s.Secim and s.Secim.strip().lower() in ('çıkış', 'cikis', 'exit'):
            cikis_secim_id = s.Secim_ID
            break

    # ── Load active employees, filtering by insurance dates ───────────────
    period_start = date_type(year, month, 1)
    _, last = calendar.monthrange(year, month)
    period_end = date_type(year, month, last)

    all_employees = queries.get_calisanlar(db_session, sube_id=sube_id, aktif_pasif=None, limit=1000)

    # Rule 4: Exclude employees whose Sigorta_Cikis is before period start
    employee_data = []
    for emp in all_employees:
        sig_cikis = emp.Sigorta_Cikis
        if sig_cikis and sig_cikis < period_start:
            continue  # Exited before this period; skip
        employee_data.append(emp)

    # ── Load puantaj records for this month/branch ─────────────────────────
    puantaj_records = queries.get_puantajlar_for_month(db_session, sube_id, year, month)

    puantaj_map = {}
    for p in puantaj_records:
        tc   = p.TC_No
        day  = p.Tarih.day
        secim = secimler_map.get(p.Secim_ID)
        if tc not in puantaj_map:
            puantaj_map[tc] = {}
        puantaj_map[tc][day] = {
            "Puantaj_ID": p.Puantaj_ID,
            "Secim_ID":   p.Secim_ID,
            "Secim":      secim.Secim if secim else "?",
            "Renk_Kodu":  secim.Renk_Kodu if secim else "#ccc",
            "Degeri":     float(secim.Degeri) if secim else 0.0,
        }

    # ── Build employee list with totals and çıkış day ─────────────────────
    employees = []
    for emp in employee_data:
        tc       = emp.TC_No
        emp_days = puantaj_map.get(tc, {})
        total    = sum(d["Degeri"] for d in emp_days.values())

        # Find the earliest day that has "Çıkış" for this employee this period
        cikis_day = None
        if cikis_secim_id:
            for d, rec in emp_days.items():
                if rec["Secim_ID"] == cikis_secim_id:
                    cikis_day = d if cikis_day is None else min(cikis_day, d)

        employees.append({
            "TC_No":         tc,
            "Adi":           emp.Adi,
            "Soyadi":        emp.Soyadi,
            "Aktif_Pasif":   emp.Aktif_Pasif,
            "Sigorta_Giris": emp.Sigorta_Giris.isoformat() if emp.Sigorta_Giris else None,
            "Sigorta_Cikis": emp.Sigorta_Cikis.isoformat() if emp.Sigorta_Cikis else None,
            "Total":         round(total, 2),
            "Cikis_Day":     cikis_day,  # day number when Çıkış was entered (or None)
        })

    # ── Donem dropdown options ─────────────────────────────────────────────
    ay_adlari = ["", "Ocak", "Şubat", "Mart", "Nisan", "Mayıs", "Haziran",
                 "Temmuz", "Ağustos", "Eylül", "Ekim", "Kasım", "Aralık"]
    donem_options = []
    # Admin sees last 12 months; non-admin sees last 3
    max_periods = 12 if is_admin else 3
    for i in range(max_periods):
        yr2, mo2 = _prev_period(current_year, current_month, i)
        code = int(f"{str(yr2)[2:]}{mo2:02d}")
        donem_options.append({"code": code, "label": f"{code} - {ay_adlari[mo2]} {yr2}"})

    db_session.close()

    return render_template(
        "puantaj_girisi.html",
        user=user,
        subeler=subeler_list,
        current_sube_id=sube_id,
        employees=employees,
        secimler=secimler_list,
        puantaj_map=json.dumps(puantaj_map),
        year=year,
        month=month,
        num_days=num_days,
        donem=donem_int,
        donem_options=donem_options,
        sube_adi=next((s["Sube_Adi"] for s in subeler_list if s["Sube_ID"] == sube_id), ""),
        today_day=today_day,
        is_current_period=is_current_period,
        is_admin=is_admin,
        can_edit_period=can_edit_period,
        cikis_secim_id=cikis_secim_id or 0,
        cikis_days_json=json.dumps({emp['TC_No']: emp['Cikis_Day'] for emp in employees}),
    )

@web_hr_bp.route("/avans-talepleri", methods=["GET"])
@login_required
def avans_talepleri():
    """
    Avans Talepleri page.
    Shows a list of advance requests with branch and period filters.
    """
    db_session = get_db_session()
    user = auth_queries.get_kullanici_by_id(db_session, session['user_id'])
    if not user:
        db_session.close()
        return redirect(url_for('web_auth.login'))

    # Admin check
    is_admin = (user.Kullanici_Adi and user.Kullanici_Adi.lower() == 'admin')
    if not is_admin:
        roles = auth_queries.get_user_roles(db_session, user.Kullanici_ID)
        is_admin = 'admin' in [r.lower() for r in roles]

    # Branch list
    all_suber = ref_queries.get_suber(db_session, limit=1000)
    auth_suber = all_suber if is_admin else [
        s for s in all_suber
        if s.Sube_ID in auth_queries.get_user_branches(db_session, user.Kullanici_ID)
    ]
    subeler_list = [{"Sube_ID": s.Sube_ID, "Sube_Adi": s.Sube_Adi} for s in auth_suber]

    sube_id = request.args.get('sube_id', type=int)
    if sube_id is None and auth_suber:
        sube_id = auth_suber[0].Sube_ID

    # Period logic
    from datetime import datetime as dt
    today = dt.now().date()
    current_year  = today.year
    current_month = today.month
    current_donem = int(f"{str(current_year)[2:]}{current_month:02d}")

    donem_raw = request.args.get('donem', None)
    if not donem_raw:
        donem_raw = session.get('donem', str(current_donem))
    try:
        donem_int = int(donem_raw)
    except (ValueError, TypeError):
        donem_int = current_donem

    # Get data
    istekler = queries.get_avans_istekler(db_session, sube_id=sube_id, donem=donem_int, limit=1000)
    
    # Get employees for new avans modal - Only active and not exited before today
    employees_data = queries.get_calisanlar(db_session, sube_id=sube_id, limit=1000)
    employees_list = [
        {"TC_No": e.TC_No, "Ad_Soyad": f"{e.Adi} {e.Soyadi}"}
        for e in employees_data 
        if e.Aktif_Pasif and (e.Sigorta_Cikis is None or e.Sigorta_Cikis >= today)
    ]

    # Format list for template
    avans_list = []
    for a in istekler:
        avans_list.append({
            "Avans_ID": a.Avans_ID,
            "Donem": a.Donem,
            "TC_No": a.TC_No,
            "Calisan_Ad_Soyad": f"{a.calisan.Adi} {a.calisan.Soyadi}" if a.calisan else a.TC_No,
            "Tutar": float(a.Tutar),
            "Aciklama": a.Aciklama or "-",
            "Kayit_Tarihi": a.Kayit_Tarihi.strftime("%d.%m.%Y")
        })

    # Period options (last 12 months)
    def _prev_period(yr, mo, n):
        mo -= n
        while mo <= 0:
            mo += 12
            yr -= 1
        return yr, mo

    donem_options = []
    ay_adlari = ["", "Ocak", "Şubat", "Mart", "Nisan", "Mayıs", "Haziran",
                 "Temmuz", "Ağustos", "Eylül", "Ekim", "Kasım", "Aralık"]
    for i in range(12):
        yr2, mo2 = _prev_period(current_year, current_month, i)
        code = int(f"{str(yr2)[2:]}{mo2:02d}")
        donem_options.append({"code": code, "label": f"{code} - {ay_adlari[mo2]} {yr2}"})

    db_session.close()

    return render_template(
        "avans_talepleri.html",
        user=user,
        subeler=subeler_list,
        current_sube_id=sube_id,
        avanslar=avans_list,
        donem=donem_int,
        donem_options=donem_options,
        employees=employees_list,
        sube_adi=next((s["Sube_Adi"] for s in subeler_list if s["Sube_ID"] == sube_id), "")
    )


@web_hr_bp.route("/calisan-talep-yonetimi")
@login_required
def calisan_talep_yonetimi():
    """Çalışan Talep Yönetimi screen."""
    db_session = get_db_session()
    user = auth_queries.get_kullanici_by_id(db_session, session['user_id'])

    # Get filters
    sube_id = request.args.get("sube_id", type=int)
    talep_type = request.args.get("talep", type=str)
    
    # Check permissions
    is_admin = any(r.rol.Rol_Adi == "Admin" for r in user.kullanici_rolleri)
    user_branches = [ub.Sube_ID for ub in user.kullanici_rolleri]
    
    if not is_admin and sube_id and sube_id not in user_branches:
        sube_id = user_branches[0] if user_branches else None

    # Fetch branches
    subeler_data = ref_queries.get_suber(db_session, limit=1000)
    subeler_list = [
        {"Sube_ID": s.Sube_ID, "Sube_Adi": s.Sube_Adi}
        for s in subeler_data
        if is_admin or s.Sube_ID in user_branches
    ]

    if not sube_id and subeler_list:
        sube_id = subeler_list[0]["Sube_ID"]

    # Fetch talepler
    talepler_data = queries.get_calisan_talepler(db_session, sube_id=sube_id, talep=talep_type)
    
    # Prepare list for template
    talepler_list = []
    for t in talepler_data:
        # Determine status based on old program logic
        if t.Talep == 'İşe Giriş':
            if not t.Is_Onay_Veren_Kullanici_ID:
                status = "İşe Giriş Onayı Bekleniyor"
                status_color = "warning"
            elif not t.SSK_Onay_Veren_Kullanici_ID:
                status = "SSK Onayı Bekleniyor"
                status_color = "info"
            else:
                status = "SSK Onaylandı"
                status_color = "success"
        else: # İşten Çıkış
            if not t.SSK_Onay_Veren_Kullanici_ID:
                status = "SSK Onayı Bekleniyor"
                status_color = "info"
            else:
                status = "SSK Onaylandı"
                status_color = "success"
            
        talepler_list.append({
            "ID": t.Calisan_Talep_ID,
            "TC_No": t.TC_No,
            "Ad_Soyad": f"{t.Adi} {t.Soyadi}",
            "Net_Maas": float(t.Net_Maas) if t.Net_Maas else 0.0,
            "Talep_Turu": t.Talep,
            "Tarih": t.Kayit_Tarih.strftime("%d.%m.%Y") if t.Kayit_Tarih else "-",
            "Durum": status,
            "Durum_Color": status_color,
            "HR_Onay": t.Is_Onay_Veren_Kullanici_ID is not None,
            "SSK_Onay": t.SSK_Onay_Veren_Kullanici_ID is not None,
            "Data": { # For edit modal - include ALL fields
                "ID": t.Calisan_Talep_ID,
                "Talep": t.Talep,
                "TC_No": t.TC_No,
                "Adi": t.Adi,
                "Soyadi": t.Soyadi,
                "Ilk_Soyadi": t.Ilk_Soyadi or "",
                "Hesap_No": t.Hesap_No or "",
                "IBAN": t.IBAN or "",
                "Ogrenim_Durumu": t.Ogrenim_Durumu or "",
                "Cinsiyet": t.Cinsiyet,
                "Gorevi": t.Gorevi or "",
                "Anne_Adi": t.Anne_Adi or "",
                "Baba_Adi": t.Baba_Adi or "",
                "Dogum_Yeri": t.Dogum_Yeri or "",
                "Dogum_Tarihi": t.Dogum_Tarihi.isoformat() if t.Dogum_Tarihi else "",
                "Medeni_Hali": t.Medeni_Hali,
                "Cep_No": t.Cep_No or "",
                "Adres_Bilgileri": t.Adres_Bilgileri or "",
                "Gelir_Vergisi_Matrahi": float(t.Gelir_Vergisi_Matrahi) if t.Gelir_Vergisi_Matrahi else 0.0,
                "SSK_Cikis_Nedeni": t.SSK_Cikis_Nedeni or "",
                "Net_Maas": float(t.Net_Maas) if t.Net_Maas else 0.0,
                "Sigorta_Giris": t.Sigorta_Giris.isoformat() if t.Sigorta_Giris else "",
                "Sigorta_Cikis": t.Sigorta_Cikis.isoformat() if t.Sigorta_Cikis else ""
            }
        })

    db_session.close()

    return render_template(
        "calisan_talep_yonetimi.html",
        user=user,
        subeler=subeler_list,
        current_sube_id=sube_id,
        talepler=talepler_list,
        current_talep=talep_type,
        sube_adi=next((s["Sube_Adi"] for s in subeler_list if s["Sube_ID"] == sube_id), "")
    )



