"""
Invoicing Domain Routes
CRUD endpoints for Faturalar, Odemeler, Nakit, Gelir, and related entities.
All endpoints protected by @auth_required decorator.
"""

from functools import wraps
from datetime import date, datetime
from flask import Blueprint, request, jsonify
from app.common.database import get_db_session
from app.modules.invoicing import queries
from app.modules.reference import queries as ref_queries

invoicing_bp = Blueprint("invoicing", __name__, url_prefix="/api/v1")

# Late-binding auth_required to avoid circular import
def auth_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        from app.modules.auth.routes import auth_required as _auth_required
        return _auth_required(f)(*args, **kwargs)
    return decorated


# ============================================================================
# EFATURA (E-INVOICES) ENDPOINTS
# ============================================================================

@invoicing_bp.route("/efaturalar", methods=["GET"])
@auth_required
def list_efaturalar():
    """Get all e-invoices with optional filtering."""
    try:
        skip = request.args.get("skip", 0, type=int)
        limit = request.args.get("limit", 500, type=int)
        sube_id = request.args.get("sube_id", None, type=int)
        kategori_id = request.args.get("kategori_id", None, type=int)
        status = request.args.get("status", None, type=str)
        donem = request.args.get("donem", None, type=int)
        giden_fatura = request.args.get("giden_fatura", None)
        if giden_fatura is not None:
            giden_fatura = giden_fatura.lower() == 'true'
        search = request.args.get("search", None, type=str)
        
        db = get_db_session()
        
        # Determine permission to view Gizli/Ozel records
        from flask import session
        user_id = session.get("user_id")
        can_view_gizli = False
        if user_id:
            from app.modules.auth.queries import get_user_roles, has_permission
            roles = get_user_roles(db, user_id)
            is_admin = 'admin' in [r.lower() for r in roles]
            has_gizli_permission = has_permission(db, user_id, "Gizli Kategori Veri Erişimi")
            can_view_gizli = is_admin or has_gizli_permission

        efaturalar = queries.get_efaturalar(
            db, skip, limit, sube_id, kategori_id, status, donem, giden_fatura, search,
            can_view_gizli=can_view_gizli
        )
        db.close()
        
        result = [
            {
                "Fatura_ID": e.Fatura_ID,
                "Sube_ID": e.Sube_ID,
                "Kategori_ID": e.Kategori_ID,
                "Fatura_Numarasi": e.Fatura_Numarasi,
                "Alici_Unvani": e.Alici_Unvani,
                "Alici_VKN_TCKN": e.Alici_VKN_TCKN,
                "Tutar": float(e.Tutar),
                "Fatura_Tarihi": e.Fatura_Tarihi.isoformat() if e.Fatura_Tarihi else None,
                "Donem": e.Donem,
                "Ozel": e.Ozel,
                "Gunluk_Harcama": e.Gunluk_Harcama,
                "Giden_Fatura": e.Giden_Fatura,
                "Kayit_Tarihi": e.Kayit_Tarihi.isoformat() if e.Kayit_Tarihi else None,
                "Aciklama": e.Aciklama,
            }
            for e in efaturalar
        ]
        
        return jsonify(result), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@invoicing_bp.route("/efaturalar/<int:efatura_id>", methods=["GET"])
@auth_required
def get_efatura(efatura_id):
    """Get e-invoice by ID."""
    try:
        db = get_db_session()
        efatura = queries.get_efatura_by_id(db, efatura_id)
        db.close()
        
        if not efatura:
            return jsonify({"error": "EFatura not found"}), 404
        
        result = {
            "Fatura_ID": efatura.Fatura_ID,
            "Sube_ID": efatura.Sube_ID,
            "Kategori_ID": efatura.Kategori_ID,
            "Fatura_Numarasi": efatura.Fatura_Numarasi,
            "Tutar": float(efatura.Tutar),
            "Fatura_Tarihi": efatura.Fatura_Tarihi.isoformat() if efatura.Fatura_Tarihi else None,
            "Alici_Unvani": efatura.Alici_Unvani,
            "Donem": efatura.Donem,
            "Ozel": efatura.Ozel,
            "Gunluk_Harcama": efatura.Gunluk_Harcama,
            "Aciklama": efatura.Aciklama,
        }
        
        return jsonify(result), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@invoicing_bp.route("/efaturalar/fatura-no/<string:fatura_no>", methods=["GET"])
@auth_required
def get_efatura_by_no(fatura_no):
    """Get e-invoice by Fatura_Numarasi."""
    try:
        db = get_db_session()
        efatura = queries.get_efatura_by_no(db, fatura_no)
        db.close()
        
        if not efatura:
            return jsonify({"error": "EFatura not found"}), 404
        
        result = {
            "Fatura_ID": efatura.Fatura_ID,
            "Sube_ID": efatura.Sube_ID,
            "Kategori_ID": efatura.Kategori_ID,
            "Fatura_Numarasi": efatura.Fatura_Numarasi,
            "Tutar": float(efatura.Tutar),
            "Fatura_Tarihi": efatura.Fatura_Tarihi.isoformat() if efatura.Fatura_Tarihi else None,
            "Alici_Unvani": efatura.Alici_Unvani,
            "Donem": efatura.Donem,
            "Ozel": efatura.Ozel,
            "Gunluk_Harcama": efatura.Gunluk_Harcama,
            "Aciklama": efatura.Aciklama,
        }
        
        return jsonify(result), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@invoicing_bp.route("/efaturalar", methods=["POST"])
