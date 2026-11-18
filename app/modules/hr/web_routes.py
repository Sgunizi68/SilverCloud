"""
HR Web Routes (Server-Rendered)
Pages for HR domain such as Calisan Yonetimi.
"""

import json
from flask import Blueprint, render_template, session, redirect, url_for, request
from app.common.database import get_db_session
from app.common.decorators import login_required, permission_required
from app.modules.hr import queries
from app.modules.auth import queries as auth_queries
from app.modules.reference import queries as ref_queries

web_hr_bp = Blueprint("web_hr", __name__)

@web_hr_bp.route("/calisanlar", methods=["GET"])
@login_required
@permission_required("Çalışan Yönetimi Ekranı Görüntüleme")
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
            "Cihaz_Kaydi": c.Cihaz_Kaydi or "",
            "Aktif_Pasif": c.Aktif_Pasif,
            "Sube_ID": c.Sube_ID
        })
        
    subeler_list = [{"Sube_ID": s.Sube_ID, "Sube_Adi": s.Sube_Adi} for s in auth_suber]
    
    # Permissions
    can_add = is_admin or auth_queries.has_permission(db_session, user.Kullanici_ID, "Yeni Çalışan Ekleme")
    can_edit = is_admin or auth_queries.has_permission(db_session, user.Kullanici_ID, "Çalışan Düzenleme")
    can_view_salary = is_admin or auth_queries.has_permission(db_session, user.Kullanici_ID, "Çalışan Maaş Görme")
    can_delete_cihaz = is_admin or auth_queries.has_permission(db_session, user.Kullanici_ID, "Cihaz Kaydı Sil")
    
    db_session.close()
    
    return render_template(
        "calisanlar.html",
        user=user,
        subeler=subeler_list,
        current_sube_id=sube_id,
        calisanlar=calisanlar_list,
        can_add=can_add,
        can_edit=can_edit,
        can_view_salary=can_view_salary,
        can_delete_cihaz=can_delete_cihaz
    )


@web_hr_bp.route("/puantaj-secim-yonetimi", methods=["GET"])
@login_required
@permission_required("Puantaj Seçim Yönetimi Ekranı Görüntüleme")
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
            "Planli": getattr(s, "Planli", False),
            "Vardiya_Kaydi": getattr(s, "Vardiya_Kaydi", False),
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
@permission_required("Puantaj Girişi Ekranı Görüntüleme")
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
    
    # Check Yetki 7: Puantaj Geçmiş Veri Erişimi
    has_gecmis_yetki = is_admin or auth_queries.has_permission(
        db_session, user.Kullanici_ID, "Puantaj Geçmiş Veri Erişimi"
    )

    # Non-admin / non-gecmis-yetki can edit previous period only within first 5 days of current month
    can_edit_period = (
        is_admin or
        has_gecmis_yetki or
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
        
        # Exclude employees whose start date is after this period
        sig_giris = emp.Sigorta_Giris
        if sig_giris and sig_giris > period_end:
            continue  # Started after this period; skip
            
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
        has_gecmis_yetki=has_gecmis_yetki,
        can_edit_period=can_edit_period,
        cikis_secim_id=cikis_secim_id or 0,
        cikis_days_json=json.dumps({emp['TC_No']: emp['Cikis_Day'] for emp in employees}),
        giris_dates_json=json.dumps({emp['TC_No']: emp['Sigorta_Giris'] for emp in employees}),
        cikis_dates_json=json.dumps({emp['TC_No']: emp['Sigorta_Cikis'] for emp in employees}),
    )


