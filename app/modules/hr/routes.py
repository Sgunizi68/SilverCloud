"""
HR Domain Routes
CRUD endpoints for Employee, Attendance, and Leave/Advance management.
All endpoints protected by @auth_required decorator.
"""

import math
from datetime import datetime, date
from functools import wraps
from flask import Blueprint, request, jsonify, session
from app.common.database import get_db_session
from app.modules.hr import queries

hr_bp = Blueprint("hr", __name__, url_prefix="/api/v1")

# Late-binding auth_required to avoid circular import
def auth_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        from app.modules.auth.routes import auth_required as _auth_required
        return _auth_required(f)(*args, **kwargs)
    return decorated


# ============================================================================
# CALISAN (EMPLOYEE) ENDPOINTS
# ============================================================================

@hr_bp.route("/calisanlar", methods=["GET"])
@auth_required
def list_calisanlar():
    """Get all employees with optional filtering."""
    try:
        skip = request.args.get("skip", 0, type=int)
        limit = min(request.args.get("limit", 100, type=int), 1000)
        sube_id = request.args.get("sube_id", None, type=int)
        aktif_pasif = request.args.get("aktif_pasif", None)
        if aktif_pasif is not None:
            aktif_pasif = aktif_pasif.lower() == "true"
        
        db = get_db_session()
        calisanlar = queries.get_calisanlar(db, skip, limit, sube_id, aktif_pasif)
        db.close()
        
        result = [
            {
                "TC_No": c.TC_No,
                "Adi": c.Adi,
                "Soyadi": c.Soyadi,
                "Hesap_No": c.Hesap_No,
                "IBAN": c.IBAN,
                "Net_Maas": float(c.Net_Maas) if c.Net_Maas else None,
                "Sigorta_Giris": c.Sigorta_Giris.isoformat() if c.Sigorta_Giris else None,
                "Sigorta_Cikis": c.Sigorta_Cikis.isoformat() if c.Sigorta_Cikis else None,
                "Cihaz_Kaydi": c.Cihaz_Kaydi,
                "Aktif_Pasif": c.Aktif_Pasif,
                "Sube_ID": c.Sube_ID,
            }
            for c in calisanlar
        ]
        
        return jsonify(result), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@hr_bp.route("/calisanlar/<tc_no>", methods=["GET"])
@auth_required
def get_calisan(tc_no):
    """Get employee by TC ID."""
    try:
        db = get_db_session()
        calisan = queries.get_calisan_by_tc_no(db, tc_no)
        db.close()
        
        if not calisan:
            return jsonify({"error": "Calisan not found"}), 404
        
        result = {
            "TC_No": calisan.TC_No,
            "Adi": calisan.Adi,
            "Soyadi": calisan.Soyadi,
            "Hesap_No": calisan.Hesap_No,
            "IBAN": calisan.IBAN,
            "Net_Maas": float(calisan.Net_Maas) if calisan.Net_Maas else None,
            "Sigorta_Giris": calisan.Sigorta_Giris.isoformat() if calisan.Sigorta_Giris else None,
            "Sigorta_Cikis": calisan.Sigorta_Cikis.isoformat() if calisan.Sigorta_Cikis else None,
            "Cihaz_Kaydi": calisan.Cihaz_Kaydi,
            "Aktif_Pasif": calisan.Aktif_Pasif,
            "Sube_ID": calisan.Sube_ID,
        }
        
        return jsonify(result), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@hr_bp.route("/calisanlar", methods=["POST"])
@auth_required
def create_calisan():
    """Create a new employee."""
    try:
        data = request.get_json()
        if not data or "TC_No" not in data or "Adi" not in data or "Soyadi" not in data or "Sube_ID" not in data:
            return jsonify({"error": "TC_No, Adi, Soyadi, and Sube_ID required"}), 400
        
        db = get_db_session()
        new_calisan = queries.create_calisan(
            db,
            tc_no=data["TC_No"],
            adi=data["Adi"],
            soyadi=data["Soyadi"],
            sube_id=data["Sube_ID"],
            hesap_no=data.get("Hesap_No"),
            iban=data.get("IBAN"),
            net_maas=float(data.get("Net_Maas")) if data.get("Net_Maas") not in (None, "") else None,
            sigorta_giris=data.get("Sigorta_Giris"),
            sigorta_cikis=data.get("Sigorta_Cikis"),
            cihaz_kaydi=data.get("Cihaz_Kaydi"),
            aktif_pasif=data.get("Aktif_Pasif", True)
        )
        db.close()
        
        result = {
            "TC_No": new_calisan.TC_No,
            "Adi": new_calisan.Adi,
            "Soyadi": new_calisan.Soyadi,
            "Hesap_No": new_calisan.Hesap_No,
            "IBAN": new_calisan.IBAN,
            "Net_Maas": float(new_calisan.Net_Maas) if new_calisan.Net_Maas else None,
            "Sigorta_Giris": new_calisan.Sigorta_Giris.isoformat() if new_calisan.Sigorta_Giris else None,
            "Sigorta_Cikis": new_calisan.Sigorta_Cikis.isoformat() if new_calisan.Sigorta_Cikis else None,
            "Cihaz_Kaydi": new_calisan.Cihaz_Kaydi,
            "Aktif_Pasif": new_calisan.Aktif_Pasif,
            "Sube_ID": new_calisan.Sube_ID,
        }
        
        return jsonify(result), 201
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@hr_bp.route("/calisanlar/<tc_no>", methods=["PUT"])
@auth_required
def update_calisan(tc_no):
    """Update employee."""
    try:
        data = request.get_json()
        
        db = get_db_session()
        updated_calisan = queries.update_calisan(
            db,
            tc_no,
            adi=data.get("Adi"),
            soyadi=data.get("Soyadi"),
            hesap_no=data.get("Hesap_No"),
            iban=data.get("IBAN"),
            net_maas=data.get("Net_Maas"),
            sigorta_giris=data.get("Sigorta_Giris"),
            sigorta_cikis=data.get("Sigorta_Cikis"),
            cihaz_kaydi=data.get("Cihaz_Kaydi"),
            aktif_pasif=data.get("Aktif_Pasif"),
            sube_id=data.get("Sube_ID")
        )
        db.close()
        
        if not updated_calisan:
            return jsonify({"error": "Calisan not found"}), 404
        
        result = {
            "TC_No": updated_calisan.TC_No,
            "Adi": updated_calisan.Adi,
            "Soyadi": updated_calisan.Soyadi,
            "Hesap_No": updated_calisan.Hesap_No,
            "IBAN": updated_calisan.IBAN,
            "Net_Maas": float(updated_calisan.Net_Maas) if updated_calisan.Net_Maas else None,
            "Sigorta_Giris": updated_calisan.Sigorta_Giris.isoformat() if updated_calisan.Sigorta_Giris else None,
            "Sigorta_Cikis": updated_calisan.Sigorta_Cikis.isoformat() if updated_calisan.Sigorta_Cikis else None,
            "Cihaz_Kaydi": updated_calisan.Cihaz_Kaydi,
            "Aktif_Pasif": updated_calisan.Aktif_Pasif,
            "Sube_ID": updated_calisan.Sube_ID,
        }
        
        return jsonify(result), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@hr_bp.route("/calisanlar/<tc_no>", methods=["DELETE"])
@auth_required
def delete_calisan(tc_no):
    """Delete employee."""
    try:
        db = get_db_session()
        deleted = queries.delete_calisan(db, tc_no)
        db.close()
        
        if not deleted:
            return jsonify({"error": "Calisan not found"}), 404
        
        return jsonify({"message": "Calisan deleted"}), 204
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@hr_bp.route("/calisanlar/<tc_no>/cihaz-kaydi", methods=["DELETE"])
@auth_required
def delete_calisan_cihaz_kaydi(tc_no):
    """Clear employee device registration (Cihaz Kaydı Sil - Yetki 80)."""
    try:
        from app.modules.auth import queries as auth_queries
        user_id = session.get('user_id')
        db = get_db_session()
        
        user = auth_queries.get_kullanici_by_id(db, user_id) if user_id else None
        is_admin = False
        if user:
            if user.Kullanici_Adi and user.Kullanici_Adi.lower() == 'admin':
                is_admin = True
            else:
                roles = auth_queries.get_user_roles(db, user.Kullanici_ID)
                is_admin = 'admin' in [r.lower() for r in roles]

        can_delete_cihaz = is_admin or (user and auth_queries.has_permission(db, user.Kullanici_ID, "Cihaz Kaydı Sil"))
        if not can_delete_cihaz:
            db.close()
            return jsonify({"error": "Cihaz kaydı silme yetkiniz bulunmamaktadır."}), 403

        updated_calisan = queries.update_calisan(db, tc_no, cihaz_kaydi="")
        db.close()

        if not updated_calisan:
            return jsonify({"error": "Calisan not found"}), 404

        return jsonify({
            "message": "Cihaz kaydı başarıyla silindi.",
            "TC_No": updated_calisan.TC_No,
            "Cihaz_Kaydi": updated_calisan.Cihaz_Kaydi
        }), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# ============================================================================
# PUANTAJ SECIMI (ATTENDANCE TYPE) ENDPOINTS
# ============================================================================

@hr_bp.route("/puantaj-secimler", methods=["GET"])
@auth_required
def list_puantaj_secimler():
    """Get all attendance types."""
    try:
        skip = request.args.get("skip", 0, type=int)
        limit = min(request.args.get("limit", 100, type=int), 1000)
        aktif_pasif = request.args.get("aktif_pasif", None)
        if aktif_pasif is not None:
            aktif_pasif = aktif_pasif.lower() == "true"
        
        db = get_db_session()
        secimler = queries.get_puantaj_secimler(db, skip, limit, aktif_pasif)
        db.close()
        
        result = [
            {
                "Secim_ID": s.Secim_ID,
                "Secim": s.Secim,
                "Degeri": float(s.Degeri),
                "Renk_Kodu": s.Renk_Kodu,
                "Aktif_Pasif": s.Aktif_Pasif,
                "Planli": getattr(s, "Planli", False),
            }
            for s in secimler
        ]
        
        return jsonify(result), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@hr_bp.route("/puantaj-secimler/<int:secim_id>", methods=["GET"])