@auth_required
def create_efatura():
    """Create a new e-invoice with split-friendly fields."""
    try:
        from datetime import datetime
        data = request.get_json()
        required = ["Sube_ID", "Fatura_Numarasi", "Tutar"]
        for field in required:
            if field not in data:
                return jsonify({"error": f"{field} required"}), 400
        
        # Parse dates and numbers to be safe
        f_tarihi = data.get("Fatura_Tarihi")
        if f_tarihi and isinstance(f_tarihi, str):
            f_tarihi = datetime.strptime(f_tarihi, "%Y-%m-%d").date()
            
        k_id = data.get("Kategori_ID")
        if k_id is not None: k_id = int(k_id)
        
        donem = data.get("Donem")
        if donem is not None: donem = int(donem)

        db = get_db_session()
        new_efatura = queries.create_efatura(
            db,
            sube_id=int(data["Sube_ID"]),
            kategori_id=k_id,
            fatura_no=data["Fatura_Numarasi"],
            fatura_tutari=float(data["Tutar"]),
            fatura_tarihi=f_tarihi,
            alici_unvani=data.get("Alici_Unvani"),
            donem=donem,
            aciklama=data.get("Aciklama"),
            ozel=bool(data.get("Ozel", False)),
            gunluk=bool(data.get("Gunluk_Harcama", False)),
            giden=bool(data.get("Giden_Fatura", False))
        )
        db.close()
        
        return jsonify({"Fatura_ID": new_efatura.Fatura_ID}), 201
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@invoicing_bp.route("/efaturalar/<int:efatura_id>", methods=["PUT"])
@auth_required
def update_efatura(efatura_id):
    """Update e-invoice."""
    try:
        data = request.get_json()
        
        db = get_db_session()
        
        # Parse numeric/bool fields
        k_id = data.get("Kategori_ID")
        if k_id is not None: k_id = int(k_id)
        
        donem = data.get("Donem")
        if donem is not None: donem = int(donem)
        
        updated_efatura = queries.update_efatura(
            db,
            efatura_id,
            fatura_no=data.get("Fatura_Numarasi") or data.get("Fatura_No"),
            fatura_tutari=float(data.get("Tutar")) if "Tutar" in data else (float(data.get("Fatura_Tutari")) if "Fatura_Tutari" in data else None),
            kategori_id=k_id,
            donem=donem,
            ozel=data.get("Ozel"),
            gunluk_harcama=data.get("Gunluk_Harcama"),
            aciklama=data.get("Aciklama")
        )
        db.close()
        
        if not updated_efatura:
            return jsonify({"error": "EFatura not found"}), 404
        
        result = {
            "Fatura_ID": updated_efatura.Fatura_ID,
            "Sube_ID": updated_efatura.Sube_ID,
            "Kategori_ID": updated_efatura.Kategori_ID,
            "Fatura_Numarasi": updated_efatura.Fatura_Numarasi,
            "Alici_Unvani": updated_efatura.Alici_Unvani,
            "Tutar": float(updated_efatura.Tutar),
            "Fatura_Tarihi": updated_efatura.Fatura_Tarihi.isoformat() if updated_efatura.Fatura_Tarihi else None,
            "Donem": updated_efatura.Donem,
            "Ozel": updated_efatura.Ozel,
            "Gunluk_Harcama": updated_efatura.Gunluk_Harcama,
            "Giden_Fatura": updated_efatura.Giden_Fatura,
            "Kayit_Tarihi": updated_efatura.Kayit_Tarihi.isoformat() if updated_efatura.Kayit_Tarihi else None,
            "Aciklama": updated_efatura.Aciklama,
        }
        
        return jsonify(result), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@invoicing_bp.route("/efaturalar/<int:efatura_id>", methods=["DELETE"])
@auth_required
def delete_efatura(efatura_id):
    """Delete e-invoice."""
    try:
        db = get_db_session()
        deleted = queries.delete_efatura(db, efatura_id)
        db.close()
        
        if not deleted:
            return jsonify({"error": "EFatura not found"}), 404
        
        return jsonify({"message": "EFatura deleted"}), 204
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@invoicing_bp.route("/efaturalar/bulk", methods=["POST"])
@auth_required
def upload_efaturalar_bulk():
    """Bulk upload e-invoices."""
    try:
        data = request.get_json()
        if not data or "efaturalar" not in data:
            return jsonify({"error": "efaturalar list required"}), 400
        
        efaturalar = data["efaturalar"]
        if not isinstance(efaturalar, list):
            return jsonify({"error": "efaturalar must be a list"}), 400
            
        db = get_db_session()
        result = queries.create_efatura_bulk(db, efaturalar)
        db.close()
        
        return jsonify(result), 201
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@invoicing_bp.route("/fatura-bolme/bolunmus-faturalar", methods=["GET"])
@auth_required
def list_bolunmus_faturalar():
    """Get split e-invoices grouped by parent invoice."""
    try:
        donem = request.args.get("donem", None, type=int)
        db = get_db_session()
        result = queries.get_bolunmus_faturalar(db, donem)
        db.close()
        
        # Serialize types for JSON
        for row in result:
            for key in ("Ana_Tutar", "Tutar"):
                if row.get(key) is not None:
                    row[key] = float(row[key])
            for key in ("Fatura_Tarihi", "Ana_Fatura_Tarihi"):
                if row.get(key) is not None:
                    v = row[key]
                    row[key] = v.isoformat() if hasattr(v, "isoformat") else str(v)
            # Donem may be int or string; normalize
            for key in ("Donem", "Ana_Donem"):
                if row.get(key) is not None:
                    row[key] = str(int(row[key]))
                    
        return jsonify(result), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500



# ============================================================================
# B2B EKSTRE ENDPOINTS
# ============================================================================

@invoicing_bp.route("/b2b-ekstreler/bulk", methods=["POST"])
@auth_required
def upload_b2b_ekstreler_bulk():
    """Bulk upload B2B ekstre (statements)."""
    try:
        data = request.get_json()
        if not data or "ekstreler" not in data:
            return jsonify({"error": "ekstreler list required"}), 400
        
        ekstreler = data["ekstreler"]
        if not isinstance(ekstreler, list):
            return jsonify({"error": "ekstreler must be a list"}), 400
            
        db = get_db_session()
        result = queries.create_b2b_ekstre_bulk(db, ekstreler)
        db.close()
        
        return jsonify(result), 201
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# ============================================================================
# ODEME (PAYMENT) ENDPOINTS
# ============================================================================

@invoicing_bp.route("/odemeler", methods=["GET"])
@auth_required
def get_odemeler_list():
    """Get payments with filters for Category Assignment screen."""
    try:
        sube_id = request.args.get("sube_id", type=int)
        donem = request.args.get("donem", type=int)
        kategori_id = request.args.get("kategori_id", type=int)
        search_term = request.args.get("search", type=str)
        sadece_kategorisiz = request.args.get("sadece_kategorisiz", "false").lower() == "true"
        skip = request.args.get("skip", 0, type=int)
        limit = min(request.args.get("limit", 5000, type=int), 10000)
        
        db = get_db_session()
        odemeler = queries.get_odemeler(
            db, 
            sube_id=sube_id, 
            donem=donem, 
            kategori_id=kategori_id,
            search_term=search_term,
            sadece_kategorisiz=sadece_kategorisiz,
            skip=skip, 
            limit=limit
        )
        db.close()
        
        result = [
            {
                "Odeme_ID": o.Odeme_ID,
                "Tip": o.Tip,
                "Hesap_Adi": o.Hesap_Adi,
                "Tarih": o.Tarih.isoformat() if o.Tarih else None,
                "Aciklama": o.Aciklama,
                "Tutar": float(o.Tutar) if o.Tutar else 0.0,
                "Kategori_ID": o.Kategori_ID,
                "Donem": o.Donem,
                "Sube_ID": o.Sube_ID
            }
            for o in odemeler
        ]
        
        return jsonify(result), 200
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500


@invoicing_bp.route("/odemeler/<int:odeme_id>", methods=["PUT"])
@auth_required
def update_odeme_endpoint(odeme_id):
    """Update payment inline (category or period)."""
    try:
        data = request.get_json()
        
        kategori_id = data.get("Kategori_ID")
        donem = data.get("Donem")
        kategori_clear = data.get("Kategori_Clear", False)
        donem_clear = data.get("Donem_Clear", False)
        
        db = get_db_session()
        updated_odeme = queries.update_odeme(
            db, 
            odeme_id, 
            kategori_id=kategori_id, 
            donem=donem,
            kategori_clear=kategori_clear,
            donem_clear=donem_clear
        )
        db.close()
        
        if not updated_odeme:
            return jsonify({"error": "Payment not found"}), 404
            
        return jsonify({
            "message": "Payment updated successfully",
            "Odeme": {
                "Odeme_ID": updated_odeme.Odeme_ID,
                "Kategori_ID": updated_odeme.Kategori_ID,
                "Donem": updated_odeme.Donem
            }
        }), 200
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500



