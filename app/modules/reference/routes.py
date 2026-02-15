"""
Reference Domain Routes
CRUD endpoints for Kategoriler, Deverler, Sube, UstKategori, and Kullanici.
All endpoints protected by @auth_required decorator.
"""

from functools import wraps
from flask import Blueprint, request, jsonify
from app.common.database import get_db_session
from app.modules.reference import queries

reference_bp = Blueprint("reference", __name__, url_prefix="/api/v1")

# Late-binding auth_required to avoid circular import
def auth_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        from app.modules.auth.routes import auth_required as _auth_required
        return _auth_required(f)(*args, **kwargs)
    return decorated


# ============================================================================
# SUBE (BRANCHES) ENDPOINTS
# ============================================================================

@reference_bp.route("/subeler", methods=["GET"])
@auth_required
def list_suber():
    """Get all branches with pagination."""
    try:
        skip = request.args.get("skip", 0, type=int)
        limit = min(request.args.get("limit", 100, type=int), 1000)
        
        db = get_db_session()
        suber = queries.get_suber(db, skip, limit)
        db.close()
        
        result = [
            {
                "Sube_ID": s.Sube_ID,
                "Sube_Adi": s.Sube_Adi,
                "Aciklama": s.Aciklama,
                "Aktif_Pasif": s.Aktif_Pasif,
            }
            for s in suber
        ]
        
        return jsonify(result), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@reference_bp.route("/subeler/<int:sube_id>", methods=["GET"])
@auth_required
def get_sube(sube_id):
    """Get a branch by ID."""
    try:
        db = get_db_session()
        sube = queries.get_sube_by_id(db, sube_id)
        db.close()
        
        if not sube:
            return jsonify({"error": "Sube not found"}), 404
        
        result = {
            "Sube_ID": sube.Sube_ID,
            "Sube_Adi": sube.Sube_Adi,
            "Aciklama": sube.Aciklama,
            "Aktif_Pasif": sube.Aktif_Pasif,
        }
        
        return jsonify(result), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@reference_bp.route("/subeler", methods=["POST"])
@auth_required
def create_sube():
    """Create a new branch."""
    try:
        data = request.get_json()
        if not data or "Sube_Adi" not in data:
            return jsonify({"error": "Sube_Adi required"}), 400
        
        db = get_db_session()
        new_sube = queries.create_sube(
            db,
            sube_adi=data["Sube_Adi"],
            aciklama=data.get("Aciklama")
        )
        db.close()
        
        result = {
            "Sube_ID": new_sube.Sube_ID,
            "Sube_Adi": new_sube.Sube_Adi,
            "Aciklama": new_sube.Aciklama,
            "Aktif_Pasif": new_sube.Aktif_Pasif,
        }
        
        return jsonify(result), 201
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@reference_bp.route("/subeler/<int:sube_id>", methods=["PUT"])
@auth_required
def update_sube(sube_id):
    """Update a branch."""
    try:
        data = request.get_json()
        
        db = get_db_session()
        updated_sube = queries.update_sube(
            db,
            sube_id,
            sube_adi=data.get("Sube_Adi"),
            aciklama=data.get("Aciklama"),
            aktif_pasif=data.get("Aktif_Pasif")
        )
        db.close()
        
        if not updated_sube:
            return jsonify({"error": "Sube not found"}), 404
        
        result = {
            "Sube_ID": updated_sube.Sube_ID,
            "Sube_Adi": updated_sube.Sube_Adi,
            "Aciklama": updated_sube.Aciklama,
            "Aktif_Pasif": updated_sube.Aktif_Pasif,
        }
        
        return jsonify(result), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@reference_bp.route("/subeler/<int:sube_id>", methods=["DELETE"])
@auth_required
def delete_sube(sube_id):
    """Delete a branch."""
    try:
        db = get_db_session()
        deleted = queries.delete_sube(db, sube_id)
        db.close()
        
        if not deleted:
            return jsonify({"error": "Sube not found"}), 404
        
        return jsonify({"message": "Sube deleted"}), 204
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# ============================================================================
# KATEGORI (CATEGORIES) ENDPOINTS
# ============================================================================

@reference_bp.route("/kategoriler", methods=["GET"])
@auth_required
def list_kategoriler():
    """Get all categories with optional filtering."""
    try:
        skip = request.args.get("skip", 0, type=int)
        limit = min(request.args.get("limit", 100, type=int), 1000)
        ust_kategori_id = request.args.get("ust_kategori_id", None, type=int)
        tip = request.args.get("tip", None, type=str)
        aktif_only = request.args.get("aktif_only", True, type=bool)
        
        db = get_db_session()
        kategoriler = queries.get_kategoriler(
            db, skip, limit, ust_kategori_id, tip, aktif_only
        )
        db.close()
        
        result = [
            {
                "Kategori_ID": k.Kategori_ID,
                "Kategori_Adi": k.Kategori_Adi,
                "Ust_Kategori_ID": k.Ust_Kategori_ID,
                "Tip": k.Tip,
                "Aktif_Pasif": k.Aktif_Pasif,
                "Gizli": k.Gizli,
            }
            for k in kategoriler
        ]
        
        return jsonify(result), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@reference_bp.route("/kategoriler/<int:kategori_id>", methods=["GET"])
