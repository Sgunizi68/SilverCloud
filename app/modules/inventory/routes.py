"""
Inventory Domain Routes
CRUD endpoints for Stock, Stock Price, and Stock Count.
All endpoints protected by @auth_required decorator.
"""

from functools import wraps
from flask import Blueprint, request, jsonify
from app.common.database import get_db_session
from app.modules.inventory import queries

inventory_bp = Blueprint("inventory", __name__, url_prefix="/api/v1")

# Late-binding auth_required to avoid circular import
def auth_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        from app.modules.auth.routes import auth_required as _auth_required
        return _auth_required(f)(*args, **kwargs)
    return decorated


# ============================================================================
# STOK (STOCK) ENDPOINTS
# ============================================================================

@inventory_bp.route("/stok", methods=["GET"])
@auth_required
def list_stok():
    """Get all stock items with optional filtering."""
    try:
        skip = request.args.get("skip", 0, type=int)
        limit = min(request.args.get("limit", 100, type=int), 1000)
        urun_grubu = request.args.get("urun_grubu", None, type=str)
        malzeme_kodu = request.args.get("malzeme_kodu", None, type=str)
        aktif_pasif = request.args.get("aktif_pasif", None)
        if aktif_pasif is not None:
            aktif_pasif = aktif_pasif.lower() == "true"
        
        db = get_db_session()
        stoklar = queries.get_stoklar(
            db, skip, limit, urun_grubu, malzeme_kodu, aktif_pasif
        )
        db.close()
        
        result = [
            {
                "Stok_ID": s.Stok_ID,
                "Urun_Grubu": s.Urun_Grubu,
                "Malzeme_Kodu": s.Malzeme_Kodu,
                "Malzeme_Aciklamasi": s.Malzeme_Aciklamasi,
                "Birimi": s.Birimi,
                "Sinif": s.Sinif,
                "Aktif_Pasif": s.Aktif_Pasif,
            }
            for s in stoklar
        ]
        
        return jsonify(result), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@inventory_bp.route("/stok/<int:stok_id>", methods=["GET"])
@auth_required
def get_stok(stok_id):
    """Get stock item by ID."""
    try:
        db = get_db_session()
        stok = queries.get_stok_by_id(db, stok_id)
        db.close()
        
        if not stok:
            return jsonify({"error": "Stok not found"}), 404
        
        result = {
            "Stok_ID": stok.Stok_ID,
            "Urun_Grubu": stok.Urun_Grubu,
            "Malzeme_Kodu": stok.Malzeme_Kodu,
            "Malzeme_Aciklamasi": stok.Malzeme_Aciklamasi,
            "Birimi": stok.Birimi,
            "Sinif": stok.Sinif,
            "Aktif_Pasif": stok.Aktif_Pasif,
        }
        
        return jsonify(result), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@inventory_bp.route("/stok", methods=["POST"])
@auth_required
def create_stok():
    """Create a new stock item."""
    try:
        data = request.get_json()
        if not data or "Urun_Grubu" not in data or "Malzeme_Kodu" not in data or "Malzeme_Aciklamasi" not in data or "Birimi" not in data:
            return jsonify({"error": "Urun_Grubu, Malzeme_Kodu, Malzeme_Aciklamasi, and Birimi required"}), 400
        
        db = get_db_session()
        new_stok = queries.create_stok(
            db,
            urun_grubu=data["Urun_Grubu"],
            malzeme_kodu=data["Malzeme_Kodu"],
            malzeme_aciklamasi=data["Malzeme_Aciklamasi"],
            birimi=data["Birimi"],
            sinif=data.get("Sinif"),
            aktif_pasif=data.get("Aktif_Pasif", True)
        )
        db.close()
        
        result = {
            "Stok_ID": new_stok.Stok_ID,
            "Urun_Grubu": new_stok.Urun_Grubu,
            "Malzeme_Kodu": new_stok.Malzeme_Kodu,
            "Malzeme_Aciklamasi": new_stok.Malzeme_Aciklamasi,
            "Birimi": new_stok.Birimi,
            "Sinif": new_stok.Sinif,
            "Aktif_Pasif": new_stok.Aktif_Pasif,
        }
        
        return jsonify(result), 201
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@inventory_bp.route("/stok/<int:stok_id>", methods=["PUT"])
@auth_required
def update_stok(stok_id):
    """Update stock item."""
    try:
        data = request.get_json()
        
        db = get_db_session()
        updated_stok = queries.update_stok(
            db,
            stok_id,
            urun_grubu=data.get("Urun_Grubu"),
            malzeme_aciklamasi=data.get("Malzeme_Aciklamasi"),
            birimi=data.get("Birimi"),
            sinif=data.get("Sinif"),
            aktif_pasif=data.get("Aktif_Pasif")
        )
        db.close()
        
        if not updated_stok:
            return jsonify({"error": "Stok not found"}), 404
        
        result = {
            "Stok_ID": updated_stok.Stok_ID,
            "Urun_Grubu": updated_stok.Urun_Grubu,
            "Malzeme_Kodu": updated_stok.Malzeme_Kodu,
            "Malzeme_Aciklamasi": updated_stok.Malzeme_Aciklamasi,
            "Birimi": updated_stok.Birimi,
            "Sinif": updated_stok.Sinif,
            "Aktif_Pasif": updated_stok.Aktif_Pasif,
        }
        
        return jsonify(result), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@inventory_bp.route("/stok/<int:stok_id>", methods=["DELETE"])