@invoicing_bp.route("/odemeler/bulk", methods=["POST"])
@auth_required
def create_odeme_bulk_api():
    """Bulk create payments from uploaded data."""
    try:
        data = request.get_json()
        if not data or "odemeler" not in data:
            return jsonify({"error": "odemeler list required"}), 400
            
        db = get_db_session()
        result = queries.create_odeme_bulk(db, data["odemeler"])
        db.close()
        
        return jsonify(result), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# ============================================================================
# NAKIT (CASH) ENDPOINTS
# ============================================================================

@invoicing_bp.route("/nakit", methods=["GET"])
@auth_required
def list_nakit():
    """Get all cash transactions."""
    try:
        skip = request.args.get("skip", 0, type=int)
        limit = min(request.args.get("limit", 100, type=int), 1000)
        sube_id = request.args.get("sube_id", None, type=int)
        kategori_id = request.args.get("kategori_id", None, type=int)
        
        db = get_db_session()
        nakit_list = queries.get_nakit_list(db, skip, limit, sube_id, kategori_id)
        db.close()
        
        result = [
            {
                "Nakit_ID": n.Nakit_ID,
                "Sube_ID": n.Sube_ID,
                "Kategori_ID": n.Kategori_ID,
                "Islem_Tutari": float(n.Islem_Tutari),
                "Islem_Sekli": n.Islem_Sekli,
                "Islem_Tarihi": n.Islem_Tarihi.isoformat(),
                "Aciklama": n.Aciklama,
            }
            for n in nakit_list
        ]
        
        return jsonify(result), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@invoicing_bp.route("/nakit/<int:nakit_id>", methods=["GET"])
@auth_required
def get_nakit(nakit_id):
    """Get cash transaction by ID."""
    try:
        db = get_db_session()
        nakit = queries.get_nakit_by_id(db, nakit_id)
        db.close()
        
        if not nakit:
            return jsonify({"error": "Nakit not found"}), 404
        
        result = {
            "Nakit_ID": nakit.Nakit_ID,
            "Sube_ID": nakit.Sube_ID,
            "Kategori_ID": nakit.Kategori_ID,
            "Islem_Tutari": float(nakit.Islem_Tutari),
            "Islem_Sekli": nakit.Islem_Sekli,
            "Islem_Tarihi": nakit.Islem_Tarihi.isoformat(),
            "Aciklama": nakit.Aciklama,
        }
        
        return jsonify(result), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@invoicing_bp.route("/nakit", methods=["POST"])
@auth_required
def create_nakit():
    """Create a new cash transaction."""
    try:
        data = request.get_json()
        if not data or "Sube_ID" not in data or "Kategori_ID" not in data or "Islem_Tutari" not in data or "Islem_Sekli" not in data:
            return jsonify({"error": "Sube_ID, Kategori_ID, Islem_Tutari, and Islem_Sekli required"}), 400
        
        db = get_db_session()
        new_nakit = queries.create_nakit(
            db,
            sube_id=data["Sube_ID"],
            kategori_id=data["Kategori_ID"],
            islem_tutari=float(data["Islem_Tutari"]),
            islem_sekli=data["Islem_Sekli"],
            islem_tarihi=data.get("Islem_Tarihi"),
            aciklama=data.get("Aciklama")
        )
        db.close()
        
        result = {
            "Nakit_ID": new_nakit.Nakit_ID,
            "Sube_ID": new_nakit.Sube_ID,
            "Kategori_ID": new_nakit.Kategori_ID,
            "Islem_Tutari": float(new_nakit.Islem_Tutari),
            "Islem_Sekli": new_nakit.Islem_Sekli,
            "Islem_Tarihi": new_nakit.Islem_Tarihi.isoformat(),
            "Aciklama": new_nakit.Aciklama,
        }
        
        return jsonify(result), 201
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@invoicing_bp.route("/nakit/<int:nakit_id>", methods=["PUT"])
@auth_required
def update_nakit(nakit_id):
    """Update cash transaction."""
    try:
        data = request.get_json()
        
        db = get_db_session()
        updated_nakit = queries.update_nakit(
            db,
            nakit_id,
            islem_tutari=float(data.get("Islem_Tutari")) if "Islem_Tutari" in data else None,
            islem_sekli=data.get("Islem_Sekli"),
            aciklama=data.get("Aciklama")
        )
        db.close()
        
        if not updated_nakit:
            return jsonify({"error": "Nakit not found"}), 404
        
        result = {
            "Nakit_ID": updated_nakit.Nakit_ID,
            "Sube_ID": updated_nakit.Sube_ID,
            "Kategori_ID": updated_nakit.Kategori_ID,
            "Islem_Tutari": float(updated_nakit.Islem_Tutari),
            "Islem_Sekli": updated_nakit.Islem_Sekli,
            "Islem_Tarihi": updated_nakit.Islem_Tarihi.isoformat(),
            "Aciklama": updated_nakit.Aciklama,
        }
        
        return jsonify(result), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@invoicing_bp.route("/nakit/<int:nakit_id>", methods=["DELETE"])
@auth_required
def delete_nakit(nakit_id):
    """Delete cash transaction."""
    try:
        db = get_db_session()
        deleted = queries.delete_nakit(db, nakit_id)
        db.close()
        
        if not deleted:
            return jsonify({"error": "Nakit not found"}), 404
        
        return jsonify({"message": "Nakit deleted"}), 204
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# ============================================================================
# GELIR (INCOME) ENDPOINTS
# ============================================================================

@invoicing_bp.route("/gelirler", methods=["GET"])
@auth_required
def list_gelirler():
    """Get all incomes."""
    try:
        skip = request.args.get("skip", 0, type=int)
        limit = min(request.args.get("limit", 100, type=int), 1000)
        sube_id = request.args.get("sube_id", None, type=int)
        kategori_id = request.args.get("kategori_id", None, type=int)
        
        db = get_db_session()
        gelirler = queries.get_gelirler(db, skip, limit, sube_id, kategori_id)
        db.close()
        
        result = [
            {
                "Gelir_ID": g.Gelir_ID,
                "Sube_ID": g.Sube_ID,
                "Kategori_ID": g.Kategori_ID,
                "Gelir_Tutari": float(g.Gelir_Tutari),
                "Kayit_Tarihi": g.Kayit_Tarihi.isoformat(),
                "Aciklama": g.Aciklama,
            }
            for g in gelirler
        ]
        
        return jsonify(result), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@invoicing_bp.route("/gelirler/<int:gelir_id>", methods=["GET"])