@auth_required
def get_puantaj_secim(secim_id):
    """Get attendance type by ID."""
    try:
        db = get_db_session()
        secim = queries.get_puantaj_secim_by_id(db, secim_id)
        db.close()
        
        if not secim:
            return jsonify({"error": "PuantajSecimi not found"}), 404
        
        result = {
            "Secim_ID": secim.Secim_ID,
            "Secim": secim.Secim,
            "Degeri": float(secim.Degeri),
            "Renk_Kodu": secim.Renk_Kodu,
            "Aktif_Pasif": secim.Aktif_Pasif,
            "Planli": getattr(secim, "Planli", False),
        }
        
        return jsonify(result), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@hr_bp.route("/puantaj-secimler", methods=["POST"])
@auth_required
def create_puantaj_secim():
    """Create a new attendance type."""
    try:
        data = request.get_json()
        if not data or "Secim" not in data or "Degeri" not in data or "Renk_Kodu" not in data:
            return jsonify({"error": "Secim, Degeri, and Renk_Kodu required"}), 400
        
        db = get_db_session()
        new_secim = queries.create_puantaj_secim(
            db,
            secim=data["Secim"],
            degeri=float(data["Degeri"]),
            renk_kodu=data["Renk_Kodu"],
            aktif_pasif=data.get("Aktif_Pasif", True),
            planli=bool(data.get("Planli", False))
        )
        db.close()
        
        result = {
            "Secim_ID": new_secim.Secim_ID,
            "Secim": new_secim.Secim,
            "Degeri": float(new_secim.Degeri),
            "Renk_Kodu": new_secim.Renk_Kodu,
            "Aktif_Pasif": new_secim.Aktif_Pasif,
            "Planli": getattr(new_secim, "Planli", False),
        }
        
        return jsonify(result), 201
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@hr_bp.route("/puantaj-secimler/<int:secim_id>", methods=["PUT"])
@auth_required
def update_puantaj_secim(secim_id):
    """Update attendance type."""
    try:
        data = request.get_json()
        
        db = get_db_session()
        updated_secim = queries.update_puantaj_secim(
            db,
            secim_id,
            secim=data.get("Secim"),
            degeri=float(data.get("Degeri")) if "Degeri" in data else None,
            renk_kodu=data.get("Renk_Kodu"),
            aktif_pasif=data.get("Aktif_Pasif"),
            planli=bool(data.get("Planli")) if "Planli" in data else None
        )
        db.close()
        
        if not updated_secim:
            return jsonify({"error": "PuantajSecimi not found"}), 404
        
        result = {
            "Secim_ID": updated_secim.Secim_ID,
            "Secim": updated_secim.Secim,
            "Degeri": float(updated_secim.Degeri),
            "Renk_Kodu": updated_secim.Renk_Kodu,
            "Aktif_Pasif": updated_secim.Aktif_Pasif,
            "Planli": getattr(updated_secim, "Planli", False),
        }
        
        return jsonify(result), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@hr_bp.route("/puantaj-secimler/<int:secim_id>", methods=["DELETE"])
@auth_required
def delete_puantaj_secim(secim_id):
    """Delete attendance type."""
    try:
        db = get_db_session()
        deleted = queries.delete_puantaj_secim(db, secim_id)
        db.close()
        
        if not deleted:
            return jsonify({"error": "PuantajSecimi not found"}), 404
        
        return jsonify({"message": "PuantajSecimi deleted"}), 204
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# ============================================================================
# PUANTAJ (ATTENDANCE) ENDPOINTS
# ============================================================================

@hr_bp.route("/puantajlar", methods=["GET"])
@auth_required
def list_puantajlar():
    """Get all attendance records with optional filtering."""
    try:
        skip = request.args.get("skip", 0, type=int)
        limit = min(request.args.get("limit", 100, type=int), 1000)
        tc_no = request.args.get("tc_no", None, type=str)
        sube_id = request.args.get("sube_id", None, type=int)
        secim_id = request.args.get("secim_id", None, type=int)
        
        db = get_db_session()
        puantajlar = queries.get_puantajlar(db, skip, limit, tc_no, sube_id, secim_id)
        db.close()
        
        result = [
            {
                "Puantaj_ID": p.Puantaj_ID,
                "Tarih": p.Tarih.isoformat(),
                "TC_No": p.TC_No,
                "Secim_ID": p.Secim_ID,
                "Sube_ID": p.Sube_ID,
                "Kayit_Tarihi": p.Kayit_Tarihi.isoformat(),
            }
            for p in puantajlar
        ]
        
        return jsonify(result), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@hr_bp.route("/puantajlar/<int:puantaj_id>", methods=["GET"])
@auth_required
def get_puantaj(puantaj_id):
    """Get attendance record by ID."""
    try:
        db = get_db_session()
        puantaj = queries.get_puantaj_by_id(db, puantaj_id)
        db.close()
        
        if not puantaj:
            return jsonify({"error": "Puantaj not found"}), 404
        
        result = {
            "Puantaj_ID": puantaj.Puantaj_ID,
            "Tarih": puantaj.Tarih.isoformat(),
            "TC_No": puantaj.TC_No,
            "Secim_ID": puantaj.Secim_ID,
            "Sube_ID": puantaj.Sube_ID,
            "Kayit_Tarihi": puantaj.Kayit_Tarihi.isoformat(),
        }
        
        return jsonify(result), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@hr_bp.route("/puantajlar", methods=["POST"])
@auth_required
def create_puantaj():
    """Create a new attendance record."""
    try:
        data = request.get_json()
        if not data or "TC_No" not in data or "Secim_ID" not in data or "Sube_ID" not in data:
            return jsonify({"error": "TC_No, Secim_ID, and Sube_ID required"}), 400
        
        db = get_db_session()
        
        # Validation: Date cannot be before Sigorta_Giris or after Sigorta_Cikis
        from datetime import date as date_type
        target_date = data.get("Tarih")
        if isinstance(target_date, str):
            target_date = date_type.fromisoformat(target_date)
        
        calisan = queries.get_calisan_by_tc_no(db, data["TC_No"])
        if calisan:
            if calisan.Sigorta_Giris and target_date < calisan.Sigorta_Giris:
                db.close()
                return jsonify({"error": f"Sigorta giriş tarihinden ({calisan.Sigorta_Giris.strftime('%d.%m.%Y')}) öncesine veri girişi yapılamaz."}), 403
            if calisan.Sigorta_Cikis and target_date > calisan.Sigorta_Cikis:
                db.close()
                return jsonify({"error": f"Sigorta çıkış tarihinden ({calisan.Sigorta_Cikis.strftime('%d.%m.%Y')}) sonrasına veri girişi yapılamaz."}), 403

        new_puantaj = queries.create_puantaj(
            db,
            tc_no=data["TC_No"],
            secim_id=data["Secim_ID"],
            sube_id=data["Sube_ID"],
            tarih=data.get("Tarih"),
            kayit_tarihi=data.get("Kayit_Tarihi")
        )
        db.close()
        
        result = {
            "Puantaj_ID": new_puantaj.Puantaj_ID,
            "Tarih": new_puantaj.Tarih.isoformat(),
            "TC_No": new_puantaj.TC_No,
            "Secim_ID": new_puantaj.Secim_ID,
            "Sube_ID": new_puantaj.Sube_ID,
            "Kayit_Tarihi": new_puantaj.Kayit_Tarihi.isoformat(),
        }
        
        return jsonify(result), 201
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@hr_bp.route("/puantajlar/<int:puantaj_id>", methods=["PUT"])
@auth_required
def update_puantaj(puantaj_id):
    """Update attendance record."""
    try:
        data = request.get_json()
        
        db = get_db_session()
        
        # Validation: Date cannot be before Sigorta_Giris or after Sigorta_Cikis
        puantaj = queries.get_puantaj_by_id(db, puantaj_id)
        if puantaj:
            from datetime import date as date_type
            target_date = data.get("Tarih")
            if target_date:
                if isinstance(target_date, str):
                    target_date = date_type.fromisoformat(target_date)
            else:
                target_date = puantaj.Tarih
            
            calisan = queries.get_calisan_by_tc_no(db, puantaj.TC_No)
            if calisan:
                if calisan.Sigorta_Giris and target_date < calisan.Sigorta_Giris:
                    db.close()
                    return jsonify({"error": f"Sigorta giriş tarihinden ({calisan.Sigorta_Giris.strftime('%d.%m.%Y')}) öncesine veri girişi yapılamaz."}), 403
                if calisan.Sigorta_Cikis and target_date > calisan.Sigorta_Cikis:
                    db.close()
                    return jsonify({"error": f"Sigorta çıkış tarihinden ({calisan.Sigorta_Cikis.strftime('%d.%m.%Y')}) sonrasına veri girişi yapılamaz."}), 403

        updated_puantaj = queries.update_puantaj(
            db,
            puantaj_id,
            secim_id=data.get("Secim_ID"),
            tarih=data.get("Tarih")
        )
        db.close()
        
        if not updated_puantaj:
            return jsonify({"error": "Puantaj not found"}), 404
        
        result = {
            "Puantaj_ID": updated_puantaj.Puantaj_ID,
            "Tarih": updated_puantaj.Tarih.isoformat(),
            "TC_No": updated_puantaj.TC_No,
            "Secim_ID": updated_puantaj.Secim_ID,
            "Sube_ID": updated_puantaj.Sube_ID,
            "Kayit_Tarihi": updated_puantaj.Kayit_Tarihi.isoformat(),
        }
        
        return jsonify(result), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@hr_bp.route("/puantajlar/<int:puantaj_id>", methods=["DELETE"])
@auth_required
def delete_puantaj(puantaj_id):
    """Delete attendance record."""
    try:
        db = get_db_session()
        deleted = queries.delete_puantaj(db, puantaj_id)
        db.close()
        
        if not deleted:
            return jsonify({"error": "Puantaj not found"}), 404
        
        return jsonify({"message": "Puantaj deleted"}), 204
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# ============================================================================
# VARDIYA PLAN (SHIFT PLAN) ENDPOINTS
# ============================================================================