@auth_required
def delete_stok(stok_id):
    """Delete stock item."""
    try:
        db = get_db_session()
        deleted = queries.delete_stok(db, stok_id)
        db.close()
        
        if not deleted:
            return jsonify({"error": "Stok not found"}), 404
        
        return jsonify({"message": "Stok deleted"}), 204
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# ============================================================================
# STOK FIYAT (STOCK PRICE) ENDPOINTS
# ============================================================================

@inventory_bp.route("/stok-fiyatlar", methods=["GET"])
@auth_required
def list_stok_fiyatlar():
    """Get all stock prices with optional filtering."""
    try:
        skip = request.args.get("skip", 0, type=int)
        limit = min(request.args.get("limit", 100, type=int), 1000)
        malzeme_kodu = request.args.get("malzeme_kodu", None, type=str)
        sube_id = request.args.get("sube_id", None, type=int)
        aktif_pasif = request.args.get("aktif_pasif", None)
        if aktif_pasif is not None:
            aktif_pasif = aktif_pasif.lower() == "true"
        
        db = get_db_session()
        fiyatlar = queries.get_stok_fiyatlar(
            db, skip, limit, malzeme_kodu, sube_id, aktif_pasif
        )
        db.close()
        
        result = [
            {
                "Fiyat_ID": f.Fiyat_ID,
                "Malzeme_Kodu": f.Malzeme_Kodu,
                "Gecerlilik_Baslangic_Tarih": f.Gecerlilik_Baslangic_Tarih.isoformat(),
                "Fiyat": float(f.Fiyat),
                "Sube_ID": f.Sube_ID,
                "Aktif_Pasif": f.Aktif_Pasif,
            }
            for f in fiyatlar
        ]
        
        return jsonify(result), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@inventory_bp.route("/stok-fiyatlar/<int:fiyat_id>", methods=["GET"])
@auth_required
def get_stok_fiyat(fiyat_id):
    """Get stock price by ID."""
    try:
        db = get_db_session()
        fiyat = queries.get_stok_fiyat_by_id(db, fiyat_id)
        db.close()
        
        if not fiyat:
            return jsonify({"error": "StokFiyat not found"}), 404
        
        result = {
            "Fiyat_ID": fiyat.Fiyat_ID,
            "Malzeme_Kodu": fiyat.Malzeme_Kodu,
            "Gecerlilik_Baslangic_Tarih": fiyat.Gecerlilik_Baslangic_Tarih.isoformat(),
            "Fiyat": float(fiyat.Fiyat),
            "Sube_ID": fiyat.Sube_ID,
            "Aktif_Pasif": fiyat.Aktif_Pasif,
        }
        
        return jsonify(result), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@inventory_bp.route("/stok-fiyatlar", methods=["POST"])