@auth_required
def get_gelir(gelir_id):
    """Get income by ID."""
    try:
        db = get_db_session()
        gelir = queries.get_gelir_by_id(db, gelir_id)
        db.close()
        
        if not gelir:
            return jsonify({"error": "Gelir not found"}), 404
        
        result = {
            "Gelir_ID": gelir.Gelir_ID,
            "Sube_ID": gelir.Sube_ID,
            "Kategori_ID": gelir.Kategori_ID,
            "Gelir_Tutari": float(gelir.Gelir_Tutari),
            "Kayit_Tarihi": gelir.Kayit_Tarihi.isoformat(),
            "Aciklama": gelir.Aciklama,
        }
        
        return jsonify(result), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@invoicing_bp.route("/gelirler", methods=["POST"])
@auth_required
def create_gelir():
    """Create a new income."""
    try:
        data = request.get_json()
        if not data or "Sube_ID" not in data or "Kategori_ID" not in data or "Gelir_Tutari" not in data:
            return jsonify({"error": "Sube_ID, Kategori_ID, and Gelir_Tutari required"}), 400
        
        db = get_db_session()
        new_gelir = queries.create_gelir(
            db,
            sube_id=data["Sube_ID"],
            kategori_id=data["Kategori_ID"],
            gelir_tutari=float(data["Gelir_Tutari"]),
            kayit_tarihi=data.get("Kayit_Tarihi"),
            aciklama=data.get("Aciklama")
        )
        db.close()
        
        result = {
            "Gelir_ID": new_gelir.Gelir_ID,
            "Sube_ID": new_gelir.Sube_ID,
            "Kategori_ID": new_gelir.Kategori_ID,
            "Gelir_Tutari": float(new_gelir.Gelir_Tutari),
            "Kayit_Tarihi": new_gelir.Kayit_Tarihi.isoformat(),
            "Aciklama": new_gelir.Aciklama,
        }
        
        return jsonify(result), 201
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@invoicing_bp.route("/gelirler/<int:gelir_id>", methods=["PUT"])
@auth_required
def update_gelir(gelir_id):
    """Update income."""
    try:
        data = request.get_json()
        
        db = get_db_session()
        updated_gelir = queries.update_gelir(
            db,
            gelir_id,
            gelir_tutari=float(data.get("Gelir_Tutari")) if "Gelir_Tutari" in data else None,
            aciklama=data.get("Aciklama")
        )
        db.close()
        
        if not updated_gelir:
            return jsonify({"error": "Gelir not found"}), 404
        
        result = {
            "Gelir_ID": updated_gelir.Gelir_ID,
            "Sube_ID": updated_gelir.Sube_ID,
            "Kategori_ID": updated_gelir.Kategori_ID,
            "Gelir_Tutari": float(updated_gelir.Gelir_Tutari),
            "Kayit_Tarihi": updated_gelir.Kayit_Tarihi.isoformat(),
            "Aciklama": updated_gelir.Aciklama,
        }
        
        return jsonify(result), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@invoicing_bp.route("/gelirler/<int:gelir_id>", methods=["DELETE"])
@auth_required
def delete_gelir(gelir_id):
    """Delete income."""
    try:
        db = get_db_session()
        deleted = queries.delete_gelir(db, gelir_id)
        db.close()
        
        if not deleted:
            return jsonify({"error": "Gelir not found"}), 404
        
        return jsonify({"message": "Gelir deleted"}), 204
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# ============================================================================
# DIGER HARCAMA (OTHER EXPENSES) ENDPOINTS
# ============================================================================

import base64
from datetime import datetime

@invoicing_bp.route("/diger-harcamalar", methods=["GET"])
@auth_required
def list_diger_harcamalar():
    """Get all other expenses."""
    try:
        skip = request.args.get("skip", 0, type=int)
        limit = min(request.args.get("limit", 100, type=int), 1000)
        sube_id = request.args.get("sube_id", None, type=int)
        donem = request.args.get("donem", None, type=int)
        kategori_id = request.args.get("kategori_id", None, type=int)
        harcama_tipi = request.args.get("harcama_tipi", None, type=str)
        
        db = get_db_session()
        from app.modules.auth import queries as auth_queries
        user = request.user
        is_admin = (user.Kullanici_Adi and user.Kullanici_Adi.lower() == 'admin')
        if not is_admin:
            roles = auth_queries.get_user_roles(db, user.Kullanici_ID)
            is_admin = 'admin' in [r.lower() for r in roles]
        can_view_gizli = is_admin or auth_queries.has_permission(db, user.Kullanici_ID, "Gizli Kategori Veri Erişimi")
        
        harcamalar = queries.get_diger_harcamalar(db, skip, limit, sube_id, donem, kategori_id, harcama_tipi, can_view_gizli=can_view_gizli)
        db.close()
        
        result = []
        for h in harcamalar:
            item = {
                "Harcama_ID": h.Harcama_ID,
                "Alici_Adi": h.Alici_Adi,
                "Belge_Numarasi": h.Belge_Numarasi,
                "Belge_Tarihi": h.Belge_Tarihi.isoformat() if h.Belge_Tarihi else None,
                "Donem": h.Donem,
                "Tutar": float(h.Tutar) if h.Tutar else 0.0,
                "Kategori_ID": h.Kategori_ID,
                "Harcama_Tipi": h.Harcama_Tipi,
                "Gunluk_Harcama": h.Gunluk_Harcama,
                "Sube_ID": h.Sube_ID,
                "Aciklama": h.Açıklama,
                "Kayit_Tarihi": h.Kayit_Tarihi.isoformat() if h.Kayit_Tarihi else None,
                "Imaj_Adi": h.Imaj_Adi,
                "has_imaj": bool(h.Imaj)
            }
            # Optional: if you need to send image data back for viewing on row click
            if h.Imaj:
                item["Imaj_Base64"] = base64.b64encode(h.Imaj).decode('utf-8')
            result.append(item)
            
        return jsonify(result), 200
    except Exception as e:
        import traceback; traceback.print_exc()
        return jsonify({"error": str(e)}), 500


@invoicing_bp.route("/diger-harcamalar/<int:harcama_id>", methods=["GET"])
@auth_required
def get_diger_harcama(harcama_id):
    """Get other expense by ID."""
    try:
        db = get_db_session()
        from app.modules.auth import queries as auth_queries
        user = request.user
        is_admin = (user.Kullanici_Adi and user.Kullanici_Adi.lower() == 'admin')
        if not is_admin:
            roles = auth_queries.get_user_roles(db, user.Kullanici_ID)
            is_admin = 'admin' in [r.lower() for r in roles]
        can_view_gizli = is_admin or auth_queries.has_permission(db, user.Kullanici_ID, "Gizli Kategori Veri Erişimi")
        
        h = queries.get_diger_harcama_by_id(db, harcama_id, can_view_gizli=can_view_gizli)
        db.close()
        
        if not h:
            return jsonify({"error": "DigerHarcama not found"}), 404
        
        result = {
            "Harcama_ID": h.Harcama_ID,
            "Alici_Adi": h.Alici_Adi,
            "Belge_Numarasi": h.Belge_Numarasi,
            "Belge_Tarihi": h.Belge_Tarihi.isoformat() if h.Belge_Tarihi else None,
            "Donem": h.Donem,
            "Tutar": float(h.Tutar) if h.Tutar else 0.0,
            "Kategori_ID": h.Kategori_ID,
            "Harcama_Tipi": h.Harcama_Tipi,
            "Gunluk_Harcama": h.Gunluk_Harcama,
            "Sube_ID": h.Sube_ID,
            "Aciklama": h.Açıklama,
            "Kayit_Tarihi": h.Kayit_Tarihi.isoformat() if h.Kayit_Tarihi else None,
            "Imaj_Adi": h.Imaj_Adi,
            "has_imaj": bool(h.Imaj)
        }
        if h.Imaj:
            result["Imaj_Base64"] = base64.b64encode(h.Imaj).decode('utf-8')
            
        return jsonify(result), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@invoicing_bp.route("/diger-harcamalar", methods=["POST"])