def _check_vardiya_plan_period_permission(db, target_date):
    """
    Check if the user has permission to edit vardiya plan for target_date.
    Admins can always edit.
    Users with Permission 79 ("Vardiya Plan Geçmiş Veri Erişimi") can edit today and past dates.
    Users without Permission 79 CAN ONLY enter/edit plans starting from tomorrow onwards (target_date > today).
    Today and past dates (target_date <= today) require Permission 79.
    """
    from app.modules.auth import queries as auth_queries
    user_id = session.get('user_id')
    if not user_id:
        return True  # Handled by auth_required
    
    user = auth_queries.get_kullanici_by_id(db, user_id)
    if not user:
        return False
        
    is_admin = (user.Kullanici_Adi and user.Kullanici_Adi.lower() == 'admin')
    if not is_admin:
        roles = auth_queries.get_user_roles(db, user.Kullanici_ID)
        is_admin = 'admin' in [r.lower() for r in roles]
        
    if is_admin:
        return True
        
    has_gecmis_yetki = auth_queries.has_permission(db, user.Kullanici_ID, "Vardiya Plan Geçmiş Veri Erişimi")
    if has_gecmis_yetki:
        return True

    from datetime import datetime as dt
    today = dt.now().date()

    # Rule: Without Yetki 79, cannot add or modify records for today or earlier dates (target_date <= today)
    if target_date <= today:
        return False

    return True


@hr_bp.route("/vardiya-planlar", methods=["GET"])
@auth_required
def list_vardiya_planlar():
    """List shift plans with optional filtering."""
    try:
        skip = request.args.get("skip", 0, type=int)
        limit = min(request.args.get("limit", 100, type=int), 1000)
        tc_no = request.args.get("tc_no", None, type=str)
        sube_id = request.args.get("sube_id", None, type=int)
        secim_id = request.args.get("secim_id", None, type=int)

        db = get_db_session()
        planlar = queries.get_vardiya_planlar(db, skip, limit, tc_no, sube_id, secim_id)
        db.close()

        result = [
            {
                "Vardiya_Plan_ID": p.Vardiya_Plan_ID,
                "Tarih": p.Tarih.isoformat(),
                "TC_No": p.TC_No,
                "Secim_ID": p.Secim_ID,
                "Sube_ID": p.Sube_ID,
                "Kayit_Tarihi": p.Kayit_Tarihi.isoformat() if p.Kayit_Tarihi else None,
            }
            for p in planlar
        ]
        return jsonify(result), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@hr_bp.route("/vardiya-planlar/<int:plan_id>", methods=["GET"])
@auth_required
def get_vardiya_plan(plan_id):
    """Get shift plan by ID."""
    try:
        db = get_db_session()
        plan = queries.get_vardiya_plan_by_id(db, plan_id)
        db.close()

        if not plan:
            return jsonify({"error": "VardiyaPlan not found"}), 404

        result = {
            "Vardiya_Plan_ID": plan.Vardiya_Plan_ID,
            "Tarih": plan.Tarih.isoformat(),
            "TC_No": plan.TC_No,
            "Secim_ID": plan.Secim_ID,
            "Sube_ID": plan.Sube_ID,
            "Kayit_Tarihi": plan.Kayit_Tarihi.isoformat() if plan.Kayit_Tarihi else None,
        }
        return jsonify(result), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@hr_bp.route("/vardiya-planlar", methods=["POST"])
@auth_required
def create_vardiya_plan():
    """Create a new shift plan record."""
    try:
        data = request.get_json()
        if not data or "TC_No" not in data or "Secim_ID" not in data or "Sube_ID" not in data:
            return jsonify({"error": "TC_No, Secim_ID, and Sube_ID required"}), 400

        from datetime import date as date_type
        target_date = data.get("Tarih")
        if isinstance(target_date, str):
            target_date = date_type.fromisoformat(target_date)
        elif target_date is None:
            from datetime import datetime as dt
            target_date = dt.now().date()

        db = get_db_session()

        # Check permission (Yetki 79 / Admin for today and past dates)
        if not _check_vardiya_plan_period_permission(db, target_date):
            db.close()
            return jsonify({"error": "Bugün ve geçmiş günlere ait vardiya planı giriş/düzenleme yetkiniz bulunmamaktadır."}), 403

        # Validation: Secim must have Planli == True
        secim = queries.get_puantaj_secim_by_id(db, data["Secim_ID"])
        if not secim or not getattr(secim, "Planli", False) or not secim.Aktif_Pasif:
            db.close()
            return jsonify({"error": "Seçilen puantaj türü vardiya planı için geçerli değildir."}), 400

        # Validation: Date cannot be before Sigorta_Giris or after Sigorta_Cikis
        calisan = queries.get_calisan_by_tc_no(db, data["TC_No"])
        if calisan:
            if calisan.Sigorta_Giris and target_date < calisan.Sigorta_Giris:
                db.close()
                return jsonify({"error": f"Sigorta giriş tarihinden ({calisan.Sigorta_Giris.strftime('%d.%m.%Y')}) öncesine veri girişi yapılamaz."}), 403
            if calisan.Sigorta_Cikis and target_date > calisan.Sigorta_Cikis:
                db.close()
                return jsonify({"error": f"Sigorta çıkış tarihinden ({calisan.Sigorta_Cikis.strftime('%d.%m.%Y')}) sonrasına veri girişi yapılamaz."}), 403

        new_plan = queries.create_vardiya_plan(
            db,
            tc_no=data["TC_No"],
            secim_id=data["Secim_ID"],
            sube_id=data["Sube_ID"],
            tarih=target_date,
            kayit_tarihi=data.get("Kayit_Tarihi")
        )
        db.close()

        result = {
            "Vardiya_Plan_ID": new_plan.Vardiya_Plan_ID,
            "Tarih": new_plan.Tarih.isoformat(),
            "TC_No": new_plan.TC_No,
            "Secim_ID": new_plan.Secim_ID,
            "Sube_ID": new_plan.Sube_ID,
            "Kayit_Tarihi": new_plan.Kayit_Tarihi.isoformat() if new_plan.Kayit_Tarihi else None,
        }
        return jsonify(result), 201
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@hr_bp.route("/vardiya-planlar/<int:plan_id>", methods=["PUT"])
@auth_required
def update_vardiya_plan(plan_id):
    """Update shift plan record."""
    try:
        data = request.get_json()
        db = get_db_session()

        plan = queries.get_vardiya_plan_by_id(db, plan_id)
        if not plan:
            db.close()
            return jsonify({"error": "VardiyaPlan not found"}), 404

        from datetime import date as date_type
        target_date = data.get("Tarih")
        if target_date:
            if isinstance(target_date, str):
                target_date = date_type.fromisoformat(target_date)
        else:
            target_date = plan.Tarih

        # Check permission (Yetki 79 / Admin for today and past dates)
        if not _check_vardiya_plan_period_permission(db, target_date):
            db.close()
            return jsonify({"error": "Bugün ve geçmiş günlere ait vardiya planı giriş/düzenleme yetkiniz bulunmamaktadır."}), 403

        # Validation: If Secim_ID is being updated, it must have Planli == True
        new_secim_id = data.get("Secim_ID")
        if new_secim_id is not None:
            secim = queries.get_puantaj_secim_by_id(db, new_secim_id)
            if not secim or not getattr(secim, "Planli", False) or not secim.Aktif_Pasif:
                db.close()
                return jsonify({"error": "Seçilen puantaj türü vardiya planı için geçerli değildir."}), 400

        calisan = queries.get_calisan_by_tc_no(db, plan.TC_No)
        if calisan:
            if calisan.Sigorta_Giris and target_date < calisan.Sigorta_Giris:
                db.close()
                return jsonify({"error": f"Sigorta giriş tarihinden ({calisan.Sigorta_Giris.strftime('%d.%m.%Y')}) öncesine veri girişi yapılamaz."}), 403
            if calisan.Sigorta_Cikis and target_date > calisan.Sigorta_Cikis:
                db.close()
                return jsonify({"error": f"Sigorta çıkış tarihinden ({calisan.Sigorta_Cikis.strftime('%d.%m.%Y')}) sonrasına veri girişi yapılamaz."}), 403

        updated_plan = queries.update_vardiya_plan(
            db,
            plan_id,
            secim_id=data.get("Secim_ID"),
            tarih=target_date,
            sube_id=data.get("Sube_ID")
        )
        db.close()

        result = {
            "Vardiya_Plan_ID": updated_plan.Vardiya_Plan_ID,
            "Tarih": updated_plan.Tarih.isoformat(),
            "TC_No": updated_plan.TC_No,
            "Secim_ID": updated_plan.Secim_ID,
            "Sube_ID": updated_plan.Sube_ID,
            "Kayit_Tarihi": updated_plan.Kayit_Tarihi.isoformat() if updated_plan.Kayit_Tarihi else None,
        }
        return jsonify(result), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@hr_bp.route("/vardiya-planlar/<int:plan_id>", methods=["DELETE"])
@auth_required
def delete_vardiya_plan(plan_id):
    """Delete shift plan record."""
    try:
        db = get_db_session()
        plan = queries.get_vardiya_plan_by_id(db, plan_id)
        if not plan:
            db.close()
            return jsonify({"error": "VardiyaPlan not found"}), 404

        if not _check_vardiya_plan_period_permission(db, plan.Tarih):
            db.close()
            return jsonify({"error": "Bugün ve geçmiş günlere ait vardiya planı silme yetkiniz bulunmamaktadır."}), 403

        queries.delete_vardiya_plan(db, plan_id)
        db.close()
        return jsonify({"message": "VardiyaPlan deleted"}), 204
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# ============================================================================
# AVANS ISTEK (ADVANCE REQUEST) ENDPOINTS
# ============================================================================

@hr_bp.route("/avans-istekler", methods=["GET"])
@auth_required
def list_avans_istekler():
    """Get all advance requests with optional filtering."""
    try:
        skip = request.args.get("skip", 0, type=int)
        limit = min(request.args.get("limit", 100, type=int), 1000)
        tc_no = request.args.get("tc_no", None, type=str)
        sube_id = request.args.get("sube_id", None, type=int)
        donem = request.args.get("donem", None, type=int)
        
        db = get_db_session()
        istekler = queries.get_avans_istekler(db, skip, limit, tc_no, sube_id, donem)
        db.close()
        
        result = [
            {
                "Avans_ID": a.Avans_ID,
                "Donem": a.Donem,
                "TC_No": a.TC_No,
                "Tutar": float(a.Tutar),
                "Aciklama": a.Aciklama,
                "Sube_ID": a.Sube_ID,
                "Kayit_Tarihi": a.Kayit_Tarihi.isoformat(),
            }
            for a in istekler
        ]
        
        return jsonify(result), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@hr_bp.route("/avans-istekler/<int:avans_id>", methods=["GET"])