@auth_required
def create_stok_fiyat():
    """Create a new stock price."""
    try:
        data = request.get_json()
        if not data or "Malzeme_Kodu" not in data or "Fiyat" not in data or "Sube_ID" not in data:
            return jsonify({"error": "Malzeme_Kodu, Fiyat, and Sube_ID required"}), 400
        
        db = get_db_session()
        new_fiyat = queries.create_stok_fiyat(
            db,
            malzeme_kodu=data["Malzeme_Kodu"],
            gecerlilik_baslangic_tarih=data.get("Gecerlilik_Baslangic_Tarih"),
            fiyat=float(data["Fiyat"]),
            sube_id=data["Sube_ID"],
            aktif_pasif=data.get("Aktif_Pasif", True)
        )
        db.close()
        
        result = {
            "Fiyat_ID": new_fiyat.Fiyat_ID,
            "Malzeme_Kodu": new_fiyat.Malzeme_Kodu,
            "Gecerlilik_Baslangic_Tarih": new_fiyat.Gecerlilik_Baslangic_Tarih.isoformat(),
            "Fiyat": float(new_fiyat.Fiyat),
            "Sube_ID": new_fiyat.Sube_ID,
            "Aktif_Pasif": new_fiyat.Aktif_Pasif,
        }
        
        return jsonify(result), 201
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@inventory_bp.route("/stok-fiyatlar/<int:fiyat_id>", methods=["PUT"])
@auth_required
def update_stok_fiyat(fiyat_id):
    """Update stock price."""
    try:
        data = request.get_json()
        
        db = get_db_session()
        updated_fiyat = queries.update_stok_fiyat(
            db,
            fiyat_id,
            fiyat=float(data.get("Fiyat")) if "Fiyat" in data else None,
            aktif_pasif=data.get("Aktif_Pasif"),
            gecerlilik_baslangic_tarih=data.get("Gecerlilik_Baslangic_Tarih")
        )
        db.close()
        
        if not updated_fiyat:
            return jsonify({"error": "StokFiyat not found"}), 404
        
        result = {
            "Fiyat_ID": updated_fiyat.Fiyat_ID,
            "Malzeme_Kodu": updated_fiyat.Malzeme_Kodu,
            "Gecerlilik_Baslangic_Tarih": updated_fiyat.Gecerlilik_Baslangic_Tarih.isoformat(),
            "Fiyat": float(updated_fiyat.Fiyat),
            "Sube_ID": updated_fiyat.Sube_ID,
            "Aktif_Pasif": updated_fiyat.Aktif_Pasif,
        }
        
        return jsonify(result), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@inventory_bp.route("/stok-fiyatlar/<int:fiyat_id>", methods=["DELETE"])
@auth_required
def delete_stok_fiyat(fiyat_id):
    """Delete stock price."""
    try:
        db = get_db_session()
        deleted = queries.delete_stok_fiyat(db, fiyat_id)
        db.close()
        
        if not deleted:
            return jsonify({"error": "StokFiyat not found"}), 404
        
        return jsonify({"message": "StokFiyat deleted"}), 204
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# ============================================================================
# STOK SAYIM (STOCK COUNT) ENDPOINTS
# ============================================================================

@inventory_bp.route("/stok-sayimlar", methods=["GET"])
@auth_required
def list_stok_sayimlar():
    """Get all stock counts with optional filtering."""
    try:
        skip = request.args.get("skip", 0, type=int)
        limit = min(request.args.get("limit", 100, type=int), 1000)
        malzeme_kodu = request.args.get("malzeme_kodu", None, type=str)
        sube_id = request.args.get("sube_id", None, type=int)
        donem = request.args.get("donem", None, type=int)
        
        db = get_db_session()
        sayimlar = queries.get_stok_sayimlar(
            db, skip, limit, malzeme_kodu, sube_id, donem
        )
        db.close()
        
        result = [
            {
                "Sayim_ID": s.Sayim_ID,
                "Malzeme_Kodu": s.Malzeme_Kodu,
                "Donem": s.Donem,
                "Miktar": float(s.Miktar),
                "Sube_ID": s.Sube_ID,
                "Kayit_Tarihi": s.Kayit_Tarihi.isoformat(),
            }
            for s in sayimlar
        ]
        
        return jsonify(result), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@inventory_bp.route("/stok-sayimlar/<int:sayim_id>", methods=["GET"])