@auth_required
def create_diger_harcama():
    """Create a new other expense with file upload."""
    try:
        # Expected inputs can come from form data (multipart)
        form_data = request.form
        
        if "Sube_ID" not in form_data or "Alici_Adi" not in form_data or "Tutar" not in form_data:
            return jsonify({"error": "Sube_ID, Alici_Adi, and Tutar required"}), 400
            
        tarih_str = form_data.get("Belge_Tarihi")
        try:
            belge_tarihi = datetime.strptime(tarih_str, '%Y-%m-%d').date() if tarih_str else datetime.now().date()
        except ValueError:
            belge_tarihi = datetime.now().date()
            
        data = {
            "Alici_Adi": form_data.get("Alici_Adi"),
            "Belge_Numarasi": form_data.get("Belge_Numarasi"),
            "Belge_Tarihi": belge_tarihi,
            "Donem": int(form_data.get("Donem", f"{belge_tarihi.year % 100:02d}{belge_tarihi.month:02d}")),
            "Tutar": float(form_data.get("Tutar")),
            "Kategori_ID": int(form_data.get("Kategori_ID")) if form_data.get("Kategori_ID") else None,
            "Harcama_Tipi": form_data.get("Harcama_Tipi"),
            "Gunluk_Harcama": form_data.get("Gunluk_Harcama") == 'true',
            "Sube_ID": int(form_data.get("Sube_ID")),
            "Açıklama": form_data.get("Aciklama")
        }
        
        # Handle file upload
        imaj = None
        imaj_adi = form_data.get("Imaj_Adi")
        if "image" in request.files:
            file = request.files["image"]
            if file and file.filename:
                imaj = file.read()
                if not imaj_adi:
                    imaj_adi = file.filename
                    
        db = get_db_session()
        new_harcama = queries.create_diger_harcama(db, data, imaj, imaj_adi)
        db.close()
        
        return jsonify({"message": "Diger Harcama created", "Harcama_ID": new_harcama.Harcama_ID}), 201
    except Exception as e:
        import traceback; traceback.print_exc()
        return jsonify({"error": str(e)}), 500


@invoicing_bp.route("/diger-harcamalar/<int:harcama_id>", methods=["PUT"])
@auth_required
def update_diger_harcama(harcama_id):
    """Update other expense."""
    try:
        form_data = request.form
        data = {}
        
        if "Alici_Adi" in form_data:
            data["Alici_Adi"] = form_data.get("Alici_Adi")
        if "Belge_Numarasi" in form_data:
            data["Belge_Numarasi"] = form_data.get("Belge_Numarasi")
        if "Belge_Tarihi" in form_data:
            try:
                data["Belge_Tarihi"] = datetime.strptime(form_data.get("Belge_Tarihi"), '%Y-%m-%d').date()
            except ValueError:
                pass
        if "Donem" in form_data:
            data["Donem"] = int(form_data.get("Donem"))
        if "Tutar" in form_data:
            data["Tutar"] = float(form_data.get("Tutar"))
        if "Kategori_ID" in form_data:
            data["Kategori_ID"] = int(form_data.get("Kategori_ID")) if form_data.get("Kategori_ID") else None
        if "Harcama_Tipi" in form_data:
            data["Harcama_Tipi"] = form_data.get("Harcama_Tipi")
        if "Gunluk_Harcama" in form_data:
            data["Gunluk_Harcama"] = form_data.get("Gunluk_Harcama") == 'true'
        if "Sube_ID" in form_data:
            data["Sube_ID"] = int(form_data.get("Sube_ID"))
        if "Aciklama" in form_data:
            data["Açıklama"] = form_data.get("Aciklama")

        imaj = None
        imaj_adi = form_data.get("Imaj_Adi")
        clear_image = False
        
        if "image" in request.files:
            file = request.files["image"]
            if file and file.filename:
                imaj = file.read()
                if not imaj_adi:
                    imaj_adi = file.filename
        elif imaj_adi == "":
            clear_image = True
            
        db = get_db_session()
        updated = queries.update_diger_harcama(db, harcama_id, data, imaj, imaj_adi, clear_image)
        db.close()
        
        if not updated:
            return jsonify({"error": "DigerHarcama not found"}), 404
            
        return jsonify({"message": "Diger Harcama updated"}), 200
    except Exception as e:
        import traceback; traceback.print_exc()
        return jsonify({"error": str(e)}), 500


@invoicing_bp.route("/diger-harcamalar/<int:harcama_id>", methods=["DELETE"])
@auth_required
def delete_diger_harcama(harcama_id):
    """Delete other expense."""
    try:
        db = get_db_session()
        deleted = queries.delete_diger_harcama(db, harcama_id)
        db.close()
        
        if not deleted:
            return jsonify({"error": "DigerHarcama not found"}), 404
        
        return jsonify({"message": "DigerHarcama deleted"}), 204
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# ============================================================================
# POSHAREKETLERİ (POS TRANSACTIONS) ENDPOINTS
# ============================================================================

@invoicing_bp.route("/pos-hareketleri", methods=["GET"])
@auth_required
def list_pos_hareketleri():
    """Get all POS transactions."""
    try:
        skip = request.args.get("skip", 0, type=int)
        limit = min(request.args.get("limit", 100, type=int), 1000)
        sube_id = request.args.get("sube_id", None, type=int)
        
        db = get_db_session()
        hareketler = queries.get_pos_hareketleri(db, skip, limit, sube_id)
        db.close()
        
        result = [
            {
                "POSHareketleri_ID": p.ID,
                "Sube_ID": p.Sube_ID,
                "Islem_Tutari": float(p.Islem_Tutari),
                "Pos_Adi": getattr(p, "Pos_Adi", None),
                "Islem_Tarihi": p.Islem_Tarihi.isoformat(),
                "Aciklama": getattr(p, "Aciklama", None),
            }
            for p in hareketler
        ]
        
        return jsonify(result), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@invoicing_bp.route("/pos-hareketleri/<int:hareketi_id>", methods=["GET"])