@web_hr_bp.route("/puantaj-kontrol", methods=["GET"])
@login_required
@permission_required("Puantaj Kontrol Ekranı Görüntüleme")
def puantaj_kontrol():
    """
    Puantaj Kontrol Screen (#82).
    Compares Puantaj, Vardiya_Plan, and vardiya_kayit records.
    Displays consistency results with intuitive status symbols (🟢, 🔴, 🟡, ⚪).
    Read-only audit screen.
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

    # Permission #7 check: Puantaj Geçmiş Veri Erişimi
    has_gecmis_yetki = is_admin or auth_queries.has_permission(
        db_session, user.Kullanici_ID, "Puantaj Geçmiş Veri Erişimi"
    )

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

    today = dt.now().date()
    current_year  = today.year
    current_month = today.month
    today_day     = today.day
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

    # Period access restrictions for non-admin without Yetki 7
    def _prev_period(yr, mo, n):
        mo -= n
        while mo <= 0:
            mo += 12
            yr -= 1
        return yr, mo

    allowed_donems = set()
    for i in range(3):
        yr_tmp2, mo_tmp2 = _prev_period(current_year, current_month, i)
        code = int(f"{str(yr_tmp2)[2:]}{mo_tmp2:02d}")
        allowed_donems.add(code)

    if not is_admin and not has_gecmis_yetki and donem_int not in allowed_donems:
        donem_int = current_donem
        year  = current_year
        month = current_month

    is_current_period  = (year == current_year and month == current_month)

    _, num_days = calendar.monthrange(year, month)

    # Load Puantaj Secimleri map
    secimler_data = queries.get_puantaj_secimler(db_session, skip=0, limit=1000)
    secimler_map  = {s.Secim_ID: s for s in secimler_data}

    # Load active employees within period bounds
    period_start = date_type(year, month, 1)
    period_end = date_type(year, month, num_days)

    all_employees = queries.get_calisanlar(db_session, sube_id=sube_id, aktif_pasif=None, limit=1000)
    employee_data = []
    for emp in all_employees:
        if emp.Sigorta_Cikis and emp.Sigorta_Cikis < period_start:
            continue
        if emp.Sigorta_Giris and emp.Sigorta_Giris > period_end:
            continue
        employee_data.append(emp)

    # 1. Puantaj records for the month
    puantaj_records = queries.get_puantajlar_for_month(db_session, sube_id, year, month)
    # 2. Vardiya_Plan records for the month
    vardiya_plan_records = queries.get_vardiya_planlar_for_month(db_session, sube_id, year, month)
    # 3. vardiya_kayit records for the month
    vardiya_kayit_records = queries.get_vardiya_kayitlar_for_month(db_session, sube_id, year, month)

    # Data structures for O(1) day-employee lookup
    p_map = {}
    for p in puantaj_records:
        tc = p.TC_No
        day = p.Tarih.day
        p_map.setdefault(tc, {}).setdefault(day, []).append(p)

    vp_map = {}
    for vp in vardiya_plan_records:
        tc = vp.TC_No
        day = vp.Tarih.day
        vp_map.setdefault(tc, {}).setdefault(day, []).append(vp)

    vk_map = {}
    for vk in vardiya_kayit_records:
        tc = vk.calisan_id
        day = vk.kayit_zamani.day
        day_dict = vk_map.setdefault(tc, {}).setdefault(day, {'girisler': [], 'cikisler': []})
        time_str = vk.kayit_zamani.strftime("%H:%M")
        if vk.islem_tipi == 'GIRIS':
            day_dict['girisler'].append(time_str)
        elif vk.islem_tipi == 'CIKIS':
            day_dict['cikisler'].append(time_str)

    results_map = {}
    total_stats = {'green': 0, 'red': 0, 'yellow': 0, 'gray': 0}

    for emp in employee_data:
        tc = emp.TC_No
        results_map[tc] = {}
        for d in range(1, num_days + 1):
            day_date = date_type(year, month, d)

            is_before_giris = (emp.Sigorta_Giris and day_date < emp.Sigorta_Giris)
            is_after_cikis = (emp.Sigorta_Cikis and day_date > emp.Sigorta_Cikis)
            is_out_of_bounds = is_before_giris or is_after_cikis

            p_list = p_map.get(tc, {}).get(d, [])
            vp_list = vp_map.get(tc, {}).get(d, [])
            vk_info = vk_map.get(tc, {}).get(d, {'girisler': [], 'cikisler': []})

            has_dup_puantaj = len(p_list) > 1
            has_dup_plan = len(vp_list) > 1

            p_rec = p_list[0] if p_list else None
            vp_rec = vp_list[0] if vp_list else None

            p_secim = secimler_map.get(p_rec.Secim_ID) if p_rec else None
            vp_secim = secimler_map.get(vp_rec.Secim_ID) if vp_rec else None

            giris_count = len(vk_info['girisler'])
            cikis_count = len(vk_info['cikisler'])

            differences = []
            status = 'green'

            if is_out_of_bounds:
                if p_rec or vp_rec or giris_count > 0 or cikis_count > 0:
                    status = 'red'
                    reason = "Sigorta giriş öncesi kayıt" if is_before_giris else "Sigorta çıkış sonrası kayıt"
                    differences.append(reason)
                else:
                    status = 'gray'
                    differences.append("Sigorta kapsamı dışı")
            else:
                # 1. Puantaj vs Vardiya Plan
                if p_rec and vp_rec:
                    if p_rec.Secim_ID != vp_rec.Secim_ID:
                        status = 'yellow'
                        differences.append(f"Seçim Farklı (Puantaj: {p_secim.Secim if p_secim else '?'}, Plan: {vp_secim.Secim if vp_secim else '?'})")
                elif p_rec and not vp_rec:
                    if status != 'red':
                        status = 'yellow'
                    differences.append("Vardiya Planı Yok")
                elif not p_rec and vp_rec:
                    status = 'yellow'
                    differences.append("Puantaj Kaydı Yok")
                else:
                    if giris_count > 0 or cikis_count > 0:
                        status = 'red'
                        differences.append("Puantaj ve Plan Yokken Beklenmeyen Vardiya Kaydı")
                    else:
                        status = 'gray'
                        differences.append("Kayıt Yok")

                # Duplicate warnings
                if has_dup_puantaj:
                    status = 'red'
                    differences.append(f"Mükerrer Puantaj Kaydı ({len(p_list)} adet)")
                if has_dup_plan:
                    status = 'red'
                    differences.append(f"Mükerrer Vardiya Planı ({len(vp_list)} adet)")

                # 2. Puantaj vs Vardiya Kaydı
                if p_secim:
                    v_kaydi = getattr(p_secim, 'Vardiya_Kaydi', False)
                    if v_kaydi:
                        if giris_count == 0 and cikis_count == 0:
                            status = 'red'
                            differences.append("Giriş ve Çıkış Kaydı Eksik")
                        elif giris_count > 0 and cikis_count == 0:
                            status = 'red'
                            differences.append("Çıkış Kaydı Eksik")
                        elif giris_count == 0 and cikis_count > 0:
                            status = 'red'
                            differences.append("Giriş Kaydı Eksik")
                    else:
                        if giris_count > 0 or cikis_count > 0:
                            status = 'red'
                            differences.append("Beklenmeyen Vardiya Kaydı (Vardiya kaydı beklenmeyen puantaj seçimi)")

            if not differences:
                differences.append("Tüm kontroller uyumlu")

            total_stats[status] += 1

            results_map[tc][d] = {
                "status": status,
                "puantaj_secim": p_secim.Secim if p_secim else None,
                "puantaj_renk": p_secim.Renk_Kodu if p_secim else "#cbd5e1",
                "vardiya_kaydi_beklenir": getattr(p_secim, 'Vardiya_Kaydi', False) if p_secim else False,
                "plan_secim": vp_secim.Secim if vp_secim else None,
                "plan_renk": vp_secim.Renk_Kodu if vp_secim else "#cbd5e1",
                "girisler": vk_info['girisler'],
                "cikisler": vk_info['cikisler'],
                "differences": differences,
                "is_out_of_bounds": is_out_of_bounds
            }

    employees = [
        {
            "TC_No": emp.TC_No,
            "Adi": emp.Adi,
            "Soyadi": emp.Soyadi,
            "Aktif_Pasif": emp.Aktif_Pasif,
            "Sigorta_Giris": emp.Sigorta_Giris.isoformat() if emp.Sigorta_Giris else None,
            "Sigorta_Cikis": emp.Sigorta_Cikis.isoformat() if emp.Sigorta_Cikis else None,
        }
        for emp in employee_data
    ]

    ay_adlari = ["", "Ocak", "Şubat", "Mart", "Nisan", "Mayıs", "Haziran",
                 "Temmuz", "Ağustos", "Eylül", "Ekim", "Kasım", "Aralık"]
    donem_options = []
    max_periods = 12 if (is_admin or has_gecmis_yetki) else 3
    for i in range(max_periods):
        yr2, mo2 = _prev_period(current_year, current_month, i)
        code = int(f"{str(yr2)[2:]}{mo2:02d}")
        donem_options.append({"code": code, "label": f"{code} - {ay_adlari[mo2]} {yr2}"})

    db_session.close()

    return render_template(
        "puantaj_kontrol.html",
        user=user,
        subeler=subeler_list,
        current_sube_id=sube_id,
        employees=employees,
        results_map=json.dumps(results_map),
        year=year,
        month=month,
        num_days=num_days,
        donem=donem_int,
        donem_options=donem_options,
        sube_adi=next((s["Sube_Adi"] for s in subeler_list if s["Sube_ID"] == sube_id), ""),
        today_day=today_day,
        is_current_period=is_current_period,
        is_admin=is_admin,
        has_gecmis_yetki=has_gecmis_yetki,
        total_stats=total_stats
    )


@web_hr_bp.route("/avans-talepleri", methods=["GET"])
@login_required
@permission_required("Avans Talebi Ekranı Görüntüleme")
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
        is_current_donem=(donem_int == current_donem),
        sube_adi=next((s["Sube_Adi"] for s in subeler_list if s["Sube_ID"] == sube_id), "")
    )


@web_hr_bp.route("/calisan-talep-yonetimi")
@login_required
@permission_required("Çalışan Talep Ekranı Görüntüleme")
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


@web_hr_bp.route("/vardiya-plan-girisi", methods=["GET"])
@login_required
@permission_required("Vardiya Planı Girişi Ekranı Görüntüleme")
def vardiya_plan_girisi():
    """
    Vardiya Plan Girisi page.
    Shows an interactive grid: employees (rows) x days of period (columns).
    Mirrors the puantaj_girisi workflow using Vardiya_Plan table.

    Business rules enforced:
    - Admin or users with 'Vardiya Plan Geçmiş Veri Erişimi' (Yetki ID 79) have full access to historical periods.
    - Non-authorized users can only see the last 3 periods and edit current period (or previous within first 5 days).
    - Future dates cannot be entered for non-authorized users.
    - Employees whose Sigorta_Cikis is before this period start are excluded.
    - Dates before Sigorta_Giris or after Sigorta_Cikis are locked.
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

    # Yetki 79: Vardiya Plan Geçmiş Veri Erişimi check
    has_gecmis_yetki = is_admin or auth_queries.has_permission(
        db_session, user.Kullanici_ID, "Vardiya Plan Geçmiş Veri Erişimi"
    )

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

    # Period access helper functions
    def _prev_period(yr, mo, n):
        mo -= n
        while mo <= 0:
            mo += 12
            yr -= 1
        return yr, mo

    def _next_period(yr, mo, n):
        mo += n
        while mo > 12:
            mo -= 12
            yr += 1
        return yr, mo

    # Calculate next period (current period + 1 month)
    next_yr, next_mo = _next_period(current_year, current_month, 1)
    next_donem = int(f"{str(next_yr)[2:]}{next_mo:02d}")

    allowed_donems = set()
    # Next period is allowed for planning
    allowed_donems.add(next_donem)
    # Current period and previous periods: non-gecmis user gets current + 2 previous
    for i in range(3):
        yr_tmp2, mo_tmp2 = _prev_period(current_year, current_month, i)
        code = int(f"{str(yr_tmp2)[2:]}{mo_tmp2:02d}")
        allowed_donems.add(code)

    if not has_gecmis_yetki and donem_int not in allowed_donems:
        # Redirect to current period if user lacks past data permission
        donem_int = current_donem
        year  = current_year
        month = current_month

    is_current_period  = (year == current_year and month == current_month)
    is_next_period     = (year == next_yr and month == next_mo)

    # In Vardiya Plan, non-yetki 79 users can edit from tomorrow onwards (including next period)
    # can_edit_period is True if user has gecmis yetki, or if period has dates after today.
    can_edit_period = has_gecmis_yetki or (date_type(year, month, calendar.monthrange(year, month)[1]) > today)

    _, num_days = calendar.monthrange(year, month)

    # Load vardiya/puantaj seçim types from Puantaj_Secimi
    secimler_data = queries.get_puantaj_secimler(db_session, skip=0, limit=1000)
    secimler_map  = {s.Secim_ID: s for s in secimler_data}
    secimler_list = [
        {
            "Secim_ID": s.Secim_ID,
            "Secim":    s.Secim,
            "Degeri":   float(s.Degeri) if s.Degeri else 0.0,
            "Renk_Kodu": s.Renk_Kodu or "#cccccc",
            "Aktif_Pasif": s.Aktif_Pasif,
            "Planli": getattr(s, "Planli", False),
        }
        for s in secimler_data if s.Aktif_Pasif and getattr(s, "Planli", False)
    ]

    # Identify "Çıkış" seçim ID
    cikis_secim_id = None
    for s in secimler_data:
        if s.Secim and s.Secim.strip().lower() in ('çıkış', 'cikis', 'exit'):
            cikis_secim_id = s.Secim_ID
            break

    # Load active employees for this period
    period_start = date_type(year, month, 1)
    _, last = calendar.monthrange(year, month)
    period_end = date_type(year, month, last)

    all_employees = queries.get_calisanlar(db_session, sube_id=sube_id, aktif_pasif=None, limit=1000)

    employee_data = []
    for emp in all_employees:
        sig_cikis = emp.Sigorta_Cikis
        if sig_cikis and sig_cikis < period_start:
            continue
        sig_giris = emp.Sigorta_Giris
        if sig_giris and sig_giris > period_end:
            continue
        employee_data.append(emp)

    # Load vardiya plan records for this month/branch
    vardiya_records = queries.get_vardiya_planlar_for_month(db_session, sube_id, year, month)

    vardiya_map = {}
    for v in vardiya_records:
        tc = v.TC_No
        day = v.Tarih.day
        secim = secimler_map.get(v.Secim_ID)
        if tc not in vardiya_map:
            vardiya_map[tc] = {}
        vardiya_map[tc][day] = {
            "Vardiya_Plan_ID": v.Vardiya_Plan_ID,
            "Secim_ID":        v.Secim_ID,
            "Secim":           secim.Secim if secim else "?",
            "Renk_Kodu":       secim.Renk_Kodu if secim else "#ccc",
            "Degeri":          float(secim.Degeri) if secim else 0.0,
        }

    # Build employee list with totals and çıkış day
    employees = []
    for emp in employee_data:
        tc = emp.TC_No
        emp_days = vardiya_map.get(tc, {})
        total = sum(d["Degeri"] for d in emp_days.values())

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
            "Cikis_Day":     cikis_day,
        })

    # Donem dropdown options
    ay_adlari = ["", "Ocak", "Şubat", "Mart", "Nisan", "Mayıs", "Haziran",
                 "Temmuz", "Ağustos", "Eylül", "Ekim", "Kasım", "Aralık"]
    donem_options = []
    
    # 1. Add next period (gecelek dönem)
    donem_options.append({"code": next_donem, "label": f"{next_donem} - {ay_adlari[next_mo]} {next_yr}"})

    # 2. Add current period and past periods
    max_periods = 12 if has_gecmis_yetki else 3
    for i in range(max_periods):
        yr2, mo2 = _prev_period(current_year, current_month, i)
        code = int(f"{str(yr2)[2:]}{mo2:02d}")
        donem_options.append({"code": code, "label": f"{code} - {ay_adlari[mo2]} {yr2}"})

    db_session.close()

    return render_template(
        "vardiya_plan_girisi.html",
        user=user,
        subeler=subeler_list,
        current_sube_id=sube_id,
        employees=employees,
        secimler=secimler_list,
        vardiya_map=json.dumps(vardiya_map),
        year=year,
        month=month,
        num_days=num_days,
        donem=donem_int,
        donem_options=donem_options,
        sube_adi=next((s["Sube_Adi"] for s in subeler_list if s["Sube_ID"] == sube_id), ""),
        today_date_str=today.isoformat(),
        today_day=today_day,
        is_current_period=is_current_period,
        is_next_period=is_next_period,
        is_admin=is_admin,
        has_gecmis_yetki=has_gecmis_yetki,
        can_edit_period=can_edit_period,
        cikis_secim_id=cikis_secim_id or 0,
        cikis_days_json=json.dumps({emp['TC_No']: emp['Cikis_Day'] for emp in employees}),
        giris_dates_json=json.dumps({emp['TC_No']: emp['Sigorta_Giris'] for emp in employees}),
        cikis_dates_json=json.dumps({emp['TC_No']: emp['Sigorta_Cikis'] for emp in employees}),
    )