@auth_required
def get_stok_sayim(sayim_id):
    """Get stock count by ID."""
    try:
        db = get_db_session()
        sayim = queries.get_stok_sayim_by_id(db, sayim_id)
        db.close()
        
        if not sayim:
            return jsonify({"error": "StokSayim not found"}), 404
        
        result = {
            "Sayim_ID": sayim.Sayim_ID,
            "Malzeme_Kodu": sayim.Malzeme_Kodu,
            "Donem": sayim.Donem,
            "Miktar": float(sayim.Miktar),
            "Sube_ID": sayim.Sube_ID,
            "Kayit_Tarihi": sayim.Kayit_Tarihi.isoformat(),
        }
        
        return jsonify(result), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@inventory_bp.route("/stok-sayimlar", methods=["POST"])
@auth_required
def create_stok_sayim():
    """Create a new stock count."""
    try:
        data = request.get_json()
        if not data or "Malzeme_Kodu" not in data or "Donem" not in data or "Miktar" not in data or "Sube_ID" not in data:
            return jsonify({"error": "Malzeme_Kodu, Donem, Miktar, and Sube_ID required"}), 400
        
        db = get_db_session()
        new_sayim = queries.create_stok_sayim(
            db,
            malzeme_kodu=data["Malzeme_Kodu"],
            donem=int(data["Donem"]),
            miktar=float(data["Miktar"]),
            sube_id=data["Sube_ID"],
            kayit_tarihi=data.get("Kayit_Tarihi")
        )
        db.close()
        
        result = {
            "Sayim_ID": new_sayim.Sayim_ID,
            "Malzeme_Kodu": new_sayim.Malzeme_Kodu,
            "Donem": new_sayim.Donem,
            "Miktar": float(new_sayim.Miktar),
            "Sube_ID": new_sayim.Sube_ID,
            "Kayit_Tarihi": new_sayim.Kayit_Tarihi.isoformat(),
        }
        
        return jsonify(result), 201
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@inventory_bp.route("/stok-sayimlar/auto-save", methods=["POST"])
@auth_required
def auto_save_stok_sayim():
    """Auto-save (upsert) a single stock count entry."""
    try:
        data = request.get_json()
        if not data or "Malzeme_Kodu" not in data or "Donem" not in data or "Miktar" not in data or "Sube_ID" not in data:
            return jsonify({"error": "Malzeme_Kodu, Donem, Miktar, and Sube_ID required"}), 400
        
        db = get_db_session()
        saved_sayim = queries.upsert_stok_sayim(
            db,
            malzeme_kodu=data["Malzeme_Kodu"],
            donem=int(data["Donem"]),
            miktar=float(data["Miktar"]),
            sube_id=data["Sube_ID"]
        )
        db.close()
        
        result = {
            "Sayim_ID": saved_sayim.Sayim_ID,
            "Malzeme_Kodu": saved_sayim.Malzeme_Kodu,
            "Donem": saved_sayim.Donem,
            "Miktar": float(saved_sayim.Miktar),
            "Sube_ID": saved_sayim.Sube_ID,
            "Kayit_Tarihi": saved_sayim.Kayit_Tarihi.isoformat(),
        }
        return jsonify(result), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@inventory_bp.route("/stok-sayimlar/<int:sayim_id>", methods=["PUT"])
@auth_required
def update_stok_sayim(sayim_id):
    """Update stock count."""
    try:
        data = request.get_json()
        
        db = get_db_session()
        updated_sayim = queries.update_stok_sayim(
            db,
            sayim_id,
            miktar=float(data.get("Miktar")) if "Miktar" in data else None
        )
        db.close()
        
        if not updated_sayim:
            return jsonify({"error": "StokSayim not found"}), 404
        
        result = {
            "Sayim_ID": updated_sayim.Sayim_ID,
            "Malzeme_Kodu": updated_sayim.Malzeme_Kodu,
            "Donem": updated_sayim.Donem,
            "Miktar": float(updated_sayim.Miktar),
            "Sube_ID": updated_sayim.Sube_ID,
            "Kayit_Tarihi": updated_sayim.Kayit_Tarihi.isoformat(),
        }
        
        return jsonify(result), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@inventory_bp.route("/stok-sayimlar/<int:sayim_id>", methods=["DELETE"])
@auth_required
def delete_stok_sayim(sayim_id):
    """Delete stock count."""
    try:
        db = get_db_session()
        deleted = queries.delete_stok_sayim(db, sayim_id)
        db.close()
        
        if not deleted:
            return jsonify({"error": "StokSayim not found"}), 404
        
        return jsonify({"message": "StokSayim deleted"}), 204
    except Exception as e:
        return jsonify({"error": str(e)}), 500