@auth_required
def get_pos_hareketi(hareketi_id):
    """Get POS transaction by ID."""
    try:
        db = get_db_session()
        hareketi = queries.get_pos_hareketi_by_id(db, hareketi_id)
        db.close()
        
        if not hareketi:
            return jsonify({"error": "POSHareketleri not found"}), 404
        
        result = {
            "POSHareketleri_ID": hareketi.ID,
            "Sube_ID": hareketi.Sube_ID,
            "Islem_Tutari": float(hareketi.Islem_Tutari),
            "Pos_Adi": getattr(hareketi, "Pos_Adi", None),
            "Islem_Tarihi": hareketi.Islem_Tarihi.isoformat(),
            "Aciklama": getattr(hareketi, "Aciklama", None),
        }
        
        return jsonify(result), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@invoicing_bp.route("/pos-hareketleri", methods=["POST"])
@auth_required
def create_pos_hareketi():
    """Create a new POS transaction."""
    try:
        data = request.get_json()
        if not data or "Sube_ID" not in data or "Islem_Tutari" not in data or "Pos_Adi" not in data:
            return jsonify({"error": "Sube_ID, Islem_Tutari, and Pos_Adi required"}), 400
        
        db = get_db_session()
        new_hareketi = queries.create_pos_hareketi(
            db,
            sube_id=data["Sube_ID"],
            islem_tutari=float(data["Islem_Tutari"]),
            pos_adi=data["Pos_Adi"],
            islem_tarihi=data.get("Islem_Tarihi"),
            aciklama=data.get("Aciklama")
        )
        db.close()
        
        result = {
            "POSHareketleri_ID": new_hareketi.ID,
            "Sube_ID": new_hareketi.Sube_ID,
            "Islem_Tutari": float(new_hareketi.Islem_Tutari),
            "Pos_Adi": getattr(new_hareketi, "Pos_Adi", None),
            "Islem_Tarihi": new_hareketi.Islem_Tarihi.isoformat(),
            "Aciklama": getattr(new_hareketi, "Aciklama", None),
        }
        
        return jsonify(result), 201
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@invoicing_bp.route("/pos-hareketleri/<int:hareketi_id>", methods=["PUT"])
@auth_required
def update_pos_hareketi(hareketi_id):
    """Update POS transaction."""
    try:
        data = request.get_json()
        
        db = get_db_session()
        updated_hareketi = queries.update_pos_hareketi(
            db,
            hareketi_id,
            islem_tutari=float(data.get("Islem_Tutari")) if "Islem_Tutari" in data else None,
            pos_adi=data.get("Pos_Adi"),
            aciklama=data.get("Aciklama")
        )
        db.close()
        
        if not updated_hareketi:
            return jsonify({"error": "POSHareketleri not found"}), 404
        
        result = {
            "POSHareketleri_ID": updated_hareketi.ID,
            "Sube_ID": updated_hareketi.Sube_ID,
            "Islem_Tutari": float(updated_hareketi.Islem_Tutari),
            "Pos_Adi": getattr(updated_hareketi, "Pos_Adi", None),
            "Islem_Tarihi": updated_hareketi.Islem_Tarihi.isoformat(),
            "Aciklama": getattr(updated_hareketi, "Aciklama", None),
        }
        
        return jsonify(result), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@invoicing_bp.route("/pos-hareketleri/<int:hareketi_id>", methods=["DELETE"])
@auth_required
def delete_pos_hareketi(hareketi_id):
    """Delete POS transaction."""
    try:
        db = get_db_session()
        deleted = queries.delete_pos_hareketi(db, hareketi_id)
        db.close()
        
        if not deleted:
            return jsonify({"error": "POSHareketleri not found"}), 404
        
        return jsonify({"message": "POSHareketleri deleted"}), 204
    except Exception as e:
        return jsonify({"error": str(e)}), 500
@invoicing_bp.route("/pos-hareketleri/bulk", methods=["POST"])
@auth_required
def create_pos_hareketi_bulk():
    """Bulk create POS transactions."""
    try:
        data = request.get_json()
        if not data or "pos_list" not in data:
            return jsonify({"error": "pos_list required"}), 400
        
        db = get_db_session()
        result = queries.create_pos_hareketi_bulk(db, data["pos_list"])
        db.close()
        
        return jsonify(result), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500
@invoicing_bp.route("/tabak-sayisi/bulk", methods=["POST"])
@auth_required
def update_tabak_sayisi_bulk():
    """Bulk update plate counts."""
    try:
        data = request.get_json()
        if not data or "sube_id" not in data or "data_list" not in data:
            return jsonify({"error": "sube_id and data_list required"}), 400
        
        db = get_db_session()
        result = queries.update_tabak_sayisi_bulk(db, data["sube_id"], data["data_list"])
        db.close()
        
        return jsonify(result), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500
# ============================================================================
# YEMEK CEKI (MEAL TICKETS) ENDPOINTS
# ============================================================================

@invoicing_bp.route("/yemek-cekileri", methods=["GET"])
@auth_required
def list_yemek_cekileri():
    """Get all meal tickets."""
    try:
        skip = request.args.get("skip", 0, type=int)
        limit = min(request.args.get("limit", 100, type=int), 1000)
        sube_id = request.args.get("sube_id", None, type=int)
        donem = request.args.get("donem", None, type=int)
        
        db = get_db_session()
        cekiler = queries.get_yemek_cekileri(db, skip, limit, sube_id, donem)
        db.close()
        
        result = []
        for c in cekiler:
            item = {
                "ID": c.ID,
                "Kategori_ID": c.Kategori_ID,
                "Tarih": c.Tarih.isoformat() if c.Tarih else None,
                "Tutar": float(c.Tutar) if c.Tutar else 0.0,
                "Odeme_Tarih": c.Odeme_Tarih.isoformat() if c.Odeme_Tarih else None,
                "Ilk_Tarih": c.Ilk_Tarih.isoformat() if c.Ilk_Tarih else None,
                "Son_Tarih": c.Son_Tarih.isoformat() if c.Son_Tarih else None,
                "Sube_ID": c.Sube_ID,
                "Imaj_Adi": c.Imaj_Adi,
                "has_imaj": bool(c.Imaj)
            }
            if c.Imaj:
                item["Imaj_Base64"] = base64.b64encode(c.Imaj).decode('utf-8')
            result.append(item)
            
        return jsonify(result), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@invoicing_bp.route("/yemek-cekileri", methods=["POST"])