@auth_required
def get_kategori(kategori_id):
    """Get a category by ID."""
    try:
        db = get_db_session()
        kategori = queries.get_kategori_by_id(db, kategori_id)
        db.close()
        
        if not kategori:
            return jsonify({"error": "Kategori not found"}), 404
        
        result = {
            "Kategori_ID": kategori.Kategori_ID,
            "Kategori_Adi": kategori.Kategori_Adi,
            "Ust_Kategori_ID": kategori.Ust_Kategori_ID,
            "Tip": kategori.Tip,
            "Aktif_Pasif": kategori.Aktif_Pasif,
            "Gizli": kategori.Gizli,
        }
        
        return jsonify(result), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@reference_bp.route("/kategoriler", methods=["POST"])
@auth_required
def create_kategori():
    """Create a new category."""
    try:
        data = request.get_json()
        if not data or "Kategori_Adi" not in data or "Tip" not in data:
            return jsonify({"error": "Kategori_Adi and Tip required"}), 400
        
        db = get_db_session()
        new_kategori = queries.create_kategori(
            db,
            kategori_adi=data["Kategori_Adi"],
            tip=data["Tip"],
            ust_kategori_id=data.get("Ust_Kategori_ID"),
            gizli=data.get("Gizli", False)
        )
        db.close()
        
        result = {
            "Kategori_ID": new_kategori.Kategori_ID,
            "Kategori_Adi": new_kategori.Kategori_Adi,
            "Ust_Kategori_ID": new_kategori.Ust_Kategori_ID,
            "Tip": new_kategori.Tip,
            "Aktif_Pasif": new_kategori.Aktif_Pasif,
            "Gizli": new_kategori.Gizli,
        }
        
        return jsonify(result), 201
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@reference_bp.route("/kategoriler/<int:kategori_id>", methods=["PUT"])
@auth_required
def update_kategori(kategori_id):
    """Update a category."""
    try:
        data = request.get_json()
        
        db = get_db_session()
        updated_kategori = queries.update_kategori(
            db,
            kategori_id,
            kategori_adi=data.get("Kategori_Adi"),
            tip=data.get("Tip"),
            ust_kategori_id=data.get("Ust_Kategori_ID"),
            aktif_pasif=data.get("Aktif_Pasif"),
            gizli=data.get("Gizli")
        )
        db.close()
        
        if not updated_kategori:
            return jsonify({"error": "Kategori not found"}), 404
        
        result = {
            "Kategori_ID": updated_kategori.Kategori_ID,
            "Kategori_Adi": updated_kategori.Kategori_Adi,
            "Ust_Kategori_ID": updated_kategori.Ust_Kategori_ID,
            "Tip": updated_kategori.Tip,
            "Aktif_Pasif": updated_kategori.Aktif_Pasif,
            "Gizli": updated_kategori.Gizli,
        }
        
        return jsonify(result), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@reference_bp.route("/kategoriler/<int:kategori_id>", methods=["DELETE"])
@auth_required
def delete_kategori(kategori_id):
    """Delete a category."""
    try:
        db = get_db_session()
        deleted = queries.delete_kategori(db, kategori_id)
        db.close()
        
        if not deleted:
            return jsonify({"error": "Kategori not found"}), 404
        
        return jsonify({"message": "Kategori deleted"}), 204
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# ============================================================================
# UST KATEGORI (PARENT CATEGORIES) ENDPOINTS
# ============================================================================

@reference_bp.route("/ust-kategoriler", methods=["GET"])
@auth_required
def list_ust_kategoriler():
    """Get all parent categories."""
    try:
        skip = request.args.get("skip", 0, type=int)
        limit = min(request.args.get("limit", 100, type=int), 1000)
        
        db = get_db_session()
        ust_kategoriler = queries.get_ust_kategoriler(db, skip, limit)
        db.close()
        
        result = [
            {
                "UstKategori_ID": uk.UstKategori_ID,
                "UstKategori_Adi": uk.UstKategori_Adi,
                "Aktif_Pasif": uk.Aktif_Pasif,
            }
            for uk in ust_kategoriler
        ]
        
        return jsonify(result), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@reference_bp.route("/ust-kategoriler/<int:ust_kategori_id>", methods=["GET"])