# ============================================================================
# MOBIL ROSTER (GİRİŞ / ÇIKIŞ) WEB ROUTES
# ============================================================================

@web_hr_bp.route("/Vardiya", methods=["GET"])
def vardiya_mobil():
    """
    Public mobile shift check-in/out page.
    No login required. Works with QR token param: /Vardiya?kod=...
    """
    token = request.args.get("kod", "").strip()
    return render_template("vardiya_mobil.html", token=token)


@web_hr_bp.route("/barkod", methods=["GET"])
@login_required
@permission_required("Barkod Ekranı Görüntüleme")
def barkod_yonetimi():
    """
    Barkod Yönetimi Screen (#75).
    Allows creating, viewing, and printing QR codes for branches.
    """
    db_session = get_db_session()
    user = auth_queries.get_kullanici_by_id(db_session, session['user_id'])
    if not user:
        db_session.close()
        return redirect(url_for('web_auth.login'))

    is_admin = False
    if user.Kullanici_Adi and user.Kullanici_Adi.lower() == 'admin':
        is_admin = True
    else:
        roles = auth_queries.get_user_roles(db_session, user.Kullanici_ID)
        if 'admin' in [r.lower() for r in roles]:
            is_admin = True

    all_suber = ref_queries.get_suber(db_session, limit=1000)
    if is_admin:
        auth_suber = all_suber
    else:
        authorized_branch_ids = auth_queries.get_user_branches(db_session, user.Kullanici_ID)
        auth_suber = [s for s in all_suber if s.Sube_ID in authorized_branch_ids]

    selected_sube_id = request.args.get('sube_id', type=int)
    if not selected_sube_id and auth_suber:
        selected_sube_id = auth_suber[0].Sube_ID

    sube_list = [{"Sube_ID": s.Sube_ID, "Sube_Adi": s.Sube_Adi, "merkez_enlem": float(s.merkez_enlem) if s.merkez_enlem else None, "merkez_boylam": float(s.merkez_boylam) if s.merkez_boylam else None, "yaricap_m": s.yaricap_m} for s in auth_suber]

    db_session.close()
    return render_template(
        "barkod_yonetimi.html",
        user=user,
        subeler=sube_list,
        selected_sube_id=selected_sube_id,
        is_admin=is_admin
    )