@auth_required
def create_yemek_ceki():
    """Create a new meal ticket."""
    try:
        # data from form (multipart/form-data)
        data = {
            'Kategori_ID': request.form.get('Kategori_ID', type=int),
            'Tutar': request.form.get('Tutar', type=float),
            'Sube_ID': request.form.get('Sube_ID', type=int),
            'Tarih': datetime.strptime(request.form.get('Tarih'), '%Y-%m-%d').date() if request.form.get('Tarih') else None,
            'Odeme_Tarih': datetime.strptime(request.form.get('Odeme_Tarih'), '%Y-%m-%d').date() if request.form.get('Odeme_Tarih') else None,
            'Ilk_Tarih': datetime.strptime(request.form.get('Ilk_Tarih'), '%Y-%m-%d').date() if request.form.get('Ilk_Tarih') else None,
            'Son_Tarih': datetime.strptime(request.form.get('Son_Tarih'), '%Y-%m-%d').date() if request.form.get('Son_Tarih') else None,
        }
        
        imaj = None
        imaj_adi = None
        if 'image' in request.files:
            file = request.files['image']
            if file and file.filename:
                imaj = file.read()
                imaj_adi = file.filename

        db = get_db_session()
        new_ceki = queries.create_yemek_ceki(db, data, imaj, imaj_adi)
        db.close()
        
        return jsonify({"message": "Kayıt oluşturuldu", "id": new_ceki.ID}), 201
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@invoicing_bp.route("/yemek-cekileri/<int:ceki_id>", methods=["DELETE"])
@auth_required
def delete_yemek_ceki(ceki_id):
    """Delete a meal ticket."""
    try:
        db = get_db_session()
        deleted = queries.delete_yemek_ceki(db, ceki_id)
        db.close()
        if not deleted:
            return jsonify({"error": "Kayıt bulunamadı"}), 404
        return jsonify({"message": "Kayıt silindi"}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@invoicing_bp.route("/yemek-cekileri/<int:ceki_id>", methods=["PUT"])
@auth_required
def update_yemek_ceki_api(ceki_id):
    """Update an existing meal ticket."""
    try:
        db = get_db_session()
        
        data = {}
        if request.form.get('Kategori_ID'): data['Kategori_ID'] = request.form.get('Kategori_ID', type=int)
        if request.form.get('Tutar'): data['Tutar'] = request.form.get('Tutar', type=float)
        if request.form.get('Sube_ID'): data['Sube_ID'] = request.form.get('Sube_ID', type=int)
        if request.form.get('Tarih'): data['Tarih'] = datetime.strptime(request.form.get('Tarih'), '%Y-%m-%d').date()
        if request.form.get('Odeme_Tarih'): data['Odeme_Tarih'] = datetime.strptime(request.form.get('Odeme_Tarih'), '%Y-%m-%d').date()
        if request.form.get('Ilk_Tarih'): data['Ilk_Tarih'] = datetime.strptime(request.form.get('Ilk_Tarih'), '%Y-%m-%d').date()
        if request.form.get('Son_Tarih'): data['Son_Tarih'] = datetime.strptime(request.form.get('Son_Tarih'), '%Y-%m-%d').date()
        
        imaj = None
        imaj_adi = None
        clear_imaj = request.form.get('clear_imaj', 'false').lower() == 'true'
        
        if 'image' in request.files and not clear_imaj:
            file = request.files['image']
            if file and file.filename:
                imaj = file.read()
                imaj_adi = file.filename

        updated_ceki = queries.update_yemek_ceki(db, ceki_id, data, imaj, imaj_adi, clear_imaj)
        db.close()
        
        if not updated_ceki:
            return jsonify({"error": "Kayıt bulunamadı"}), 404
            
        return jsonify({"message": "Kayıt güncellendi"}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# ==========================================
# NAKIT ROUTES
# ==========================================

@invoicing_bp.route("/nakitler", methods=["POST"])
@auth_required
def create_nakit_api():
    """Create a new cash entry."""
    try:
        db = get_db_session()
        data = {
            'Tarih': datetime.strptime(request.form.get('Tarih'), '%Y-%m-%d').date() if request.form.get('Tarih') else None,
            'Tutar': request.form.get('Tutar', type=float),
            'Tip': request.form.get('Tip', 'Bankaya Yatan'),
            'Donem': request.form.get('Donem', type=int),
            'Sube_ID': request.form.get('Sube_ID', type=int)
        }
        
        new_nakit = queries.create_nakit(db, data)
        db.close()
        
        return jsonify({
            "message": "Nakit giriş başarıyla eklendi",
            "id": new_nakit.Nakit_ID
        }), 201
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@invoicing_bp.route("/nakitler/<int:nakit_id>", methods=["PUT"])
@auth_required
def update_nakit_api(nakit_id):
    """Update an existing cash entry."""
    try:
        db = get_db_session()
        data = {}
        
        if request.form.get('Tarih'): data['Tarih'] = datetime.strptime(request.form.get('Tarih'), '%Y-%m-%d').date()
        if request.form.get('Tutar'): data['Tutar'] = request.form.get('Tutar', type=float)
        if request.form.get('Tip'): data['Tip'] = request.form.get('Tip')
        if request.form.get('Donem'): data['Donem'] = request.form.get('Donem', type=int)
        if request.form.get('Sube_ID'): data['Sube_ID'] = request.form.get('Sube_ID', type=int)
        
        updated_nakit = queries.update_nakit(db, nakit_id, data)
        db.close()
        
        if not updated_nakit:
            return jsonify({"error": "Kayıt bulunamadı"}), 404
            
        return jsonify({"message": "Nakit giriş başarıyla güncellendi"}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@invoicing_bp.route("/nakitler/<int:nakit_id>", methods=["DELETE"])
@auth_required
def delete_nakit_api(nakit_id):
    """Delete a cash entry."""
    try:
        db = get_db_session()
        deleted = queries.delete_nakit(db, nakit_id)
        db.close()
        if not deleted:
            return jsonify({"error": "Kayıt bulunamadı"}), 404
        return jsonify({"message": "Nakit giriş silindi"}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# ==========================================
# GELİR ROUTES (Matrix / Pivot Tablo İçin)
# ==========================================

@invoicing_bp.route("/gelirler/bulk", methods=["POST"])
@auth_required
def save_bulk_gelirler_api():
    """Bulk save endpoint for Gelir Matrix."""
    try:
        data = request.get_json()
        if not data:
            return jsonify({"error": "Gelen veri bulunamadı"}), 400
            
        sube_id = data.get('sube_id')
        year = data.get('year')
        month = data.get('month')
        payload = data.get('payload', {})
        
        if not sube_id or not year or not month:
            return jsonify({"error": "Eksik zorunlu parametreler (sube_id, year, month)"}), 400
            
        db = get_db_session()
        success = queries.save_bulk_gelirler(db, int(sube_id), int(year), int(month), payload)
        db.close()
        
        if not success:
            return jsonify({"error": "Kayıt işlemi sırasında hata oluştu. Logları kontrol edin."}), 500
            
        return jsonify({"message": "Tüm matris hücreleri başarıyla kaydedildi."}), 200
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# ============================================================================
# MUTABAKAT (RECONCILIATION) ENDPOINTS
# ============================================================================

@invoicing_bp.route("/mutabakatlar", methods=["GET"])
@auth_required
def list_mutabakatlar():
    """Get all reconciliation records."""
    db = get_db_session()
    try:
        # Permission check for API
        from app.modules.auth import queries as auth_queries
        user_id = getattr(request.user, 'Kullanici_ID', None)
        if not user_id or not auth_queries.has_permission(db, user_id, "Mutabakat Yönetimi Ekranı Görüntüleme"):
            return jsonify({"error": "Permission denied"}), 403
            
        cari_id = request.args.get("cari_id", type=int)
        sube_id = request.args.get("sube_id", type=int)
        search = request.args.get("search", type=str)
        limit = request.args.get("limit", 100, type=int)
        skip = request.args.get("skip", 0, type=int)

        mutabakatlar = queries.get_mutabakatlar(
            db, 
            skip=skip, 
            limit=limit, 
            cari_id=cari_id, 
            sube_id=sube_id, 
            search=search
        )
        
        result = [
            {
                "Mutabakat_ID": m.Mutabakat_ID,
                "Cari_ID": m.Cari_ID,
                "Sube_ID": m.Sube_ID,
                "Alici_Unvani": m.cari.Alici_Unvani if m.cari else "Unknown",
                "Mutabakat_Tarihi": m.Mutabakat_Tarihi.isoformat() if m.Mutabakat_Tarihi else None,
                "Tutar": float(m.Tutar)
            }
            for m in mutabakatlar
        ]
        return jsonify(result), 200
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500
    finally:
        db.close()


@invoicing_bp.route("/mutabakatlar", methods=["POST"])
@auth_required
def create_mutabakat_route():
    """Create a new reconciliation record."""
    db = get_db_session()
    try:
        # Permission check for API
        from app.modules.auth import queries as auth_queries
        user_id = getattr(request.user, 'Kullanici_ID', None)
        if not user_id or not auth_queries.has_permission(db, user_id, "Mutabakat Yönetimi Ekranı Görüntüleme"):
            return jsonify({"error": "Permission denied"}), 403
            
        data = request.get_json()
        if not data or "Cari_ID" not in data or "Mutabakat_Tarihi" not in data or "Tutar" not in data or "Sube_ID" not in data:
            return jsonify({"error": "Cari_ID, Mutabakat_Tarihi, Tutar, and Sube_ID required"}), 400
            
        new_m = queries.create_mutabakat(
            db, 
            cari_id=data["Cari_ID"],
            sube_id=data["Sube_ID"],
            tarih=date.fromisoformat(data["Mutabakat_Tarihi"]),
            tutar=float(data["Tutar"])
        )
        
        return jsonify({
            "message": "Mutabakat created",
            "Mutabakat_ID": new_m.Mutabakat_ID
        }), 201
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        db.close()


@invoicing_bp.route("/mutabakatlar/<int:mut_id>", methods=["PUT"])
@auth_required
def update_mutabakat_route(mut_id):
    """Update reconciliation record."""
    db = get_db_session()
    try:
        # Permission check for API
        from app.modules.auth import queries as auth_queries
        user_id = getattr(request.user, 'Kullanici_ID', None)
        if not user_id or not auth_queries.has_permission(db, user_id, "Mutabakat Yönetimi Ekranı Görüntüleme"):
            return jsonify({"error": "Permission denied"}), 403
            
        data = request.get_json()
        updated = queries.update_mutabakat(
            db, 
            mut_id, 
            tarih=data.get("Mutabakat_Tarihi"),
            tutar=float(data["Tutar"]) if "Tutar" in data else None
        )
        
        if not updated:
            return jsonify({"error": "Mutabakat not found"}), 404
            
        return jsonify({"message": "Mutabakat updated"}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        db.close()


@invoicing_bp.route("/mutabakatlar/<int:mut_id>", methods=["DELETE"])
@auth_required
def delete_mutabakat_route(mut_id):
    """Delete reconciliation record."""
    db = get_db_session()
    try:
        # Permission check for API
        from app.modules.auth import queries as auth_queries
        user_id = getattr(request.user, 'Kullanici_ID', None)
        if not user_id or not auth_queries.has_permission(db, user_id, "Mutabakat Yönetimi Ekranı Görüntüleme"):
            return jsonify({"error": "Permission denied"}), 403
            
        success = queries.delete_mutabakat(db, mut_id)
        
        if not success:
            return jsonify({"error": "Mutabakat not found"}), 404
            
        return jsonify({"message": "Mutabakat deleted"}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        db.close()


@invoicing_bp.route("/robotpos-gelir/bulk", methods=["POST"])
@auth_required
def bulk_robotpos_gelir_route():
    """
    Bulk insert RobotPOS income records with mapping and duplicate control.
    Supports chunked uploads.
    """
    db = get_db_session()
    try:
        # Permission check
        from app.modules.auth import queries as auth_queries
        user_id = getattr(request.user, 'Kullanici_ID', None)
        if not user_id or not auth_queries.has_permission(db, user_id, "Robotpos Gelir Yükleme Ekranı Görüntüleme"):
            return jsonify({"error": "Permission denied"}), 403

        data = request.get_json()
        if not data or 'records' not in data:
            return jsonify({"error": "No records provided"}), 400

        records = data['records']
        
        # 1. Fetch all references for mapping (caching in memory for this request)
        references = ref_queries.get_gelir_referanslar_for_mapping(db)
        # Create a mapping dictionary: lower(trim(odeme_tipi)) -> kategori_id
        ref_map = {ref.Odeme_Tipi.strip().lower(): ref.Kategori_ID for ref in references}
        
        processed_records = []
        errors = []
        
        for idx, rec in enumerate(records):
            try:
                # Basic validation
                if not rec.get('Tarih') or not rec.get('Tutar') or not rec.get('Odeme_Tipi') or not rec.get('Sube_ID'):
                    errors.append(f"Satır {idx+1}: Eksik veri.")
                    continue
                
                odeme_tipi_raw = str(rec['Odeme_Tipi']).strip()
                odeme_tipi_lower = odeme_tipi_raw.lower()
                
                # 2. Case-insensitive Mapping
                kategori_id = ref_map.get(odeme_tipi_lower)
                if not kategori_id:
                    errors.append(f"Satır {idx+1}: '{odeme_tipi_raw}' için eşleşen kategori bulunamadı.")
                    continue
                
                # Parse date
                tarih_str = rec['Tarih']
                if 'T' in tarih_str: # ISO format check
                    tarih = datetime.fromisoformat(tarih_str.replace('Z', '+00:00')).date()
                else:
                    tarih = datetime.strptime(tarih_str, '%Y-%m-%d').date()
                    
                tutar = float(rec['Tutar'])
                
                processed_records.append({
                    'Tarih': tarih,
                    'Tutar': tutar,
                    'Odeme_Tipi': odeme_tipi_raw,
                    'Kategori_ID': kategori_id,
                    'Sube_ID': int(rec['Sube_ID']),
                    'Cek_No': rec.get('Cek_No'),
                    'Satis_Kanali': rec.get('Satis_Kanali')
                })
            except Exception as e:
                errors.append(f"Satır {idx+1}: Hata - {str(e)}")
        
        # 3. Bulk Insert with Duplicate Control
        added, skipped = ref_queries.bulk_upsert_robotpos_gelir(db, processed_records)
        
        return jsonify({
            "status": "success",
            "added": added,
            "skipped": skipped,
            "error_count": len(errors),
            "errors": errors[:50] # Limit error feedback
        }), 200
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        db.close()