@auth_required
def get_ust_kategori(ust_kategori_id):
    """Get a parent category by ID."""
    try:
        db = get_db_session()
        ust_kategori = queries.get_ust_kategori_by_id(db, ust_kategori_id)
        db.close()
        
        if not ust_kategori:
            return jsonify({"error": "UstKategori not found"}), 404
        
        result = {
            "UstKategori_ID": ust_kategori.UstKategori_ID,
            "UstKategori_Adi": ust_kategori.UstKategori_Adi,
            "Aktif_Pasif": ust_kategori.Aktif_Pasif,
        }
        
        return jsonify(result), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@reference_bp.route("/ust-kategoriler", methods=["POST"])
@auth_required
def create_ust_kategori():
    """Create a new parent category."""
    try:
        data = request.get_json()
        if not data or "UstKategori_Adi" not in data:
            return jsonify({"error": "UstKategori_Adi required"}), 400
        
        db = get_db_session()
        new_ust_kategori = queries.create_ust_kategori(db, data["UstKategori_Adi"])
        db.close()
        
        result = {
            "UstKategori_ID": new_ust_kategori.UstKategori_ID,
            "UstKategori_Adi": new_ust_kategori.UstKategori_Adi,
            "Aktif_Pasif": new_ust_kategori.Aktif_Pasif,
        }
        
        return jsonify(result), 201
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@reference_bp.route("/ust-kategoriler/<int:ust_kategori_id>", methods=["PUT"])
@auth_required
def update_ust_kategori(ust_kategori_id):
    """Update a parent category."""
    try:
        data = request.get_json()
        
        db = get_db_session()
        updated_ust_kategori = queries.update_ust_kategori(
            db,
            ust_kategori_id,
            adi=data.get("UstKategori_Adi"),
            aktif_pasif=data.get("Aktif_Pasif")
        )
        db.close()
        
        if not updated_ust_kategori:
            return jsonify({"error": "UstKategori not found"}), 404
        
        result = {
            "UstKategori_ID": updated_ust_kategori.UstKategori_ID,
            "UstKategori_Adi": updated_ust_kategori.UstKategori_Adi,
            "Aktif_Pasif": updated_ust_kategori.Aktif_Pasif,
        }
        
        return jsonify(result), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@reference_bp.route("/ust-kategoriler/<int:ust_kategori_id>", methods=["DELETE"])
@auth_required
def delete_ust_kategori(ust_kategori_id):
    """Delete a parent category."""
    try:
        db = get_db_session()
        deleted = queries.delete_ust_kategori(db, ust_kategori_id)
        db.close()
        
        if not deleted:
            return jsonify({"error": "UstKategori not found"}), 404
        
        return jsonify({"message": "UstKategori deleted"}), 204
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# ============================================================================
# DEGER (VALUES) ENDPOINTS
# ============================================================================

@reference_bp.route("/degerler", methods=["GET"])
@auth_required
def list_degerler():
    """Get all values with optional filtering."""
    try:
        skip = request.args.get("skip", 0, type=int)
        limit = min(request.args.get("limit", 100, type=int), 1000)
        deger_adi = request.args.get("deger_adi", None, type=str)
        
        db = get_db_session()
        degerler = queries.get_degerler(db, skip, limit, deger_adi)
        db.close()
        
        result = [
            {
                "Deger_ID": d.Deger_ID,
                "Deger_Adi": d.Deger_Adi,
                "Gecerli_Baslangic_Tarih": d.Gecerli_Baslangic_Tarih.isoformat(),
                "Gecerli_Bitis_Tarih": d.Gecerli_Bitis_Tarih.isoformat(),
                "Deger_Aciklama": d.Deger_Aciklama,
                "Deger": float(d.Deger),
            }
            for d in degerler
        ]
        
        return jsonify(result), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@reference_bp.route("/degerler/<int:deger_id>", methods=["GET"])
@auth_required
def get_deger(deger_id):
    """Get a value by ID."""
    try:
        db = get_db_session()
        deger = queries.get_deger_by_id(db, deger_id)
        db.close()
        
        if not deger:
            return jsonify({"error": "Deger not found"}), 404
        
        result = {
            "Deger_ID": deger.Deger_ID,
            "Deger_Adi": deger.Deger_Adi,
            "Gecerli_Baslangic_Tarih": deger.Gecerli_Baslangic_Tarih.isoformat(),
            "Gecerli_Bitis_Tarih": deger.Gecerli_Bitis_Tarih.isoformat(),
            "Deger_Aciklama": deger.Deger_Aciklama,
            "Deger": float(deger.Deger),
        }
        
        return jsonify(result), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@reference_bp.route("/degerler", methods=["POST"])