@auth_required
def get_avans_istek(avans_id):
    """Get advance request by ID."""
    try:
        db = get_db_session()
        istek = queries.get_avans_istek_by_id(db, avans_id)
        db.close()
        
        if not istek:
            return jsonify({"error": "AvansIstek not found"}), 404
        
        result = {
            "Avans_ID": istek.Avans_ID,
            "Donem": istek.Donem,
            "TC_No": istek.TC_No,
            "Tutar": float(istek.Tutar),
            "Aciklama": istek.Aciklama,
            "Sube_ID": istek.Sube_ID,
            "Kayit_Tarihi": istek.Kayit_Tarihi.isoformat(),
        }
        
        return jsonify(result), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@hr_bp.route("/avans-istekler", methods=["POST"])
@auth_required
def create_avans_istek():
    """Create a new advance request."""
    try:
        data = request.get_json()
        if not data or "TC_No" not in data or "Sube_ID" not in data or "Donem" not in data or "Tutar" not in data:
            return jsonify({"error": "TC_No, Sube_ID, Donem, and Tutar required"}), 400
        
        # Period-based restriction
        from datetime import datetime
        today = datetime.now()
        current_donem = int(f"{str(today.year)[2:]}{today.month:02d}")
        if int(data["Donem"]) != current_donem:
            return jsonify({"error": "Talep girişi yalnızca bulunan ayda yapılabilir."}), 403
        
        db = get_db_session()
        
        # Duplicate check: check if person already has a request for this month
        existing_requests = queries.get_avans_istekler(db, tc_no=data["TC_No"], donem=int(data["Donem"]))
        if existing_requests:
            db.close()
            return jsonify({"error": "Bu çalışan için bu dönemde zaten bir avans talebi bulunmaktadır."}), 400
            
        new_istek = queries.create_avans_istek(
            db,
            tc_no=data["TC_No"],
            sube_id=data["Sube_ID"],
            donem=int(data["Donem"]),
            tutar=float(data["Tutar"]),
            aciklama=data.get("Aciklama"),
            kayit_tarihi=data.get("Kayit_Tarihi")
        )
        db.close()
        
        result = {
            "Avans_ID": new_istek.Avans_ID,
            "Donem": new_istek.Donem,
            "TC_No": new_istek.TC_No,
            "Tutar": float(new_istek.Tutar),
            "Aciklama": new_istek.Aciklama,
            "Sube_ID": new_istek.Sube_ID,
            "Kayit_Tarihi": new_istek.Kayit_Tarihi.isoformat(),
        }
        
        return jsonify(result), 201
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@hr_bp.route("/avans-istekler/<int:avans_id>", methods=["PUT"])
@auth_required
def update_avans_istek(avans_id):
    """Update advance request."""
    try:
        data = request.get_json()
        
        db = get_db_session()
        
        # Period-based restriction
        istek = queries.get_avans_istek_by_id(db, avans_id)
        if not istek:
            db.close()
            return jsonify({"error": "AvansIstek not found"}), 404
            
        from datetime import datetime
        today = datetime.now()
        current_donem = int(f"{str(today.year)[2:]}{today.month:02d}")
        if istek.Donem != current_donem:
            db.close()
            return jsonify({"error": "Talep değişikliği yalnızca bulunan ayda yapılabilir."}), 403

        updated_istek = queries.update_avans_istek(
            db,
            avans_id,
            tutar=float(data.get("Tutar")) if "Tutar" in data else None,
            aciklama=data.get("Aciklama")
        )
        db.close()
        
        if not updated_istek:
            return jsonify({"error": "AvansIstek not found"}), 404
        
        result = {
            "Avans_ID": updated_istek.Avans_ID,
            "Donem": updated_istek.Donem,
            "TC_No": updated_istek.TC_No,
            "Tutar": float(updated_istek.Tutar),
            "Aciklama": updated_istek.Aciklama,
            "Sube_ID": updated_istek.Sube_ID,
            "Kayit_Tarihi": updated_istek.Kayit_Tarihi.isoformat(),
        }
        
        return jsonify(result), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@hr_bp.route("/avans-istekler/<int:avans_id>", methods=["DELETE"])
@auth_required
def delete_avans_istek(avans_id):
    """Delete advance request."""
    try:
        db = get_db_session()
        
        # Period-based restriction
        istek = queries.get_avans_istek_by_id(db, avans_id)
        if not istek:
            db.close()
            return jsonify({"error": "AvansIstek not found"}), 404
            
        from datetime import datetime
        today = datetime.now()
        current_donem = int(f"{str(today.year)[2:]}{today.month:02d}")
        if istek.Donem != current_donem:
            db.close()
            return jsonify({"error": "Talep silme işlemi yalnızca bulunan ayda yapılabilir."}), 403

        deleted = queries.delete_avans_istek(db, avans_id)
        db.close()
        
        if not deleted:
            return jsonify({"error": "AvansIstek not found"}), 404
        
        return jsonify({"message": "AvansIstek deleted"}), 204
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# ============================================================================
# CALISAN TALEP (EMPLOYEE REQUEST) ENDPOINTS
# ============================================================================

@hr_bp.route("/calisan-talepler", methods=["GET"])
@auth_required
def list_calisan_talepler():
    """Get all employee requests."""
    try:
        skip = request.args.get("skip", 0, type=int)
        limit = min(request.args.get("limit", 100, type=int), 1000)
        sube_id = request.args.get("sube_id", None, type=int)
        talep = request.args.get("talep", None, type=str)
        
        db = get_db_session()
        talepler = queries.get_calisan_talepler(db, skip, limit, sube_id, talep)
        db.close()
        
        result = [
            {
                "Calisan_Talep_ID": t.Calisan_Talep_ID,
                "Talep": t.Talep,
                "TC_No": t.TC_No,
                "Adi": t.Adi,
                "Soyadi": t.Soyadi,
                "Ilk_Soyadi": t.Ilk_Soyadi,
                "Sube_ID": t.Sube_ID,
                "Hesap_No": t.Hesap_No,
                "IBAN": t.IBAN,
                "Net_Maas": float(t.Net_Maas) if t.Net_Maas else None,
                "Sigorta_Giris": t.Sigorta_Giris.isoformat() if t.Sigorta_Giris else None,
                "Sigorta_Cikis": t.Sigorta_Cikis.isoformat() if t.Sigorta_Cikis else None,
                "Kayit_Tarih": t.Kayit_Tarih.isoformat(),
            }
            for t in talepler
        ]
        
        return jsonify(result), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@hr_bp.route("/calisan-talepler/<int:talep_id>", methods=["GET"])
@auth_required
def get_calisan_talep(talep_id):
    """Get employee request by ID."""
    try:
        db = get_db_session()
        talep = queries.get_calisan_talep_by_id(db, talep_id)
        db.close()
        
        if not talep:
            return jsonify({"error": "CalisanTalep not found"}), 404
        
        result = {
            "Calisan_Talep_ID": talep.Calisan_Talep_ID,
            "Talep": talep.Talep,
            "TC_No": talep.TC_No,
            "Adi": talep.Adi,
            "Soyadi": talep.Soyadi,
            "Ilk_Soyadi": talep.Ilk_Soyadi,
            "Sube_ID": talep.Sube_ID,
            "Hesap_No": talep.Hesap_No,
            "IBAN": talep.IBAN,
            "Net_Maas": float(talep.Net_Maas) if talep.Net_Maas else None,
            "Sigorta_Giris": talep.Sigorta_Giris.isoformat() if talep.Sigorta_Giris else None,
            "Sigorta_Cikis": talep.Sigorta_Cikis.isoformat() if talep.Sigorta_Cikis else None,
            "Kayit_Tarih": talep.Kayit_Tarih.isoformat(),
        }
        
        return jsonify(result), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@hr_bp.route("/calisan-talepler", methods=["POST"])