@web_hr_bp.route("/vardiya-cizelgesi", methods=["GET"])
@login_required
@permission_required("Vardiya Çizelgesi Ekranı Görüntüleme")
def vardiya_cizelgesi():
    """
    Vardiya Çizelgesi Screen (#76).
    Displays shift records with filters, pagination, manual creation/update (#77),
    Excel export (#33), Print (#34), and Mail (#74).
    """
    db_session = get_db_session()
    user = auth_queries.get_kullanici_by_id(db_session, session['user_id'])
    if not user:
        db_session.close()
        return redirect(url_for('web_auth.login'))

    is_admin = False
    if user.Kullanici_Adi and user.Kullanici_Adi.lower() == 'admin':
        is_admin = True
    else:
        roles = auth_queries.get_user_roles(db_session, user.Kullanici_ID)
        if 'admin' in [r.lower() for r in roles]:
            is_admin = True

    can_update = is_admin or auth_queries.has_permission(db_session, user.Kullanici_ID, "Vardiya Güncelleme Yetkisi")
    can_excel = is_admin or auth_queries.has_permission(db_session, user.Kullanici_ID, "Excele Aktar")
    can_print = is_admin or auth_queries.has_permission(db_session, user.Kullanici_ID, "Yazdırma Yetkisi")
    can_mail = is_admin or auth_queries.has_permission(db_session, user.Kullanici_ID, "Mail Gönder")

    all_suber = ref_queries.get_suber(db_session, limit=1000)
    if is_admin:
        auth_suber = all_suber
    else:
        authorized_branch_ids = auth_queries.get_user_branches(db_session, user.Kullanici_ID)
        auth_suber = [s for s in all_suber if s.Sube_ID in authorized_branch_ids]

    sube_list = [{"Sube_ID": s.Sube_ID, "Sube_Adi": s.Sube_Adi} for s in auth_suber]

    # Active employees list for manual entry modal and filter dropdown (Sorted alphabetically by Adi, Soyadi)
    active_employees = queries.get_calisanlar(db_session, limit=2000, aktif_pasif=True)
    emp_list = [{"TC_No": e.TC_No, "Adi": e.Adi, "Soyadi": e.Soyadi, "Sube_ID": e.Sube_ID} for e in active_employees]
    
    # Turkish-aware lowercase helper for accurate sorting
    tr_map = str.maketrans("İIŞĞÜÖÇ", "ıisguoc")
    def tr_sort_key(emp):
        full_name = f"{emp.get('Adi', '')} {emp.get('Soyadi', '')}".translate(tr_map).lower()
        return full_name

    emp_list.sort(key=tr_sort_key)

    db_session.close()
    return render_template(
        "vardiya_cizelgesi.html",
        user=user,
        subeler=sube_list,
        employees=emp_list,
        can_update=can_update,
        can_excel=can_excel,
        can_print=can_print,
        can_mail=can_mail,
        is_admin=is_admin
    )


