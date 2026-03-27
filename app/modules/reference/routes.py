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
        from app.modules.auth import queries as auth_queries
        user = request.user
        is_admin = (user.Kullanici_Adi and user.Kullanici_Adi.lower() == 'admin')
        if not is_admin:
            roles = auth_queries.get_user_roles(db, user.Kullanici_ID)
            is_admin = 'admin' in [r.lower() for r in roles]
        can_view_gizli = is_admin or auth_queries.has_permission(db, user.Kullanici_ID, "Gizli Kategori Veri Erişimi")

        kategoriler = queries.get_kategoriler(
            db, skip, limit, ust_kategori_id, tip, aktif_only, can_view_gizli=can_view_gizli
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


@reference_bp.route("/kullanicilar", methods=["POST"])
@auth_required
def create_kullanici():
    """Create a new user."""
    from app.modules.auth.security import get_password_hash
    from app.models.models import Kullanici
    
    try:
        data = request.get_json()
        if not data:
            return jsonify({"error": "No data provided"}), 400
            
        required_fields = ["Kullanici_Adi", "Adi_Soyadi", "Sifre"]
        for field in required_fields:
            if field not in data or not data[field]:
                return jsonify({"error": f"Missing required field: {field}"}), 400
                
        db = get_db_session()
        
        # Check if username exists
        existing_user = db.query(Kullanici).filter(Kullanici.Kullanici_Adi == data["Kullanici_Adi"]).first()
        if existing_user:
            db.close()
            return jsonify({"error": "Bu kullanıcı adı zaten kullanılıyor."}), 400
            
        hashed_password = get_password_hash(data["Sifre"])
        
        new_kullanici = Kullanici(
            Kullanici_Adi=data["Kullanici_Adi"],
            Adi_Soyadi=data["Adi_Soyadi"],
            Password=hashed_password,
            Email=data.get("Email"),
            Aktif_Pasif=data.get("Aktif_Pasif", True)
        )
        
        db.add(new_kullanici)
        db.commit()
        db.refresh(new_kullanici)
        db.close()
        
        return jsonify({"message": "User created successfully", "Kullanici_ID": new_kullanici.Kullanici_ID}), 201
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@reference_bp.route("/kullanicilar/<int:kullanici_id>", methods=["PUT"])
@auth_required
def update_kullanici(kullanici_id):
    """Update an existing user."""
    from app.modules.auth.security import get_password_hash
    from app.models.models import Kullanici
    
    try:
        data = request.get_json()
        if not data:
            return jsonify({"error": "No data provided"}), 400
            
        db = get_db_session()
        kullanici = db.query(Kullanici).filter(Kullanici.Kullanici_ID == kullanici_id).first()
        
        if not kullanici:
            db.close()
            return jsonify({"error": "User not found"}), 404
            
        if "Kullanici_Adi" in data and data["Kullanici_Adi"] != kullanici.Kullanici_Adi:
            existing_user = db.query(Kullanici).filter(Kullanici.Kullanici_Adi == data["Kullanici_Adi"]).first()
            if existing_user:
                db.close()
                return jsonify({"error": "Bu kullanıcı adı zaten kullanılıyor."}), 400
            kullanici.Kullanici_Adi = data["Kullanici_Adi"]
            
        if "Adi_Soyadi" in data:
            kullanici.Adi_Soyadi = data["Adi_Soyadi"]
        if "Email" in data:
            kullanici.Email = data["Email"]
        if "Sifre" in data and data["Sifre"]:
            kullanici.Password = get_password_hash(data["Sifre"])
        if "Aktif_Pasif" in data:
            kullanici.Aktif_Pasif = data["Aktif_Pasif"]
            
        db.commit()
        db.close()
        
        return jsonify({"message": "User updated successfully"}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# ============================================================================
# ROL (ROLES) ENDPOINTS
# ============================================================================

@reference_bp.route("/roller", methods=["GET"])
@auth_required
def list_roller():
    """Get all roles with optional filtering."""
    try:
        skip = request.args.get("skip", 0, type=int)
        limit = min(request.args.get("limit", 100, type=int), 1000)
        rol_adi = request.args.get("rol_adi", None, type=str)
        
        db = get_db_session()
        roller = queries.get_roller(db, skip, limit, rol_adi)
        db.close()
        
        result = [
            {
                "Rol_ID": r.Rol_ID,
                "Rol_Adi": r.Rol_Adi,
                "Aciklama": r.Aciklama,
                "Aktif_Pasif": r.Aktif_Pasif,
            }
            for r in roller
        ]
        
        return jsonify(result), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@reference_bp.route("/roller/<int:rol_id>", methods=["GET"])
@auth_required
def get_rol(rol_id):
    """Get a role by ID."""
    try:
        db = get_db_session()
        rol = queries.get_rol_by_id(db, rol_id)
        db.close()
        
        if not rol:
            return jsonify({"error": "Role not found"}), 404
            
        result = {
            "Rol_ID": rol.Rol_ID,
            "Rol_Adi": rol.Rol_Adi,
            "Aciklama": rol.Aciklama,
            "Aktif_Pasif": rol.Aktif_Pasif,
        }
        
        return jsonify(result), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@reference_bp.route("/roller", methods=["POST"])
@auth_required
def create_rol():
    """Create a new role."""
    try:
        data = request.get_json()
        if not data:
            return jsonify({"error": "No data provided"}), 400
            
        if "Rol_Adi" not in data or not data["Rol_Adi"]:
            return jsonify({"error": "Missing required field: Rol_Adi"}), 400
            
        db = get_db_session()
        # Check if role name already exists
        existing = queries.get_roller(db, rol_adi=data["Rol_Adi"])
        if existing and any(e.Rol_Adi.lower() == data["Rol_Adi"].lower() for e in existing):
            db.close()
            return jsonify({"error": "A role with this name already exists"}), 400
            
        rol = queries.create_rol(
            db,
            rol_adi=data["Rol_Adi"],
            aciklama=data.get("Aciklama"),
            aktif_pasif=data.get("Aktif_Pasif", True)
        )
        
        result = {
            "Rol_ID": rol.Rol_ID,
            "Rol_Adi": rol.Rol_Adi,
            "Aciklama": rol.Aciklama,
            "Aktif_Pasif": rol.Aktif_Pasif,
        }
        
        db.close()
        return jsonify(result), 201
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@reference_bp.route("/roller/<int:rol_id>", methods=["PUT"])
@auth_required
def update_rol(rol_id):
    """Update an existing role."""
    try:
        data = request.get_json()
        if not data:
            return jsonify({"error": "No data provided"}), 400
            
        db = get_db_session()
        rol = queries.get_rol_by_id(db, rol_id)
        
        if not rol:
            db.close()
            return jsonify({"error": "Role not found"}), 404
            
        # Check if new name exists and belongs to another role
        if "Rol_Adi" in data and data["Rol_Adi"] != rol.Rol_Adi:
            existing = queries.get_roller(db, rol_adi=data["Rol_Adi"])
            if existing and any(e.Rol_Adi.lower() == data["Rol_Adi"].lower() and e.Rol_ID != rol_id for e in existing):
                db.close()
                return jsonify({"error": "A role with this name already exists"}), 400
                
        updated_rol = queries.update_rol(
            db,
            rol,
            rol_adi=data.get("Rol_Adi"),
            aciklama=data.get("Aciklama"),
            aktif_pasif=data.get("Aktif_Pasif")
        )
        
        result = {
            "Rol_ID": updated_rol.Rol_ID,
            "Rol_Adi": updated_rol.Rol_Adi,
            "Aciklama": updated_rol.Aciklama,
            "Aktif_Pasif": updated_rol.Aktif_Pasif,
        }
        
        db.close()
        return jsonify(result), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@reference_bp.route("/roller/<int:rol_id>", methods=["DELETE"])
@auth_required
def delete_rol(rol_id):
    """Delete a role."""
    try:
        db = get_db_session()
        rol = queries.get_rol_by_id(db, rol_id)
        
        if not rol:
            db.close()
            return jsonify({"error": "Role not found"}), 404
            
        # Optional: check if role is used in KullaniciRol or RolYetki before deleting
        from app.models.models import KullaniciRol, RolYetki
        if db.query(KullaniciRol).filter_by(Rol_ID=rol_id).first() or \
           db.query(RolYetki).filter_by(Rol_ID=rol_id).first():
            db.close()
            return jsonify({"error": "Cannot delete role because it is assigned to users or has permissions attached."}), 400
            
        queries.delete_rol(db, rol)
        db.close()
        
        return jsonify({"message": "Role deleted successfully"}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# ============================================================================
# YETKİ (PERMISSIONS) ENDPOINTS
# ============================================================================

@reference_bp.route("/yetkiler", methods=["GET"])
@auth_required
def list_yetkiler():
    """Get all permissions with optional filtering."""
    try:
        skip = request.args.get("skip", 0, type=int)
        limit = min(request.args.get("limit", 100, type=int), 1000)
        yetki_adi = request.args.get("yetki_adi", None, type=str)
        
        db = get_db_session()
        yetkiler = queries.get_yetkiler(db, skip, limit, yetki_adi)
        db.close()
        
        result = [
            {
                "Yetki_ID": y.Yetki_ID,
                "Yetki_Adi": y.Yetki_Adi,
                "Aciklama": y.Aciklama,
                "Tip": y.Tip,
                "Aktif_Pasif": y.Aktif_Pasif,
            }
            for y in yetkiler
        ]
        
        return jsonify(result), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@reference_bp.route("/yetkiler/<int:yetki_id>", methods=["GET"])
@auth_required
def get_yetki(yetki_id):
    """Get a permission by ID."""
    try:
        db = get_db_session()
        yetki = queries.get_yetki_by_id(db, yetki_id)
        db.close()
        
        if not yetki:
            return jsonify({"error": "Permission not found"}), 404
            
        result = {
            "Yetki_ID": yetki.Yetki_ID,
            "Yetki_Adi": yetki.Yetki_Adi,
            "Aciklama": yetki.Aciklama,
            "Tip": yetki.Tip,
            "Aktif_Pasif": yetki.Aktif_Pasif,
        }
        
        return jsonify(result), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@reference_bp.route("/yetkiler", methods=["POST"])
@auth_required
def create_yetki():
    """Create a new permission."""
    try:
        data = request.get_json()
        if not data:
            return jsonify({"error": "No data provided"}), 400
            
        if "Yetki_Adi" not in data or not data["Yetki_Adi"]:
            return jsonify({"error": "Missing required field: Yetki_Adi"}), 400
            
        db = get_db_session()
        existing = queries.get_yetkiler(db, yetki_adi=data["Yetki_Adi"])
        if existing and any(e.Yetki_Adi.lower() == data["Yetki_Adi"].lower() for e in existing):
            db.close()
            return jsonify({"error": "A permission with this name already exists"}), 400
            
        yetki = queries.create_yetki(
            db,
            yetki_adi=data["Yetki_Adi"],
            aciklama=data.get("Aciklama"),
            tip=data.get("Tip"),
            aktif_pasif=data.get("Aktif_Pasif", True)
        )
        
        result = {
            "Yetki_ID": yetki.Yetki_ID,
            "Yetki_Adi": yetki.Yetki_Adi,
            "Aciklama": yetki.Aciklama,
            "Tip": yetki.Tip,
            "Aktif_Pasif": yetki.Aktif_Pasif,
        }
        
        db.close()
        return jsonify(result), 201
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@reference_bp.route("/yetkiler/<int:yetki_id>", methods=["PUT"])
@auth_required
def update_yetki(yetki_id):
    """Update an existing permission."""
    try:
        data = request.get_json()
        if not data:
            return jsonify({"error": "No data provided"}), 400
            
        db = get_db_session()
        yetki = queries.get_yetki_by_id(db, yetki_id)
        
        if not yetki:
            db.close()
            return jsonify({"error": "Permission not found"}), 404
            
        if "Yetki_Adi" in data and data["Yetki_Adi"] != yetki.Yetki_Adi:
            existing = queries.get_yetkiler(db, yetki_adi=data["Yetki_Adi"])
            if existing and any(e.Yetki_Adi.lower() == data["Yetki_Adi"].lower() and e.Yetki_ID != yetki_id for e in existing):
                db.close()
                return jsonify({"error": "A permission with this name already exists"}), 400
                
        updated_yetki = queries.update_yetki(
            db,
            yetki,
            yetki_adi=data.get("Yetki_Adi"),
            aciklama=data.get("Aciklama"),
            tip=data.get("Tip"),
            aktif_pasif=data.get("Aktif_Pasif")
        )
        
        result = {
            "Yetki_ID": updated_yetki.Yetki_ID,
            "Yetki_Adi": updated_yetki.Yetki_Adi,
            "Aciklama": updated_yetki.Aciklama,
            "Tip": updated_yetki.Tip,
            "Aktif_Pasif": updated_yetki.Aktif_Pasif,
        }
        
        db.close()
        return jsonify(result), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@reference_bp.route("/yetkiler/<int:yetki_id>", methods=["DELETE"])
@auth_required
def delete_yetki(yetki_id):
    """Delete a permission."""
    try:
        db = get_db_session()
        yetki = queries.get_yetki_by_id(db, yetki_id)
        
        if not yetki:
            db.close()
            return jsonify({"error": "Permission not found"}), 404
            
        from app.models.models import RolYetki
        if db.query(RolYetki).filter_by(Yetki_ID=yetki_id).first():
            db.close()
            return jsonify({"error": "Cannot delete permission because it is assigned to roles."}), 400
            
        queries.delete_yetki(db, yetki)
        db.close()
        
        return jsonify({"message": "Permission deleted successfully"}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# ============================================================================
# KULLANICI-ROL ATAMA ENDPOINTS
# ============================================================================

@reference_bp.route("/kullanici-rol-atamalari", methods=["GET"])
@auth_required
def list_kullanici_rol_atamalari():
    try:
        skip = request.args.get("skip", 0, type=int)
        limit = min(request.args.get("limit", 100, type=int), 1000)
        kullanici_id = request.args.get("kullanici_id", None, type=int)
        
        db = get_db_session()
        atamalar = queries.get_kullanici_rolleri(db, skip, limit, kullanici_id)
        
        result = []
        for a in atamalar:
            result.append({
                "Kullanici_ID": a.Kullanici_ID,
                "Rol_ID": a.Rol_ID,
                "Sube_ID": a.Sube_ID,
                "Aktif_Pasif": a.Aktif_Pasif,
                "Kullanici_Adi": a.kullanici.Adi_Soyadi if a.kullanici else None,
                "Kullanici_Login": a.kullanici.Kullanici_Adi if a.kullanici else None,
                "Rol_Adi": a.rol.Rol_Adi if a.rol else None,
                "Sube_Adi": a.sube.Sube_Adi if a.sube else None
            })
            
        db.close()
        return jsonify(result), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@reference_bp.route("/kullanici-rol-atamalari", methods=["POST"])
@auth_required
def create_kullanici_rol_atama():
    try:
        data = request.get_json()
        if not data:
            return jsonify({"error": "No data provided"}), 400
            
        required_fields = ["Kullanici_ID", "Rol_ID", "Sube_ID"]
        for field in required_fields:
            if field not in data:
                return jsonify({"error": f"Missing required field: {field}"}), 400
                
        db = get_db_session()
        
        existing = queries.get_kullanici_rol(db, data["Kullanici_ID"], data["Rol_ID"], data["Sube_ID"])
        if existing:
            db.close()
            return jsonify({"error": "This role is already assigned to this user for the specified branch."}), 400
            
        atama = queries.create_kullanici_rol(
            db,
            kullanici_id=data["Kullanici_ID"],
            rol_id=data["Rol_ID"],
            sube_id=data["Sube_ID"],
            aktif_pasif=data.get("Aktif_Pasif", True)
        )
        
        db.close()
        return jsonify({"message": "Role assigned successfully"}), 201
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@reference_bp.route("/kullanici-rol-atamalari/<int:k_id>/<int:r_id>/<int:s_id>", methods=["PUT"])
@auth_required
def update_kullanici_rol_atama(k_id, r_id, s_id):
    try:
        data = request.get_json()
        if not data:
            return jsonify({"error": "No data provided"}), 400
            
        db = get_db_session()
        atama = queries.get_kullanici_rol(db, k_id, r_id, s_id)
        
        if not atama:
            db.close()
            return jsonify({"error": "Assignment not found"}), 404
            
        if "Aktif_Pasif" in data:
            queries.update_kullanici_rol(db, atama, data["Aktif_Pasif"])
            
        db.close()
        return jsonify({"message": "Assignment updated"}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@reference_bp.route("/kullanici-rol-atamalari/<int:k_id>/<int:r_id>/<int:s_id>", methods=["DELETE"])
@auth_required
def delete_kullanici_rol_atama(k_id, r_id, s_id):
    try:
        db = get_db_session()
        atama = queries.get_kullanici_rol(db, k_id, r_id, s_id)
        
        if not atama:
            db.close()
            return jsonify({"error": "Assignment not found"}), 404
            
        queries.delete_kullanici_rol(db, atama)
        db.close()
        
        return jsonify({"message": "Assignment deleted successfully"}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# ============================================================================
# ROL-YETKİ ATAMA ENDPOINTS
# ============================================================================

@reference_bp.route("/rol-yetki-atamalari", methods=["GET"])
@auth_required
def list_rol_yetki_atamalari():
    try:
        skip = request.args.get("skip", 0, type=int)
        limit = min(request.args.get("limit", 100, type=int), 1000)
        rol_id = request.args.get("rol_id", None, type=int)
        
        db = get_db_session()
        atamalar = queries.get_rol_yetkileri(db, skip, limit, rol_id)
        
        result = []
        for a in atamalar:
            result.append({
                "Rol_ID": a.Rol_ID,
                "Yetki_ID": a.Yetki_ID,
                "Aktif_Pasif": a.Aktif_Pasif,
                "Rol_Adi": a.rol.Rol_Adi if a.rol else None,
                "Yetki_Adi": a.yetki.Yetki_Adi if a.yetki else None,
                "Tip": a.yetki.Tip if a.yetki else None
            })
            
        db.close()
        return jsonify(result), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@reference_bp.route("/rol-yetki-atamalari", methods=["POST"])
@auth_required
def create_rol_yetki_atama():
    try:
        data = request.get_json()
        if not data:
            return jsonify({"error": "No data provided"}), 400
            
        required_fields = ["Rol_ID", "Yetki_ID"]
        for field in required_fields:
            if field not in data:
                return jsonify({"error": f"Missing required field: {field}"}), 400
                
        db = get_db_session()
        
        existing = queries.get_rol_yetki(db, data["Rol_ID"], data["Yetki_ID"])
        if existing:
            db.close()
            return jsonify({"error": "This permission is already assigned to this role."}), 400
            
        atama = queries.create_rol_yetki(
            db,
            rol_id=data["Rol_ID"],
            yetki_id=data["Yetki_ID"],
            aktif_pasif=data.get("Aktif_Pasif", True)
        )
        
        db.close()
        return jsonify({"message": "Permission assigned to role successfully"}), 201
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@reference_bp.route("/rol-yetki-atamalari/<int:r_id>/<int:y_id>", methods=["PUT"])
@auth_required
def update_rol_yetki_atama(r_id, y_id):
    try:
        data = request.get_json()
        if not data:
            return jsonify({"error": "No data provided"}), 400
            
        db = get_db_session()
        atama = queries.get_rol_yetki(db, r_id, y_id)
        
        if not atama:
            db.close()
            return jsonify({"error": "Assignment not found"}), 404
            
        if "Aktif_Pasif" in data:
            queries.update_rol_yetki(db, atama, data["Aktif_Pasif"])
            
        db.close()
        return jsonify({"message": "Assignment updated"}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@reference_bp.route("/rol-yetki-atamalari/<int:r_id>/<int:y_id>", methods=["DELETE"])
@auth_required
def delete_rol_yetki_atama(r_id, y_id):
    try:
        db = get_db_session()
        atama = queries.get_rol_yetki(db, r_id, y_id)
        
        if not atama:
            db.close()
            return jsonify({"error": "Assignment not found"}), 404
            
        queries.delete_rol_yetki(db, atama)
        db.close()
        
        return jsonify({"message": "Assignment deleted successfully"}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# ============================================================================
# E-FATURA REFERANS ENDPOINTS
# ============================================================================

@reference_bp.route("/efatura-referans-yonetimi", methods=["GET"])
@auth_required
def list_efatura_referanslar():
    try:
        skip = request.args.get("skip", 0, type=int)
        limit = min(request.args.get("limit", 1000, type=int), 5000)
        search = request.args.get("search", None, type=str)
        
        db = get_db_session()
        referanslar = queries.get_efatura_referanslar(db, skip, limit, search)
        db.close()
        
        result = [
            {
                "Alici_Unvani": r.Alici_Unvani,
                "Referans_Kodu": r.Referans_Kodu,
                "Kategori_ID": r.Kategori_ID,
                "Kategori_Adi": r.kategori.Kategori_Adi if r.kategori else "Belirsiz",
                "Aciklama": r.Aciklama,
                "Aktif_Pasif": r.Aktif_Pasif,
            }
            for r in referanslar
        ]
        
        return jsonify(result), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@reference_bp.route("/efatura-referans-yonetimi", methods=["POST"])
@auth_required
def create_efatura_referans():
    try:
        data = request.get_json()
        if not data or "Alici_Unvani" not in data or "Kategori_ID" not in data:
            return jsonify({"error": "Alici_Unvani and Kategori_ID required"}), 400
            
        db = get_db_session()
        
        # Check if already exists
        existing = queries.get_efatura_referans_by_unvan(db, data["Alici_Unvani"])
        if existing:
            db.close()
            return jsonify({"error": "This buyer title already has a reference."}), 400
            
        new_ref = queries.create_efatura_referans(
            db,
            alici_unvani=data["Alici_Unvani"],
            kategori_id=data["Kategori_ID"],
            referans_kodu=data.get("Referans_Kodu", "TANIMSIZ"),
            aciklama=data.get("Aciklama"),
            aktif_pasif=data.get("Aktif_Pasif", True)
        )
        
        result = {
            "Alici_Unvani": new_ref.Alici_Unvani,
            "Kategori_ID": new_ref.Kategori_ID
        }
        db.close()
        return jsonify(result), 201
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@reference_bp.route("/efatura-referans-yonetimi/<path:alici_unvani>", methods=["PUT"])
@auth_required
def update_efatura_referans(alici_unvani):
    try:
        data = request.get_json()
        db = get_db_session()
        
        db_ref = queries.get_efatura_referans_by_unvan(db, alici_unvani)
        if not db_ref:
            db.close()
            return jsonify({"error": "Reference not found"}), 404
            
        updated_ref = queries.update_efatura_referans(
            db,
            db_ref,
            kategori_id=data.get("Kategori_ID"),
            aktif_pasif=data.get("Aktif_Pasif")
        )
        
        result = {
            "Alici_Unvani": updated_ref.Alici_Unvani,
            "Kategori_ID": updated_ref.Kategori_ID,
            "Aktif_Pasif": updated_ref.Aktif_Pasif
        }
        db.close()
        return jsonify(result), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@reference_bp.route("/efatura-referans-yonetimi/<path:alici_unvani>", methods=["DELETE"])
@auth_required
def delete_efatura_referans(alici_unvani):
    try:
        db = get_db_session()
        db_ref = queries.get_efatura_referans_by_unvan(db, alici_unvani)
        if not db_ref:
            db.close()
            return jsonify({"error": "Reference not found"}), 404
            
        queries.delete_efatura_referans(db, db_ref)
        db.close()
        return "", 204
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# ============================================================================
# ÖDEME REFERANS ENDPOINTS
# ============================================================================

@reference_bp.route("/odeme-referans-yonetimi", methods=["GET"])
@auth_required
def list_odeme_referanslar():
    try:
        skip = request.args.get("skip", 0, type=int)
        limit = min(request.args.get("limit", 1000, type=int), 5000)
        search = request.args.get("search", None, type=str)
        
        db = get_db_session()
        referanslar = queries.get_odeme_referanslar(db, skip, limit, search)
        db.close()
        
        result = [
            {
                "Referans_ID": r.Referans_ID,
                "Referans_Metin": r.Referans_Metin,
                "Kategori_ID": r.Kategori_ID,
                "Kategori_Adi": r.kategori.Kategori_Adi if r.kategori else "Belirsiz",
                "Aktif_Pasif": r.Aktif_Pasif,
            }
            for r in referanslar
        ]
        
        return jsonify(result), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@reference_bp.route("/odeme-referans-yonetimi", methods=["POST"])
@auth_required
def create_odeme_referans():
    try:
        data = request.get_json()
        if not data or "Referans_Metin" not in data or "Kategori_ID" not in data:
            return jsonify({"error": "Referans_Metin and Kategori_ID required"}), 400
            
        db = get_db_session()
        
        # Check if already exists
        existing = queries.get_odeme_referans_by_metin(db, data["Referans_Metin"])
        if existing:
            db.close()
            return jsonify({"error": "This reference text already exists."}), 400
            
        new_ref = queries.create_odeme_referans(
            db,
            referans_metin=data["Referans_Metin"],
            kategori_id=data["Kategori_ID"],
            aktif_pasif=data.get("Aktif_Pasif", True)
        )
        
        result = {
            "Referans_ID": new_ref.Referans_ID,
            "Referans_Metin": new_ref.Referans_Metin,
            "Kategori_ID": new_ref.Kategori_ID
        }
        db.close()
        return jsonify(result), 201
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@reference_bp.route("/odeme-referans-yonetimi/<int:referans_id>", methods=["PUT"])
@auth_required
def update_odeme_referans(referans_id):
    try:
        data = request.get_json()
        db = get_db_session()
        
        db_ref = queries.get_odeme_referans_by_id(db, referans_id)
        if not db_ref:
            db.close()
            return jsonify({"error": "Reference not found"}), 404
            
        updated_ref = queries.update_odeme_referans(
            db,
            db_ref,
            kategori_id=data.get("Kategori_ID"),
            aktif_pasif=data.get("Aktif_Pasif")
        )
        
        result = {
            "Referans_ID": updated_ref.Referans_ID,
            "Referans_Metin": updated_ref.Referans_Metin,
            "Kategori_ID": updated_ref.Kategori_ID,
            "Aktif_Pasif": updated_ref.Aktif_Pasif
        }
        db.close()
        return jsonify(result), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@reference_bp.route("/odeme-referans-yonetimi/<int:referans_id>", methods=["DELETE"])
@auth_required
def delete_odeme_referans(referans_id):
    try:
        db = get_db_session()
        db_ref = queries.get_odeme_referans_by_id(db, referans_id)
        if not db_ref:
            db.close()
            return jsonify({"error": "Reference not found"}), 404
            
        queries.delete_odeme_referans(db, db_ref)
        db.close()
        return "", 204
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# ============================================================================
# GELİR REFERANS (RobotposGelirReferans) ENDPOINTS
# ============================================================================

@reference_bp.route("/gelir-referans-yonetimi", methods=["GET"])
@auth_required
def list_gelir_referanslar():
    try:
        skip = request.args.get("skip", 0, type=int)
        limit = min(request.args.get("limit", 1000, type=int), 5000)
        search = request.args.get("search", None, type=str)
        
        db = get_db_session()
        referanslar = queries.get_gelir_referanslar(db, skip, limit, search)
        db.close()
        
        result = [
            {
                "Referans_ID": r.Robotpos_Gelir_Referans_ID,
                "Odeme_Tipi": r.Odeme_Tipi,
                "Kategori_ID": r.Kategori_ID,
                "Kategori_Adi": r.kategori.Kategori_Adi if r.kategori else "Belirsiz",
                "Aktif_Pasif": r.Aktif_Pasif,
            }
            for r in referanslar
        ]
        
        return jsonify(result), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@reference_bp.route("/gelir-referans-yonetimi", methods=["POST"])
@auth_required
def create_gelir_referans():
    try:
        data = request.get_json()
        if not data or "Odeme_Tipi" not in data or "Kategori_ID" not in data:
            return jsonify({"error": "Odeme_Tipi and Kategori_ID required"}), 400
            
        db = get_db_session()
        
        # Check if already exists
        existing = queries.get_gelir_referans_by_tip(db, data["Odeme_Tipi"])
        if existing:
            db.close()
            return jsonify({"error": "Bu ödeme tipi zaten tanımlanmış."}), 400
            
        new_ref = queries.create_gelir_referans(
            db,
            odeme_tipi=data["Odeme_Tipi"],
            kategori_id=data["Kategori_ID"],
            aktif_pasif=data.get("Aktif_Pasif", True)
        )
        
        result = {
            "Referans_ID": new_ref.Robotpos_Gelir_Referans_ID,
            "Odeme_Tipi": new_ref.Odeme_Tipi,
            "Kategori_ID": new_ref.Kategori_ID
        }
        db.close()
        return jsonify(result), 201
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@reference_bp.route("/gelir-referans-yonetimi/<int:referans_id>", methods=["PUT"])
@auth_required
def update_gelir_referans(referans_id):
    try:
        data = request.get_json()
        db = get_db_session()
        
        db_ref = queries.get_gelir_referans_by_id(db, referans_id)
        if not db_ref:
            db.close()
            return jsonify({"error": "Referans bulunamadı"}), 404
            
        # Check uniqueness if Odeme_Tipi is changed
        if "Odeme_Tipi" in data and data["Odeme_Tipi"] != db_ref.Odeme_Tipi:
            existing = queries.get_gelir_referans_by_tip(db, data["Odeme_Tipi"])
            if existing:
                db.close()
                return jsonify({"error": "Bu ödeme tipi zaten tanımlanmış."}), 400
        
        updated_ref = queries.update_gelir_referans(
            db,
            db_ref,
            odeme_tipi=data.get("Odeme_Tipi"),
            kategori_id=data.get("Kategori_ID"),
            aktif_pasif=data.get("Aktif_Pasif")
        )
        
        result = {
            "Referans_ID": updated_ref.Robotpos_Gelir_Referans_ID,
            "Odeme_Tipi": updated_ref.Odeme_Tipi,
            "Kategori_ID": updated_ref.Kategori_ID,
            "Aktif_Pasif": updated_ref.Aktif_Pasif
        }
        db.close()
        return jsonify(result), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@reference_bp.route("/gelir-referans-yonetimi/<int:referans_id>", methods=["DELETE"])
@auth_required
def delete_gelir_referans(referans_id):
    try:
        db = get_db_session()
        db_ref = queries.get_gelir_referans_by_id(db, referans_id)
        if not db_ref:
            db.close()
            return jsonify({"error": "Referans bulunamadı"}), 404
            
        queries.delete_gelir_referans(db, db_ref)
        db.close()
        return "", 204
    except Exception as e:
        return jsonify({"error": str(e)}), 500
# ============================================================================
# CARI (CLIENTS) ENDPOINTS
# ============================================================================

@reference_bp.route("/cari-yonetimi", methods=["GET"])
@auth_required
def list_cariler():
    try:
        skip = request.args.get("skip", 0, type=int)
        limit = min(request.args.get("limit", 1000, type=int), 5000)
        search = request.args.get("search", None, type=str)
        
        db = get_db_session()
        cariler = queries.get_cariler(db, skip, limit, search)
        
        result = [
            {
                "Cari_ID": c.Cari_ID,
                "Alici_Unvani": c.Alici_Unvani,
                "e_Fatura_Kategori_ID": c.e_Fatura_Kategori_ID,
                "Referans_ID": c.Referans_ID,
                "Referans_Detay": (
                    f"#{c.referans.Referans_ID} ({c.referans.Referans_Metin} - {c.referans.kategori.Kategori_Adi})"
                    if c.referans else None
                ),
                "Cari": c.Cari,
                "Aciklama": c.Aciklama,
                "Aktif_Pasif": c.Aktif_Pasif,
            }
            for c in cariler
        ]
        db.close()
        return jsonify(result), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@reference_bp.route("/cari-yonetimi", methods=["POST"])
@auth_required
def create_cari():
    try:
        data = request.get_json()
        if not data or "Alici_Unvani" not in data:
            return jsonify({"error": "Alici_Unvani required"}), 400
            
        db = get_db_session()
        new_cari = queries.create_cari(
            db,
            alici_unvani=data["Alici_Unvani"],
            e_fatura_kategori_id=data.get("e_Fatura_Kategori_ID"),
            referans_id=data.get("Referans_ID"),
            cari=data.get("Cari", True),
            aciklama=data.get("Aciklama"),
            aktif_pasif=data.get("Aktif_Pasif", True)
        )
        
        result = {
            "Cari_ID": new_cari.Cari_ID,
            "Alici_Unvani": new_cari.Alici_Unvani
        }
        db.close()
        return jsonify(result), 201
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@reference_bp.route("/cari-yonetimi/<int:cari_id>", methods=["PUT"])
@auth_required
def update_cari(cari_id):
    try:
        data = request.get_json()
        db = get_db_session()
        
        db_cari = queries.get_cari_by_id(db, cari_id)
        if not db_cari:
            db.close()
            return jsonify({"error": "Cari not found"}), 404
            
        updated_cari = queries.update_cari(
            db,
            db_cari,
            alici_unvani=data.get("Alici_Unvani"),
            e_fatura_kategori_id=data.get("e_Fatura_Kategori_ID"),
            referans_id=data.get("Referans_ID"),
            cari=data.get("Cari"),
            aciklama=data.get("Aciklama"),
            aktif_pasif=data.get("Aktif_Pasif")
        )
        
        result = {
            "Cari_ID": updated_cari.Cari_ID,
            "Alici_Unvani": updated_cari.Alici_Unvani,
            "Aktif_Pasif": updated_cari.Aktif_Pasif
        }
        db.close()
        return jsonify(result), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@reference_bp.route("/cari-yonetimi/<int:cari_id>", methods=["DELETE"])
@auth_required
def delete_cari(cari_id):
    try:
        db = get_db_session()
        db_cari = queries.get_cari_by_id(db, cari_id)
        if not db_cari:
            db.close()
            return jsonify({"error": "Cari not found"}), 404
            
        queries.delete_cari(db, db_cari)
        db.close()
        return "", 204
    except Exception as e:
        return jsonify({"error": str(e)}), 500