@auth_required
def create_deger():
    """Create a new value."""
    try:
        data = request.get_json()
        if not data or "Deger_Adi" not in data or "Gecerli_Baslangic_Tarih" not in data or "Deger" not in data:
            return jsonify({"error": "Deger_Adi, Gecerli_Baslangic_Tarih, and Deger are required"}), 400
        
        db = get_db_session()
        new_deger = queries.create_deger(
            db,
            deger_adi=data["Deger_Adi"],
            baslangic_tarih=data["Gecerli_Baslangic_Tarih"],
            deger_value=float(data["Deger"]),
            bitis_tarih=data.get("Gecerli_Bitis_Tarih"),
            aciklama=data.get("Deger_Aciklama")
        )
        db.close()
        
        result = {
            "Deger_ID": new_deger.Deger_ID,
            "Deger_Adi": new_deger.Deger_Adi,
            "Gecerli_Baslangic_Tarih": new_deger.Gecerli_Baslangic_Tarih.isoformat(),
            "Gecerli_Bitis_Tarih": new_deger.Gecerli_Bitis_Tarih.isoformat(),
            "Deger_Aciklama": new_deger.Deger_Aciklama,
            "Deger": float(new_deger.Deger),
        }
        
        return jsonify(result), 201
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@reference_bp.route("/degerler/<int:deger_id>", methods=["PUT"])
@auth_required
def update_deger(deger_id):
    """Update a value."""
    try:
        data = request.get_json()
        
        db = get_db_session()
        # Convert Deger to float if provided
        deger_value = float(data.get("Deger")) if "Deger" in data else None
        
        updated_deger = queries.update_deger(
            db,
            deger_id,
            deger_adi=data.get("Deger_Adi"),
            baslangic_tarih=data.get("Gecerli_Baslangic_Tarih"),
            bitis_tarih=data.get("Gecerli_Bitis_Tarih"),
            deger_value=deger_value,
            aciklama=data.get("Deger_Aciklama")
        )
        db.close()
        
        if not updated_deger:
            return jsonify({"error": "Deger not found"}), 404
        
        result = {
            "Deger_ID": updated_deger.Deger_ID,
            "Deger_Adi": updated_deger.Deger_Adi,
            "Gecerli_Baslangic_Tarih": updated_deger.Gecerli_Baslangic_Tarih.isoformat(),
            "Gecerli_Bitis_Tarih": updated_deger.Gecerli_Bitis_Tarih.isoformat(),
            "Deger_Aciklama": updated_deger.Deger_Aciklama,
            "Deger": float(updated_deger.Deger),
        }
        
        return jsonify(result), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@reference_bp.route("/degerler/<int:deger_id>", methods=["DELETE"])
@auth_required
def delete_deger(deger_id):
    """Delete a value."""
    try:
        db = get_db_session()
        deleted = queries.delete_deger(db, deger_id)
        db.close()
        
        if not deleted:
            return jsonify({"error": "Deger not found"}), 404
        
        return jsonify({"message": "Deger deleted"}), 204
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# ============================================================================
# KULLANICI (USERS) ENDPOINTS
# ============================================================================

@reference_bp.route("/kullanicilar", methods=["GET"])
@auth_required
def list_kullanicilar():
    """Get all users with pagination."""
    try:
        skip = request.args.get("skip", 0, type=int)
        limit = min(request.args.get("limit", 100, type=int), 1000)
        
        db = get_db_session()
        kullanicilar = queries.get_kullanicilar(db, skip, limit, aktif_only=True)
        db.close()
        
        result = [
            {
                "Kullanici_ID": k.Kullanici_ID,
                "Adi_Soyadi": k.Adi_Soyadi,
                "Kullanici_Adi": k.Kullanici_Adi,
                "Email": k.Email,
                "Expire_Date": k.Expire_Date.isoformat() if k.Expire_Date else None,
                "Aktif_Pasif": k.Aktif_Pasif,
            }
            for k in kullanicilar
        ]
        
        return jsonify(result), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@reference_bp.route("/kullanicilar/<int:kullanici_id>", methods=["GET"])
@auth_required
def get_kullanici(kullanici_id):
    """Get a user by ID."""
    try:
        db = get_db_session()
        kullanici = queries.get_kullanici_by_id(db, kullanici_id)
        db.close()
        
        if not kullanici:
            return jsonify({"error": "Kullanici not found"}), 404
        
        result = {
            "Kullanici_ID": kullanici.Kullanici_ID,
            "Adi_Soyadi": kullanici.Adi_Soyadi,
            "Kullanici_Adi": kullanici.Kullanici_Adi,
            "Email": kullanici.Email,
            "Expire_Date": kullanici.Expire_Date.isoformat() if kullanici.Expire_Date else None,
            "Aktif_Pasif": kullanici.Aktif_Pasif,
        }
        
        return jsonify(result), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500