@web_hr_bp.route("/vardiya-kayit-log-raporu", methods=["GET"])
@login_required
@permission_required("Vardiya Kayit Log Raporu Görüntüleme")
def vardiya_kayit_log_raporu():
    """
    Vardiya Kayıt Log Raporu Screen (#81).
    Displays audit log of shift records with filtering, pagination,
    Excel export (#33), Print (#34), and Mail (#74).
    """
    db_session = get_db_session()
    user = auth_queries.get_kullanici_by_id(db_session, session['user_id'])
    if not user:
        db_session.close()
        return redirect(url_for('web_auth.login'))

    is_admin = False
    if user.Kullanici_Adi.lower() == 'admin':
        is_admin = True
    else:
        roles = auth_queries.get_user_roles(db_session, user.Kullanici_ID)
        is_admin = 'admin' in [r.lower() for r in roles]

    can_excel = is_admin or auth_queries.has_permission(db_session, user.Kullanici_ID, "Excel'e Aktarma")
    can_print = is_admin or auth_queries.has_permission(db_session, user.Kullanici_ID, "Yazdırma Yetkisi")
    can_mail = is_admin or auth_queries.has_permission(db_session, user.Kullanici_ID, "Mail Gönder")

    # Get user list for filter dropdown (sorted alphabetically by Adi_Soyadi)
    from app.models import Kullanici
    all_users = db_session.query(Kullanici).filter(Kullanici.Aktif_Pasif == True).all()
    user_list = [
        {
            "Kullanici_ID": u.Kullanici_ID,
            "Kullanici_Adi": u.Adi_Soyadi if u.Adi_Soyadi else u.Kullanici_Adi
        }
        for u in all_users
    ]
    
    tr_map = str.maketrans("İIŞĞÜÖÇ", "ıisguoc")
    user_list.sort(key=lambda x: (x["Kullanici_Adi"] or "").translate(tr_map).lower())

    db_session.close()
    return render_template(
        "vardiya_kayit_log_raporu.html",
        user=user,
        kullanicilar=user_list,
        can_excel=can_excel,
        can_print=can_print,
        can_mail=can_mail,
        is_admin=is_admin
    )




