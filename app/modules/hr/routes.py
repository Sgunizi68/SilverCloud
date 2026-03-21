"""
HR Domain Routes
CRUD endpoints for Employee, Attendance, and Leave/Advance management.
All endpoints protected by @auth_required decorator.
"""

from functools import wraps
from flask import Blueprint, request, jsonify
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
            net_maas=float(data.get("Net_Maas")) if "Net_Maas" in data else None,
            sigorta_giris=data.get("Sigorta_Giris"),
            sigorta_cikis=data.get("Sigorta_Cikis"),
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
            aktif_pasif=data.get("Aktif_Pasif")
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
            aktif_pasif=data.get("Aktif_Pasif", True)
        )
        db.close()
        
        result = {
            "Secim_ID": new_secim.Secim_ID,
            "Secim": new_secim.Secim,
            "Degeri": float(new_secim.Degeri),
            "Renk_Kodu": new_secim.Renk_Kodu,
            "Aktif_Pasif": new_secim.Aktif_Pasif,
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
            aktif_pasif=data.get("Aktif_Pasif")
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
        
        db = get_db_session()
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
            ilk_soyadi=data["Ilk_Soyadi"],
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