@auth_required
def create_calisan_talep():
    """Create a new employee request."""
    try:
        data = request.get_json()
        if not data or not all(k in data for k in ("TC_No", "Adi", "Soyadi", "Sube_ID")):
            return jsonify({"error": "TC_No, Adi, Soyadi, and Sube_ID required"}), 400
        
        db = get_db_session()
        new_talep = queries.create_calisan_talep(
            db,
            tc_no=data["TC_No"],
            adi=data["Adi"],
            soyadi=data["Soyadi"],
            ilk_soyadi=data.get("Ilk_Soyadi"),
            sube_id=data["Sube_ID"],
            talep=data.get("Talep", "İşe Giriş"),
            hesap_no=data.get("Hesap_No"),
            iban=data.get("IBAN"),
            ogrenim_durumu=data.get("Ogrenim_Durumu"),
            cinsiyet=data.get("Cinsiyet", "Erkek"),
            gorevi=data.get("Gorevi"),
            anne_adi=data.get("Anne_Adi"),
            baba_adi=data.get("Baba_Adi"),
            dogum_yeri=data.get("Dogum_Yeri"),
            dogum_tarihi=data.get("Dogum_Tarihi"),
            medeni_hali=data.get("Medeni_Hali", "Bekar"),
            cep_no=data.get("Cep_No"),
            adres_bilgileri=data.get("Adres_Bilgileri"),
            gelir_vergisi_matrahi=float(data.get("Gelir_Vergisi_Matrahi")) if "Gelir_Vergisi_Matrahi" in data else None,
            ssk_cikis_nedeni=data.get("SSK_Cikis_Nedeni"),
            net_maas=float(data.get("Net_Maas")) if "Net_Maas" in data else None,
            sigorta_giris=data.get("Sigorta_Giris"),
            sigorta_cikis=data.get("Sigorta_Cikis")
        )
        db.close()
        
        result = {
            "Calisan_Talep_ID": new_talep.Calisan_Talep_ID,
            "Talep": new_talep.Talep,
            "TC_No": new_talep.TC_No,
            "Adi": new_talep.Adi,
            "Soyadi": new_talep.Soyadi,
            "Ilk_Soyadi": new_talep.Ilk_Soyadi,
            "Sube_ID": new_talep.Sube_ID,
            "Hesap_No": new_talep.Hesap_No,
            "IBAN": new_talep.IBAN,
            "Net_Maas": float(new_talep.Net_Maas) if new_talep.Net_Maas else None,
            "Sigorta_Giris": new_talep.Sigorta_Giris.isoformat() if new_talep.Sigorta_Giris else None,
            "Sigorta_Cikis": new_talep.Sigorta_Cikis.isoformat() if new_talep.Sigorta_Cikis else None,
            "Kayit_Tarih": new_talep.Kayit_Tarih.isoformat(),
        }
        
        return jsonify(result), 201
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@hr_bp.route("/calisan-talepler/<int:talep_id>", methods=["PUT"])
@auth_required
def update_calisan_talep(talep_id):
    """Update employee request."""
    try:
        data = request.get_json()
        
        db = get_db_session()
        updated_talep = queries.update_calisan_talep(
            db,
            talep_id,
            adi=data.get("Adi"),
            soyadi=data.get("Soyadi"),
            ilk_soyadi=data.get("Ilk_Soyadi"),
            hesap_no=data.get("Hesap_No"),
            iban=data.get("IBAN"),
            ogrenim_durumu=data.get("Ogrenim_Durumu"),
            cinsiyet=data.get("Cinsiyet"),
            gorevi=data.get("Gorevi"),
            anne_adi=data.get("Anne_Adi"),
            baba_adi=data.get("Baba_Adi"),
            dogum_yeri=data.get("Dogum_Yeri"),
            dogum_tarihi=data.get("Dogum_Tarihi"),
            medeni_hali=data.get("Medeni_Hali"),
            cep_no=data.get("Cep_No"),
            adres_bilgileri=data.get("Adres_Bilgileri"),
            gelir_vergisi_matrahi=float(data.get("Gelir_Vergisi_Matrahi")) if "Gelir_Vergisi_Matrahi" in data and data["Gelir_Vergisi_Matrahi"] else None,
            ssk_cikis_nedeni=data.get("SSK_Cikis_Nedeni"),
            net_maas=float(data.get("Net_Maas")) if "Net_Maas" in data and data["Net_Maas"] else None,
            sigorta_giris=data.get("Sigorta_Giris"),
            sigorta_cikis=data.get("Sigorta_Cikis")
        )
        db.close()
        
        if not updated_talep:
            return jsonify({"error": "CalisanTalep not found"}), 404
        
        result = {
            "Calisan_Talep_ID": updated_talep.Calisan_Talep_ID,
            "Talep": updated_talep.Talep,
            "TC_No": updated_talep.TC_No,
            "Adi": updated_talep.Adi,
            "Soyadi": updated_talep.Soyadi,
            "Ilk_Soyadi": updated_talep.Ilk_Soyadi,
            "Sube_ID": updated_talep.Sube_ID,
            "Hesap_No": updated_talep.Hesap_No,
            "IBAN": updated_talep.IBAN,
            "Ogrenim_Durumu": updated_talep.Ogrenim_Durumu,
            "Cinsiyet": updated_talep.Cinsiyet,
            "Gorevi": updated_talep.Gorevi,
            "Anne_Adi": updated_talep.Anne_Adi,
            "Baba_Adi": updated_talep.Baba_Adi,
            "Dogum_Yeri": updated_talep.Dogum_Yeri,
            "Dogum_Tarihi": updated_talep.Dogum_Tarihi.isoformat() if updated_talep.Dogum_Tarihi else None,
            "Medeni_Hali": updated_talep.Medeni_Hali,
            "Cep_No": updated_talep.Cep_No,
            "Adres_Bilgileri": updated_talep.Adres_Bilgileri,
            "Gelir_Vergisi_Matrahi": float(updated_talep.Gelir_Vergisi_Matrahi) if updated_talep.Gelir_Vergisi_Matrahi else None,
            "SSK_Cikis_Nedeni": updated_talep.SSK_Cikis_Nedeni,
            "Net_Maas": float(updated_talep.Net_Maas) if updated_talep.Net_Maas else None,
            "Sigorta_Giris": updated_talep.Sigorta_Giris.isoformat() if updated_talep.Sigorta_Giris else None,
            "Sigorta_Cikis": updated_talep.Sigorta_Cikis.isoformat() if updated_talep.Sigorta_Cikis else None,
            "Kayit_Tarih": updated_talep.Kayit_Tarih.isoformat(),
        }
        
        return jsonify(result), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@hr_bp.route("/calisan-talepler/<int:talep_id>", methods=["DELETE"])
