"""
Invoicing Domain Routes
CRUD endpoints for Faturalar, Odemeler, Nakit, Gelir, and related entities.
All endpoints protected by @auth_required decorator.
"""

from functools import wraps
from flask import Blueprint, request, jsonify
from app.common.database import get_db_session
from app.modules.invoicing import queries

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
        limit = min(request.args.get("limit", 100, type=int), 1000)
        sube_id = request.args.get("sube_id", None, type=int)
        kategori_id = request.args.get("kategori_id", None, type=int)
        status = request.args.get("status", None, type=str)
        
        db = get_db_session()
        efaturalar = queries.get_efaturalar(
            db, skip, limit, sube_id, kategori_id, status
        )
        db.close()
        
        result = [
            {
                "EFatura_ID": e.EFatura_ID,
                "Sube_ID": e.Sube_ID,
                "Kategori_ID": e.Kategori_ID,
                "Fatura_No": e.Fatura_No,
                "Fatura_Tutari": float(e.Fatura_Tutari),
                "Kayit_Tarihi": e.Kayit_Tarihi.isoformat(),
                "Durum": e.Durum,
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
            "EFatura_ID": efatura.EFatura_ID,
            "Sube_ID": efatura.Sube_ID,
            "Kategori_ID": efatura.Kategori_ID,
            "Fatura_No": efatura.Fatura_No,
            "Fatura_Tutari": float(efatura.Fatura_Tutari),
            "Kayit_Tarihi": efatura.Kayit_Tarihi.isoformat(),
            "Durum": efatura.Durum,
            "Aciklama": efatura.Aciklama,
        }
        
        return jsonify(result), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@invoicing_bp.route("/efaturalar", methods=["POST"])
@auth_required
def create_efatura():
    """Create a new e-invoice."""
    try:
        data = request.get_json()
        if not data or "Sube_ID" not in data or "Kategori_ID" not in data or "Fatura_No" not in data or "Fatura_Tutari" not in data:
            return jsonify({"error": "Sube_ID, Kategori_ID, Fatura_No, and Fatura_Tutari required"}), 400
        
        db = get_db_session()
        new_efatura = queries.create_efatura(
            db,
            sube_id=data["Sube_ID"],
            kategori_id=data["Kategori_ID"],
            fatura_no=data["Fatura_No"],
            fatura_tutari=float(data["Fatura_Tutari"]),
            kayit_tarihi=data.get("Kayit_Tarihi"),
            aciklama=data.get("Aciklama")
        )
        db.close()
        
        result = {
            "EFatura_ID": new_efatura.EFatura_ID,
            "Sube_ID": new_efatura.Sube_ID,
            "Kategori_ID": new_efatura.Kategori_ID,
            "Fatura_No": new_efatura.Fatura_No,
            "Fatura_Tutari": float(new_efatura.Fatura_Tutari),
            "Kayit_Tarihi": new_efatura.Kayit_Tarihi.isoformat(),
            "Durum": new_efatura.Durum,
            "Aciklama": new_efatura.Aciklama,
        }
        
        return jsonify(result), 201
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@invoicing_bp.route("/efaturalar/<int:efatura_id>", methods=["PUT"])
@auth_required
def update_efatura(efatura_id):
    """Update e-invoice."""
    try:
        data = request.get_json()
        
        db = get_db_session()
        updated_efatura = queries.update_efatura(
            db,
            efatura_id,
            fatura_no=data.get("Fatura_No"),
            fatura_tutari=float(data.get("Fatura_Tutari")) if "Fatura_Tutari" in data else None,
            durum=data.get("Durum"),
            aciklama=data.get("Aciklama")
        )
        db.close()
        
        if not updated_efatura:
            return jsonify({"error": "EFatura not found"}), 404
        
        result = {
            "EFatura_ID": updated_efatura.EFatura_ID,
            "Sube_ID": updated_efatura.Sube_ID,
            "Kategori_ID": updated_efatura.Kategori_ID,
            "Fatura_No": updated_efatura.Fatura_No,
            "Fatura_Tutari": float(updated_efatura.Fatura_Tutari),
            "Kayit_Tarihi": updated_efatura.Kayit_Tarihi.isoformat(),
            "Durum": updated_efatura.Durum,
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


# ============================================================================
# ODEME (PAYMENTS) ENDPOINTS
# ============================================================================

@invoicing_bp.route("/odemeler", methods=["GET"])
@auth_required
def list_odemeler():
    """Get all payments with optional filtering."""
    try:
        skip = request.args.get("skip", 0, type=int)
        limit = min(request.args.get("limit", 100, type=int), 1000)
        sube_id = request.args.get("sube_id", None, type=int)
        kategori_id = request.args.get("kategori_id", None, type=int)
        status = request.args.get("status", None, type=str)
        
        db = get_db_session()
        odemeler = queries.get_odemeler(
            db, skip, limit, sube_id, kategori_id, status
        )
        db.close()
        
        result = [
            {
                "Odeme_ID": o.Odeme_ID,
                "Sube_ID": o.Sube_ID,
                "Kategori_ID": o.Kategori_ID,
                "Odeme_Tutari": float(o.Odeme_Tutari),
                "Odeme_Tarihi": o.Odeme_Tarihi.isoformat(),
                "Odeme_Sekli": o.Odeme_Sekli,
                "Durum": o.Durum,
                "Aciklama": o.Aciklama,
            }
            for o in odemeler
        ]
        
        return jsonify(result), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@invoicing_bp.route("/odemeler/<int:odeme_id>", methods=["GET"])
@auth_required
def get_odeme(odeme_id):
    """Get payment by ID."""
    try:
        db = get_db_session()
        odeme = queries.get_odeme_by_id(db, odeme_id)
        db.close()
        
        if not odeme:
            return jsonify({"error": "Odeme not found"}), 404
        
        result = {
            "Odeme_ID": odeme.Odeme_ID,
            "Sube_ID": odeme.Sube_ID,
            "Kategori_ID": odeme.Kategori_ID,
            "Odeme_Tutari": float(odeme.Odeme_Tutari),
            "Odeme_Tarihi": odeme.Odeme_Tarihi.isoformat(),
            "Odeme_Sekli": odeme.Odeme_Sekli,
            "Durum": odeme.Durum,
            "Aciklama": odeme.Aciklama,
        }
        
        return jsonify(result), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@invoicing_bp.route("/odemeler", methods=["POST"])
@auth_required
def create_odeme():
    """Create a new payment."""
    try:
        data = request.get_json()
        if not data or "Sube_ID" not in data or "Kategori_ID" not in data or "Odeme_Tutari" not in data:
            return jsonify({"error": "Sube_ID, Kategori_ID, and Odeme_Tutari required"}), 400
        
        db = get_db_session()
        new_odeme = queries.create_odeme(
            db,
            sube_id=data["Sube_ID"],
            kategori_id=data["Kategori_ID"],
            odeme_tutari=float(data["Odeme_Tutari"]),
            odeme_tarihi=data.get("Odeme_Tarihi"),
            odeme_sekli=data.get("Odeme_Sekli", "Nakit"),
            aciklama=data.get("Aciklama")
        )
        db.close()
        
        result = {
            "Odeme_ID": new_odeme.Odeme_ID,
            "Sube_ID": new_odeme.Sube_ID,
            "Kategori_ID": new_odeme.Kategori_ID,
            "Odeme_Tutari": float(new_odeme.Odeme_Tutari),
            "Odeme_Tarihi": new_odeme.Odeme_Tarihi.isoformat(),
            "Odeme_Sekli": new_odeme.Odeme_Sekli,
            "Durum": new_odeme.Durum,
            "Aciklama": new_odeme.Aciklama,
        }
        
        return jsonify(result), 201
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@invoicing_bp.route("/odemeler/<int:odeme_id>", methods=["PUT"])
@auth_required
def update_odeme(odeme_id):
    """Update payment."""
    try:
        data = request.get_json()
        
        db = get_db_session()
        updated_odeme = queries.update_odeme(
            db,
            odeme_id,
            odeme_tutari=float(data.get("Odeme_Tutari")) if "Odeme_Tutari" in data else None,
            odeme_sekli=data.get("Odeme_Sekli"),
            durum=data.get("Durum"),
            aciklama=data.get("Aciklama")
        )
        db.close()
        
        if not updated_odeme:
            return jsonify({"error": "Odeme not found"}), 404
        
        result = {
            "Odeme_ID": updated_odeme.Odeme_ID,
            "Sube_ID": updated_odeme.Sube_ID,
            "Kategori_ID": updated_odeme.Kategori_ID,
            "Odeme_Tutari": float(updated_odeme.Odeme_Tutari),
            "Odeme_Tarihi": updated_odeme.Odeme_Tarihi.isoformat(),
            "Odeme_Sekli": updated_odeme.Odeme_Sekli,
            "Durum": updated_odeme.Durum,
            "Aciklama": updated_odeme.Aciklama,
        }
        
        return jsonify(result), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@invoicing_bp.route("/odemeler/<int:odeme_id>", methods=["DELETE"])
@auth_required
def delete_odeme(odeme_id):
    """Delete payment."""
    try:
        db = get_db_session()
        deleted = queries.delete_odeme(db, odeme_id)
        db.close()
        
        if not deleted:
            return jsonify({"error": "Odeme not found"}), 404
        
        return jsonify({"message": "Odeme deleted"}), 204
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

@invoicing_bp.route("/diger-harcamalar", methods=["GET"])
@auth_required
def list_diger_harcamalar():
    """Get all other expenses."""
    try:
        skip = request.args.get("skip", 0, type=int)
        limit = min(request.args.get("limit", 100, type=int), 1000)
        sube_id = request.args.get("sube_id", None, type=int)
        
        db = get_db_session()
        harcamalar = queries.get_diger_harcamalar(db, skip, limit, sube_id)
        db.close()
        
        result = [
            {
                "DigerHarcama_ID": h.DigerHarcama_ID,
                "Sube_ID": h.Sube_ID,
                "Harcama_Adi": h.Harcama_Adi,
                "Harcama_Tutari": float(h.Harcama_Tutari),
                "Kayit_Tarihi": h.Kayit_Tarihi.isoformat(),
                "Aciklama": h.Aciklama,
            }
            for h in harcamalar
        ]
        
        return jsonify(result), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@invoicing_bp.route("/diger-harcamalar/<int:harcama_id>", methods=["GET"])
@auth_required
def get_diger_harcama(harcama_id):
    """Get other expense by ID."""
    try:
        db = get_db_session()
        harcama = queries.get_diger_harcama_by_id(db, harcama_id)
        db.close()
        
        if not harcama:
            return jsonify({"error": "DigerHarcama not found"}), 404
        
        result = {
            "DigerHarcama_ID": harcama.DigerHarcama_ID,
            "Sube_ID": harcama.Sube_ID,
            "Harcama_Adi": harcama.Harcama_Adi,
            "Harcama_Tutari": float(harcama.Harcama_Tutari),
            "Kayit_Tarihi": harcama.Kayit_Tarihi.isoformat(),
            "Aciklama": harcama.Aciklama,
        }
        
        return jsonify(result), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@invoicing_bp.route("/diger-harcamalar", methods=["POST"])
@auth_required
def create_diger_harcama():
    """Create a new other expense."""
    try:
        data = request.get_json()
        if not data or "Sube_ID" not in data or "Harcama_Adi" not in data or "Harcama_Tutari" not in data:
            return jsonify({"error": "Sube_ID, Harcama_Adi, and Harcama_Tutari required"}), 400
        
        db = get_db_session()
        new_harcama = queries.create_diger_harcama(
            db,
            sube_id=data["Sube_ID"],
            harcama_adi=data["Harcama_Adi"],
            harcama_tutari=float(data["Harcama_Tutari"]),
            kayit_tarihi=data.get("Kayit_Tarihi"),
            aciklama=data.get("Aciklama")
        )
        db.close()
        
        result = {
            "DigerHarcama_ID": new_harcama.DigerHarcama_ID,
            "Sube_ID": new_harcama.Sube_ID,
            "Harcama_Adi": new_harcama.Harcama_Adi,
            "Harcama_Tutari": float(new_harcama.Harcama_Tutari),
            "Kayit_Tarihi": new_harcama.Kayit_Tarihi.isoformat(),
            "Aciklama": new_harcama.Aciklama,
        }
        
        return jsonify(result), 201
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@invoicing_bp.route("/diger-harcamalar/<int:harcama_id>", methods=["PUT"])
@auth_required
def update_diger_harcama(harcama_id):
    """Update other expense."""
    try:
        data = request.get_json()
        
        db = get_db_session()
        updated_harcama = queries.update_diger_harcama(
            db,
            harcama_id,
            harcama_adi=data.get("Harcama_Adi"),
            harcama_tutari=float(data.get("Harcama_Tutari")) if "Harcama_Tutari" in data else None,
            aciklama=data.get("Aciklama")
        )
        db.close()
        
        if not updated_harcama:
            return jsonify({"error": "DigerHarcama not found"}), 404
        
        result = {
            "DigerHarcama_ID": updated_harcama.DigerHarcama_ID,
            "Sube_ID": updated_harcama.Sube_ID,
            "Harcama_Adi": updated_harcama.Harcama_Adi,
            "Harcama_Tutari": float(updated_harcama.Harcama_Tutari),
            "Kayit_Tarihi": updated_harcama.Kayit_Tarihi.isoformat(),
            "Aciklama": updated_harcama.Aciklama,
        }
        
        return jsonify(result), 200
    except Exception as e:
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