@auth_required
def delete_calisan_talep(talep_id):
    """Delete employee request."""
    try:
        db = get_db_session()
        deleted = queries.delete_calisan_talep(db, talep_id)
        db.close()
        
        if not deleted:
            return jsonify({"error": "CalisanTalep not found"}), 404
        
        return jsonify({"message": "CalisanTalep deleted"}), 204
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@hr_bp.route("/calisan-talepler/<int:talep_id>/approve-hr", methods=["POST"])
@auth_required
def approve_calisan_talep_hr(talep_id):
    """Approve employee request by HR."""
    try:
        user = request.user
        db = get_db_session()
        updated = queries.approve_calisan_talep_hr(db, talep_id, user.Kullanici_ID)
        db.close()
        
        if not updated:
            return jsonify({"error": "CalisanTalep not found"}), 404
        
        return jsonify({"message": "HR Approval successful", "talep_id": talep_id}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@hr_bp.route("/calisan-talepler/<int:talep_id>/approve-ssk", methods=["POST"])
@auth_required
def approve_calisan_talep_ssk(talep_id):
    """Approve employee request by SSK."""
    try:
        user = request.user
        db = get_db_session()
        updated = queries.approve_calisan_talep_ssk(db, talep_id, user.Kullanici_ID)
        db.close()
        
        if not updated:
            return jsonify({"error": "CalisanTalep not found"}), 404
        
        return jsonify({"message": "SSK Approval successful", "talep_id": talep_id}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# ============================================================================
# MOBIL ROSTER (GİRİŞ / ÇIKIŞ) ENDPOINTS
# ============================================================================

def _is_current_user_admin(db, user) -> bool:
    """Helper to check if current logged in user has admin role."""
    from app.modules.auth import queries as auth_queries
    if not user:
        return False
    if getattr(user, 'Kullanici_Adi', '') and user.Kullanici_Adi.lower() == 'admin':
        return True
    roles = auth_queries.get_user_roles(db, user.Kullanici_ID)
    return 'admin' in [r.lower() for r in roles]


def _check_user_permission(db, user, perm_name: str) -> bool:
    """Helper to verify if user is admin or possesses named permission."""
    from app.modules.auth import queries as auth_queries
    if _is_current_user_admin(db, user):
        return True
    if not user:
        return False
    return auth_queries.has_permission(db, user.Kullanici_ID, perm_name)


# --- 1. Barkod Endpoints (Protected with #75) ---

@hr_bp.route("/barkodlar", methods=["GET"])
@auth_required
def list_barkodlar():
    """List barcodes, optionally filtered by sube_id (#75)."""
    db = get_db_session()
    try:
        user = request.user
        if not _check_user_permission(db, user, "Barkod Ekranı Görüntüleme"):
            return jsonify({"error": "Barkod Ekranı Görüntüleme yetkiniz bulunmamaktadır."}), 403

        sube_id = request.args.get("sube_id", type=int)
        barkodlar = queries.get_barkodlar_by_sube(db, sube_id)
        
        result = []
        for b in barkodlar:
            result.append({
                "id": b.id,
                "sube_id": b.sube_id,
                "sube_adi": b.sube.Sube_Adi if b.sube else "",
                "barkod_kodu": b.barkod_kodu,
                "aktif": bool(b.aktif),
                "olusturan_id": b.olusturan_id,
                "olusturan_adi": b.olusturan.Adi_Soyadi if b.olusturan else "",
                "olusturma_zamani": b.olusturma_zamani.strftime("%d.%m.%Y %H:%M:%S") if b.olusturma_zamani else ""
            })
        return jsonify(result), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        db.close()


@hr_bp.route("/barkodlar", methods=["POST"])
@auth_required
def create_new_barkod():
    """Create a new random barcode for a branch (#75)."""
    db = get_db_session()
    try:
        user = request.user
        if not _check_user_permission(db, user, "Barkod Ekranı Görüntüleme"):
            return jsonify({"error": "Barkod oluşturma yetkiniz bulunmamaktadır."}), 403

        data = request.get_json() or {}
        sube_id = data.get("sube_id")
        if not sube_id:
            return jsonify({"error": "Şube seçimi zorunludur."}), 400

        from app.models import Sube
        sube = db.get(Sube, sube_id)
        if not sube:
            return jsonify({"error": "Geçerli bir şube bulunamadı."}), 404

        barkod = queries.create_barkod(db, sube_id=sube_id, olusturan_id=user.Kullanici_ID)
        return jsonify({
            "message": "Barkod başarıyla oluşturuldu.",
            "id": barkod.id,
            "sube_id": barkod.sube_id,
            "sube_adi": sube.Sube_Adi,
            "barkod_kodu": barkod.barkod_kodu,
            "aktif": barkod.aktif,
            "olusturma_zamani": barkod.olusturma_zamani.strftime("%d.%m.%Y %H:%M:%S")
        }), 201
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        db.close()


@hr_bp.route("/barkodlar/<int:barkod_id>/toggle-durum", methods=["PUT"])
@auth_required
def toggle_barkod_status(barkod_id):
    """Toggle active/passive state of a barcode (#75)."""
    db = get_db_session()
    try:
        user = request.user
        if not _check_user_permission(db, user, "Barkod Ekranı Görüntüleme"):
            return jsonify({"error": "Barkod durumu değiştirme yetkiniz bulunmamaktadır."}), 403

        barkod = queries.toggle_barkod_durum(db, barkod_id)
        if not barkod:
            return jsonify({"error": "Barkod bulunamadı."}), 404

        return jsonify({
            "message": "Barkod durumu güncellendi.",
            "id": barkod.id,
            "aktif": barkod.aktif
        }), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        db.close()


# --- 2. Public Mobile Vardiya Endpoints (No Login Required) ---

@hr_bp.route("/vardiya/token-kontrol", methods=["GET"])
def check_vardiya_token():
    """
    Public token validation endpoint for mobile check-in/out.
    Checks if token is valid and active. Does not leak employee list or TC numbers.
    """
    token = request.args.get("kod", "").strip()
    if not token:
        return jsonify({"valid": False, "message": "Barkod geçersiz. Lütfen şubedeki barkodu okutun."}), 400

    db = get_db_session()
    try:
        barkod = queries.get_barkod_by_token(db, token)
        if not barkod or not barkod.aktif:
            return jsonify({"valid": False, "message": "Barkod geçersiz veya pasif. Lütfen şubedeki barkodu okutun."}), 400

        sube = barkod.sube
        return jsonify({
            "valid": True,
            "sube_id": barkod.sube_id,
            "sube_adi": sube.Sube_Adi if sube else "Tanımsız Şube"
        }), 200
    except Exception as e:
        return jsonify({"valid": False, "message": f"Sunucu hatası: {str(e)}"}), 500
    finally:
        db.close()


@hr_bp.route("/vardiya/calisan-dogrula", methods=["POST"])
def verify_calisan_for_mobile():
    """
    Public employee verification endpoint.
    Validates entered TC_No:
    - Must exist in Calisan table and be active (Aktif_Pasif=True)
    - Must belong to the barcode's branch (Rule 10.3)
    - If Calisan.Cihaz_Kaydi is set, must match passed cihaz_id
    - If cihaz_id is already bound to another employee, reject
    """
    data = request.get_json() or {}
    token = data.get("kod", "").strip()
    tc_no = data.get("tc_no", "").strip()
    cihaz_id = data.get("cihaz_id", "").strip()

    client_ip = request.headers.get("X-Forwarded-For", request.remote_addr)
    user_agent = request.headers.get("User-Agent", "")

    if not token or not tc_no:
        return jsonify({"success": False, "message": "Barkod kodu ve T.C. kimlik numarası zorunludur."}), 400

    db = get_db_session()
    try:
        barkod = queries.get_barkod_by_token(db, token)
        if not barkod or not barkod.aktif:
            queries.log_vardiya_red_deneme(
                db, neden="GECERSIZ_BARKOD",
                cihaz_id=cihaz_id, kullanici_araci=user_agent, ip_adresi=client_ip
            )
            return jsonify({"success": False, "message": "Barkod geçersiz. Lütfen şubedeki barkodu okutun."}), 400

        from app.models import Calisan
        calisan = db.get(Calisan, tc_no)
        if not calisan or not calisan.Aktif_Pasif:
            queries.log_vardiya_red_deneme(
                db, neden="TC_ESLESMEDI", sube_id=barkod.sube_id, barkod_id=barkod.id,
                cihaz_id=cihaz_id, kullanici_araci=user_agent, ip_adresi=client_ip
            )
            return jsonify({"success": False, "message": "Girilen T.C. kimlik numarası aktif çalışanlar arasında bulunamadı."}), 400

        # Branch check: Employee must belong to the barcode's branch
        if calisan.Sube_ID != barkod.sube_id:
            queries.log_vardiya_red_deneme(
                db, neden="BOLGE_DISI", calisan_id=calisan.TC_No, sube_id=barkod.sube_id, barkod_id=barkod.id,
                cihaz_id=cihaz_id, kullanici_araci=user_agent, ip_adresi=client_ip
            )
            return jsonify({"success": False, "message": "Kayıtlı olduğunuz şube ile barkodun ait olduğu şube uyuşmuyor."}), 400

        # Device checks
        if cihaz_id:
            # Check if this employee already has a different device bound
            if calisan.Cihaz_Kaydi and calisan.Cihaz_Kaydi != cihaz_id:
                queries.log_vardiya_red_deneme(
                    db, neden="CIHAZ_KAYDI_DOLU", calisan_id=calisan.TC_No, sube_id=barkod.sube_id, barkod_id=barkod.id,
                    cihaz_id=cihaz_id, kullanici_araci=user_agent, ip_adresi=client_ip
                )
                return jsonify({"success": False, "message": "Bu kişi için başka bir cihaz kaydı mevcut. Kayıt yapılamaz."}), 400

            # Check if this device is already bound to another employee
            other_calisan = db.query(Calisan).filter(Calisan.Cihaz_Kaydi == cihaz_id, Calisan.TC_No != calisan.TC_No).first()
            if other_calisan:
                queries.log_vardiya_red_deneme(
                    db, neden="CIHAZ_KAYDI_DOLU", calisan_id=calisan.TC_No, sube_id=barkod.sube_id, barkod_id=barkod.id,
                    cihaz_id=cihaz_id, kullanici_araci=user_agent, ip_adresi=client_ip
                )
                return jsonify({"success": False, "message": "Bu cihaz başka bir çalışanla ilişkilendirilmiş."}), 400

        # Check last operation for duplicate warning check
        last_rec = queries.get_last_vardiya_kayit_for_calisan(db, calisan.TC_No)
        last_islem = last_rec.islem_tipi if last_rec else None

        return jsonify({
            "success": True,
            "calisan_adi": f"{calisan.Adi} {calisan.Soyadi[:1]}.",
            "last_islem": last_islem,
            "is_device_bound": bool(calisan.Cihaz_Kaydi)
        }), 200
    except Exception as e:
        return jsonify({"success": False, "message": f"Sunucu hatası: {str(e)}"}), 500
    finally:
        db.close()


@hr_bp.route("/vardiya/islem", methods=["POST"])
def submit_vardiya_islem():
    """
    Public mobile shift check-in/out submission endpoint.
    Performs full server-side validation:
    1. Validate barcode token (active, not expired)
    2. Validate employee (active, assigned branch matches barcode's branch)
    3. Validate device binding (Cihaz_Kaydi):
       - If empty, bind now to employee
       - If already set, must match submitted cihaz_id
       - If submitted cihaz_id already used by someone else, reject
    4. Validate coordinates and GPS accuracy:
       - lat/lon required, else KONUM_ALINAMADI
       - accuracy <= 200m, else KONUM_DOGRULUGU_DUSUK
       - branch must have merkez_enlem and merkez_boylam, else BOLGE_DISI
       - distance <= branch.yaricap_m, else BOLGE_DISI
    5. Check consecutive same action:
       - If duplicate and not confirmed, return duplicate prompt flag
       - If confirmed, set mukerrer_uyari = True
    6. Log rejected attempts to vardiya_red_deneme
    """
    data = request.get_json() or {}
    token = data.get("kod", "").strip()
    tc_no = data.get("tc_no", "").strip()
    islem_tipi = (data.get("islem_tipi") or "").upper().strip()
    cihaz_id = data.get("cihaz_id", "").strip()
    istemci_zamani_raw = data.get("istemci_zamani")
    confirm_mukerrer = bool(data.get("confirm_mukerrer", False))

    enlem = data.get("enlem")
    boylam = data.get("boylam")
    konum_dogrulugu_m = data.get("konum_dogrulugu_m")
    platform = data.get("platform", "")
    ekran = data.get("ekran", "")

    client_ip = request.headers.get("X-Forwarded-For", request.remote_addr)
    user_agent = request.headers.get("User-Agent", "")

    if islem_tipi not in ["GIRIS", "CIKIS"]:
        return jsonify({"success": False, "message": "Geçersiz işlem tipi."}), 400

    istemci_zamani = None
    if istemci_zamani_raw:
        try:
            istemci_zamani = datetime.fromisoformat(istemci_zamani_raw.replace("Z", "+00:00"))
        except Exception:
            istemci_zamani = None

    db = get_db_session()
    try:
        # 1. Barcode check
        barkod = queries.get_barkod_by_token(db, token)
        if not barkod or not barkod.aktif:
            queries.log_vardiya_red_deneme(
                db, neden="GECERSIZ_BARKOD", islem_tipi=islem_tipi,
                cihaz_id=cihaz_id, kullanici_araci=user_agent, ip_adresi=client_ip
            )
            return jsonify({"success": False, "message": "Barkod geçersiz. Lütfen şubedeki barkodu okutun."}), 400

        sube = barkod.sube
        sube_id = barkod.sube_id

        # 2. Employee check
        from app.models import Calisan
        calisan = db.get(Calisan, tc_no)
        if not calisan or not calisan.Aktif_Pasif:
            queries.log_vardiya_red_deneme(
                db, neden="TC_ESLESMEDI", sube_id=sube_id, barkod_id=barkod.id, islem_tipi=islem_tipi,
                cihaz_id=cihaz_id, kullanici_araci=user_agent, ip_adresi=client_ip
            )
            return jsonify({"success": False, "message": "Girilen T.C. kimlik numarası aktif çalışanlar arasında bulunamadı."}), 400

        # Branch assignment check
        if calisan.Sube_ID != sube_id:
            queries.log_vardiya_red_deneme(
                db, neden="BOLGE_DISI", calisan_id=calisan.TC_No, sube_id=sube_id, barkod_id=barkod.id, islem_tipi=islem_tipi,
                cihaz_id=cihaz_id, kullanici_araci=user_agent, ip_adresi=client_ip
            )
            return jsonify({"success": False, "message": "Kayıtlı olduğunuz şube ile barkodun ait olduğu şube uyuşmuyor."}), 400

        # 3. Device check
        if not cihaz_id:
            queries.log_vardiya_red_deneme(
                db, neden="DIGER", calisan_id=calisan.TC_No, sube_id=sube_id, barkod_id=barkod.id, islem_tipi=islem_tipi,
                cihaz_id=cihaz_id, kullanici_araci=user_agent, ip_adresi=client_ip
            )
            return jsonify({"success": False, "message": "Cihaz tanımlayıcısı bulunamadı. Lütfen sayfayı yenileyin."}), 400

        if calisan.Cihaz_Kaydi and calisan.Cihaz_Kaydi != cihaz_id:
            queries.log_vardiya_red_deneme(
                db, neden="CIHAZ_KAYDI_DOLU", calisan_id=calisan.TC_No, sube_id=sube_id, barkod_id=barkod.id, islem_tipi=islem_tipi,
                cihaz_id=cihaz_id, kullanici_araci=user_agent, ip_adresi=client_ip
            )
            return jsonify({"success": False, "message": "Bu kişi için başka bir cihaz kaydı mevcut. Kayıt yapılamaz."}), 400

        other_calisan = db.query(Calisan).filter(Calisan.Cihaz_Kaydi == cihaz_id, Calisan.TC_No != calisan.TC_No).first()
        if other_calisan:
            queries.log_vardiya_red_deneme(
                db, neden="CIHAZ_KAYDI_DOLU", calisan_id=calisan.TC_No, sube_id=sube_id, barkod_id=barkod.id, islem_tipi=islem_tipi,
                cihaz_id=cihaz_id, kullanici_araci=user_agent, ip_adresi=client_ip
            )
            return jsonify({"success": False, "message": "Bu cihaz başka bir çalışanla ilişkilendirilmiş."}), 400

        # 4. Location & Geofence check
        if enlem is None or boylam is None:
            queries.log_vardiya_red_deneme(
                db, neden="KONUM_ALINAMADI", calisan_id=calisan.TC_No, sube_id=sube_id, barkod_id=barkod.id, islem_tipi=islem_tipi,
                cihaz_id=cihaz_id, kullanici_araci=user_agent, ip_adresi=client_ip
            )
            return jsonify({"success": False, "message": "Konumunuz alınamadı. Lütfen tekrar deneyin."}), 400

        try:
            enlem_val = float(enlem)
            boylam_val = float(boylam)
            accuracy_val = float(konum_dogrulugu_m) if konum_dogrulugu_m is not None else 999.0
        except (ValueError, TypeError):
            queries.log_vardiya_red_deneme(
                db, neden="KONUM_ALINAMADI", calisan_id=calisan.TC_No, sube_id=sube_id, barkod_id=barkod.id, islem_tipi=islem_tipi,
                cihaz_id=cihaz_id, kullanici_araci=user_agent, ip_adresi=client_ip
            )
            return jsonify({"success": False, "message": "Geçersiz konum verisi."}), 400

        if accuracy_val > 200.0:
            queries.log_vardiya_red_deneme(
                db, neden="KONUM_DOGRULUGU_DUSUK", calisan_id=calisan.TC_No, sube_id=sube_id, barkod_id=barkod.id, islem_tipi=islem_tipi,
                enlem=enlem_val, boylam=boylam_val, konum_dogrulugu_m=accuracy_val,
                cihaz_id=cihaz_id, kullanici_araci=user_agent, ip_adresi=client_ip
            )
            return jsonify({"success": False, "message": "GPS doğruluğu yetersiz. Açık alanda tekrar deneyin."}), 400

        if not sube or sube.merkez_enlem is None or sube.merkez_boylam is None:
            queries.log_vardiya_red_deneme(
                db, neden="BOLGE_DISI", calisan_id=calisan.TC_No, sube_id=sube_id, barkod_id=barkod.id, islem_tipi=islem_tipi,
                enlem=enlem_val, boylam=boylam_val, konum_dogrulugu_m=accuracy_val,
                cihaz_id=cihaz_id, kullanici_araci=user_agent, ip_adresi=client_ip
            )
            return jsonify({"success": False, "message": "Şubenin merkez koordinatları tanımlanmamış. Kayıt yapılamaz."}), 400

        branch_lat = float(sube.merkez_enlem)
        branch_lon = float(sube.merkez_boylam)
        radius_m = float(sube.yaricap_m or 100)

        distance_m = queries.calculate_haversine_distance(enlem_val, boylam_val, branch_lat, branch_lon)

        if distance_m > radius_m:
            queries.log_vardiya_red_deneme(
                db, neden="BOLGE_DISI", calisan_id=calisan.TC_No, sube_id=sube_id, barkod_id=barkod.id, islem_tipi=islem_tipi,
                enlem=enlem_val, boylam=boylam_val, konum_dogrulugu_m=accuracy_val, bolge_mesafesi_m=distance_m,
                cihaz_id=cihaz_id, kullanici_araci=user_agent, ip_adresi=client_ip
            )
            return jsonify({
                "success": False,
                "message": f"Çalışma bölgesinin dışındasınız. Şube merkezine uzaklığınız: {int(round(distance_m))} metre."
            }), 400

        # 5. Duplicate consecutive check (IK-04)
        last_rec = queries.get_last_vardiya_kayit_for_calisan(db, calisan.TC_No)
        is_duplicate = (last_rec is not None and last_rec.islem_tipi == islem_tipi)

        if is_duplicate and not confirm_mukerrer:
            action_tr = "Giriş" if islem_tipi == "GIRIS" else "Çıkış"
            return jsonify({
                "requires_confirmation": True,
                "message": f"Son işleminiz de {action_tr} olarak kaydedilmiş. Yine de devam etmek istiyor musunuz?"
            }), 200

        # Bind device if not bound yet
        if not calisan.Cihaz_Kaydi:
            calisan.Cihaz_Kaydi = cihaz_id
            db.commit()

        # 6. Create shift record
        kayit = queries.create_mobil_vardiya_kayit(
            db=db,
            calisan_tc=calisan.TC_No,
            sube_id=sube_id,
            barkod_id=barkod.id,
            islem_tipi=islem_tipi,
            istemci_zamani=istemci_zamani,
            enlem=enlem_val,
            boylam=boylam_val,
            konum_dogrulugu_m=accuracy_val,
            bolge_mesafesi_m=distance_m,
            cihaz_id=cihaz_id,
            kullanici_araci=user_agent,
            platform=platform,
            ekran=ekran,
            ip_adresi=client_ip,
            mukerrer_uyari=(is_duplicate and confirm_mukerrer)
        )

        time_str = kayit.kayit_zamani.strftime("%H:%M:%S")
        action_name = "Giriş" if islem_tipi == "GIRIS" else "Çıkış"
        return jsonify({
            "success": True,
            "message": f"{action_name} kaydedildi. Saat: {time_str}",
            "kayit_id": kayit.id,
            "kayit_zamani": kayit.kayit_zamani.isoformat(),
            "mesafe_m": round(distance_m, 1)
        }), 201

    except Exception as e:
        return jsonify({"success": False, "message": f"Sunucu hatası: {str(e)}"}), 500
    finally:
        db.close()


# --- 3. Vardiya Çizelgesi Endpoints (Protected with #76 and #77) ---

@hr_bp.route("/vardiya-cizelgesi", methods=["GET"])
@auth_required
def list_vardiya_cizelgesi():
    """
    List shift records with filtering & pagination (#76).
    Filters: start_date, end_date, sube_id, calisan_tc, islem_tipi, kaynak, show_deleted.
    """
    db = get_db_session()
    try:
        user = request.user
        if not _check_user_permission(db, user, "Vardiya Çizelgesi Ekranı Görüntüleme"):
            return jsonify({"error": "Vardiya Çizelgesi Ekranı Görüntüleme yetkiniz bulunmamaktadır."}), 403

        start_date_str = request.args.get("start_date")
        end_date_str = request.args.get("end_date")
        sube_id = request.args.get("sube_id", type=int)
        calisan_tc = request.args.get("calisan_tc")
        islem_tipi = request.args.get("islem_tipi")
        kaynak = request.args.get("kaynak")
        show_deleted = request.args.get("show_deleted", "false").lower() == "true"
        page = request.args.get("page", 1, type=int)
        per_page = min(request.args.get("per_page", 50, type=int), 200)

        start_date = datetime.strptime(start_date_str, "%Y-%m-%d").date() if start_date_str else None
        end_date = datetime.strptime(end_date_str, "%Y-%m-%d").date() if end_date_str else None

        records, total_count = queries.get_vardiya_kayitlar(
            db, start_date=start_date, end_date=end_date, sube_id=sube_id,
            calisan_tc=calisan_tc, islem_tipi=islem_tipi, kaynak=kaynak,
            show_deleted=show_deleted, page=page, per_page=per_page
        )

        items = []
        for r in records:
            items.append({
                "id": r.id,
                "calisan_tc": r.calisan_id,
                "calisan_adi": f"{r.calisan.Adi} {r.calisan.Soyadi}" if r.calisan else r.calisan_id,
                "sube_id": r.sube_id,
                "sube_adi": r.sube.Sube_Adi if r.sube else "",
                "islem_tipi": r.islem_tipi,
                "kaynak": r.kaynak,
                "kayit_zamani": r.kayit_zamani.strftime("%d.%m.%Y %H:%M:%S") if r.kayit_zamani else "",
                "kayit_tarihi_raw": r.kayit_zamani.strftime("%Y-%m-%dT%H:%M") if r.kayit_zamani else "",
                "enlem": float(r.enlem) if r.enlem is not None else None,
                "boylam": float(r.boylam) if r.boylam is not None else None,
                "konum_dogrulugu_m": float(r.konum_dogrulugu_m) if r.konum_dogrulugu_m is not None else None,
                "bolge_mesafesi_m": float(r.bolge_mesafesi_m) if r.bolge_mesafesi_m is not None else None,
                "cihaz_id": r.cihaz_id,
                "mukerrer_uyari": bool(r.mukerrer_uyari),
                "silindi": bool(r.silindi)
            })

        return jsonify({
            "items": items,
            "total_count": total_count,
            "page": page,
            "per_page": per_page,
            "total_pages": math.ceil(total_count / per_page) if total_count > 0 else 1
        }), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        db.close()


@hr_bp.route("/vardiya-cizelgesi/export-data", methods=["GET"])
@auth_required
def get_vardiya_cizelgesi_export_data():
    """Get all filtered records for Excel/Mail/Print (#33, #34, #74)."""
    db = get_db_session()
    try:
        user = request.user
        if not _check_user_permission(db, user, "Vardiya Çizelgesi Ekranı Görüntüleme"):
            return jsonify({"error": "Yetkiniz bulunmamaktadır."}), 403

        start_date_str = request.args.get("start_date")
        end_date_str = request.args.get("end_date")
        sube_id = request.args.get("sube_id", type=int)
        calisan_tc = request.args.get("calisan_tc")
        islem_tipi = request.args.get("islem_tipi")
        kaynak = request.args.get("kaynak")

        start_date = datetime.strptime(start_date_str, "%Y-%m-%d").date() if start_date_str else None
        end_date = datetime.strptime(end_date_str, "%Y-%m-%d").date() if end_date_str else None

        records = queries.get_all_vardiya_kayitlar_for_export(
            db, start_date=start_date, end_date=end_date, sube_id=sube_id,
            calisan_tc=calisan_tc, islem_tipi=islem_tipi, kaynak=kaynak
        )

        items = []
        for r in records:
            items.append({
                "id": r.id,
                "calisan_adi": f"{r.calisan.Adi} {r.calisan.Soyadi}" if r.calisan else r.calisan_id,
                "sube_adi": r.sube.Sube_Adi if r.sube else "",
                "islem_tipi": "Giriş" if r.islem_tipi == "GIRIS" else "Çıkış",
                "kaynak": "Telefon" if r.kaynak == "TELEFON" else "Manuel",
                "kayit_zamani": r.kayit_zamani.strftime("%d.%m.%Y %H:%M:%S") if r.kayit_zamani else "",
                "enlem": float(r.enlem) if r.enlem is not None else "",
                "boylam": float(r.boylam) if r.boylam is not None else "",
                "konum_dogrulugu_m": float(r.konum_dogrulugu_m) if r.konum_dogrulugu_m is not None else "",
                "bolge_mesafesi_m": float(r.bolge_mesafesi_m) if r.bolge_mesafesi_m is not None else "",
                "cihaz_id": r.cihaz_id or "",
                "mukerrer_uyari": "Evet" if r.mukerrer_uyari else "Hayır"
            })
        return jsonify(items), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        db.close()


@hr_bp.route("/vardiya-cizelgesi", methods=["POST"])
@auth_required
def create_manuel_vardiya():
    """Create manual shift entry (Requires #77 and justification)."""
    db = get_db_session()
    try:
        user = request.user
        if not _check_user_permission(db, user, "Vardiya Güncelleme Yetkisi"):
            return jsonify({"error": "Manuel kayıt ekleme yetkiniz bulunmamaktadır (Yetki #77)."}), 403

        data = request.get_json() or {}
        calisan_tc = data.get("calisan_tc")
        sube_id = data.get("sube_id")
        islem_tipi = data.get("islem_tipi")
        kayit_zamani_str = data.get("kayit_zamani")
        gerekce = (data.get("gerekce") or "").strip()

        if not calisan_tc or not sube_id or not islem_tipi or not kayit_zamani_str or not gerekce:
            return jsonify({"error": "Tüm alanlar ve gerekçe açıklaması zorunludur."}), 400

        try:
            kayit_zamani = datetime.fromisoformat(kayit_zamani_str)
        except Exception:
            return jsonify({"error": "Geçersiz tarih/saat formatı."}), 400

        kayit = queries.create_manuel_vardiya_kayit(
            db=db,
            calisan_tc=calisan_tc,
            sube_id=sube_id,
            islem_tipi=islem_tipi,
            kayit_zamani=kayit_zamani,
            olusturan_id=user.Kullanici_ID,
            gerekce=gerekce
        )

        return jsonify({
            "message": "Manuel vardiya kaydı başarıyla oluşturuldu.",
            "id": kayit.id
        }), 201
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        db.close()


@hr_bp.route("/vardiya-cizelgesi/<int:kayit_id>", methods=["PUT"])
@auth_required
def update_vardiya(kayit_id):
    """Update shift record (Requires #77 and justification)."""
    db = get_db_session()
    try:
        user = request.user
        if not _check_user_permission(db, user, "Vardiya Güncelleme Yetkisi"):
            return jsonify({"error": "Vardiya güncelleme yetkiniz bulunmamaktadır (Yetki #77)."}), 403

        data = request.get_json() or {}
        islem_tipi = data.get("islem_tipi")
        kayit_zamani_str = data.get("kayit_zamani")
        gerekce = (data.get("gerekce") or "").strip()

        if not islem_tipi or not kayit_zamani_str or not gerekce:
            return jsonify({"error": "İşlem tipi, kayıt zamanı ve gerekçe açıklaması zorunludur."}), 400

        try:
            kayit_zamani = datetime.fromisoformat(kayit_zamani_str)
        except Exception:
            return jsonify({"error": "Geçersiz tarih/saat formatı."}), 400

        kayit = queries.update_vardiya_kayit(
            db=db,
            kayit_id=kayit_id,
            islem_tipi=islem_tipi,
            kayit_zamani=kayit_zamani,
            kullanici_id=user.Kullanici_ID,
            gerekce=gerekce
        )
        if not kayit:
            return jsonify({"error": "Vardiya kaydı bulunamadı veya silinmiş."}), 404

        return jsonify({"message": "Vardiya kaydı başarıyla güncellendi."}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        db.close()


@hr_bp.route("/vardiya-cizelgesi/<int:kayit_id>", methods=["DELETE"])
@auth_required
def delete_vardiya(kayit_id):
    """Soft delete shift record (Requires #77 and justification)."""
    db = get_db_session()
    try:
        user = request.user
        if not _check_user_permission(db, user, "Vardiya Güncelleme Yetkisi"):
            return jsonify({"error": "Vardiya silme yetkiniz bulunmamaktadır (Yetki #77)."}), 403

        data = request.get_json() or {}
        gerekce = (data.get("gerekce") or "").strip()
        if not gerekce:
            return jsonify({"error": "Silme gerekçesi belirtilmesi zorunludur."}), 400

        kayit = queries.soft_delete_vardiya_kayit(
            db=db,
            kayit_id=kayit_id,
            kullanici_id=user.Kullanici_ID,
            gerekce=gerekce
        )
        if not kayit:
            return jsonify({"error": "Vardiya kaydı bulunamadı veya zaten silinmiş."}), 404

        return jsonify({"message": "Vardiya kaydı başarıyla silindi."}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        db.close()


# --- 4. Vardiya Kayıt Log Raporu Endpoints (#81) ---

@hr_bp.route("/vardiya-kayit-log-raporu", methods=["GET"])
@auth_required
def list_vardiya_kayit_log_raporu():
    """
    List vardiya kayit audit logs with filtering & pagination (#81).
    Filters: start_date, end_date, islem, kullanici_id, kayit_id.
    """
    db = get_db_session()
    try:
        user = request.user
        if not _check_user_permission(db, user, "Vardiya Kayit Log Raporu Görüntüleme"):
            return jsonify({"error": "Vardiya Kayit Log Raporu Görüntüleme yetkiniz bulunmamaktadır."}), 403

        start_date_str = request.args.get("start_date")
        end_date_str = request.args.get("end_date")
        islem = request.args.get("islem")
        kullanici_id = request.args.get("kullanici_id", type=int)
        kayit_id = request.args.get("kayit_id", type=int)
        page = request.args.get("page", 1, type=int)
        per_page = min(request.args.get("per_page", 50, type=int), 200)

        start_date = datetime.strptime(start_date_str, "%Y-%m-%d").date() if start_date_str else None
        end_date = datetime.strptime(end_date_str, "%Y-%m-%d").date() if end_date_str else None

        records, total_count = queries.get_vardiya_kayit_loglar(
            db, start_date=start_date, end_date=end_date,
            islem=islem, kullanici_id=kullanici_id, kayit_id=kayit_id,
            page=page, per_page=per_page
        )

        from app.models import Calisan

        items = []
        for r in records:
            kullanici_ad = r.kullanici.Adi_Soyadi if (r.kullanici and r.kullanici.Adi_Soyadi) else (r.kullanici.Kullanici_Adi if r.kullanici else str(r.kullanici_id))
            
            # Extract calisan_id from record or json diff
            calisan_ad_soyad = "-"
            calisan_tc = None
            if r.kayit and r.kayit.calisan:
                calisan_ad_soyad = f"{r.kayit.calisan.Adi} {r.kayit.calisan.Soyadi}"
                calisan_tc = r.kayit.calisan_id
            else:
                # Fallback to json values
                if r.yeni_deger and isinstance(r.yeni_deger, dict) and r.yeni_deger.get("calisan_id"):
                    calisan_tc = str(r.yeni_deger["calisan_id"])
                elif r.eski_deger and isinstance(r.eski_deger, dict) and r.eski_deger.get("calisan_id"):
                    calisan_tc = str(r.eski_deger["calisan_id"])
                
                if calisan_tc:
                    c = db.get(Calisan, calisan_tc)
                    if c:
                        calisan_ad_soyad = f"{c.Adi} {c.Soyadi}"
                    else:
                        calisan_ad_soyad = calisan_tc

            items.append({
                "id": r.id,
                "kayit_id": r.kayit_id,
                "islem": r.islem,
                "calisan_adi": calisan_ad_soyad,
                "calisan_tc": calisan_tc,
                "kullanici_id": r.kullanici_id,
                "kullanici_adi": kullanici_ad,
                "islem_zamani": r.islem_zamani.strftime("%d.%m.%Y %H:%M:%S") if r.islem_zamani else "",
                "gerekce": r.gerekce or "",
                "eski_deger": r.eski_deger,
                "yeni_deger": r.yeni_deger
            })

        return jsonify({
            "items": items,
            "total_count": total_count,
            "page": page,
            "per_page": per_page,
            "total_pages": math.ceil(total_count / per_page) if total_count > 0 else 1
        }), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        db.close()


@hr_bp.route("/vardiya-kayit-log-raporu/export-data", methods=["GET"])
@auth_required
def get_vardiya_kayit_log_export_data():
    """Get all filtered vardiya kayit audit logs for Excel/Mail/Print (#81)."""
    db = get_db_session()
    try:
        user = request.user
        if not _check_user_permission(db, user, "Vardiya Kayit Log Raporu Görüntüleme"):
            return jsonify({"error": "Yetkiniz bulunmamaktadır."}), 403

        start_date_str = request.args.get("start_date")
        end_date_str = request.args.get("end_date")
        islem = request.args.get("islem")
        kullanici_id = request.args.get("kullanici_id", type=int)
        kayit_id = request.args.get("kayit_id", type=int)

        start_date = datetime.strptime(start_date_str, "%Y-%m-%d").date() if start_date_str else None
        end_date = datetime.strptime(end_date_str, "%Y-%m-%d").date() if end_date_str else None

        records = queries.get_all_vardiya_kayit_loglar_for_export(
            db, start_date=start_date, end_date=end_date,
            islem=islem, kullanici_id=kullanici_id, kayit_id=kayit_id
        )

        from app.models import Calisan

        items = []
        for r in records:
            kullanici_ad = r.kullanici.Adi_Soyadi if (r.kullanici and r.kullanici.Adi_Soyadi) else (r.kullanici.Kullanici_Adi if r.kullanici else str(r.kullanici_id))
            
            calisan_ad_soyad = "-"
            calisan_tc = None
            if r.kayit and r.kayit.calisan:
                calisan_ad_soyad = f"{r.kayit.calisan.Adi} {r.kayit.calisan.Soyadi}"
                calisan_tc = r.kayit.calisan_id
            else:
                if r.yeni_deger and isinstance(r.yeni_deger, dict) and r.yeni_deger.get("calisan_id"):
                    calisan_tc = str(r.yeni_deger["calisan_id"])
                elif r.eski_deger and isinstance(r.eski_deger, dict) and r.eski_deger.get("calisan_id"):
                    calisan_tc = str(r.eski_deger["calisan_id"])
                if calisan_tc:
                    c = db.get(Calisan, calisan_tc)
                    if c:
                        calisan_ad_soyad = f"{c.Adi} {c.Soyadi}"
                    else:
                        calisan_ad_soyad = calisan_tc

            items.append({
                "id": r.id,
                "kayit_id": r.kayit_id,
                "calisan_adi": calisan_ad_soyad,
                "islem": r.islem,
                "kullanici_adi": kullanici_ad,
                "islem_zamani": r.islem_zamani.strftime("%d.%m.%Y %H:%M:%S") if r.islem_zamani else "",
                "gerekce": r.gerekce or ""
            })
        return jsonify(items), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        db.close()

