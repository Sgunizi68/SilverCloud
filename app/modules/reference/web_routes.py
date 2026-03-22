"""
Reference Web Routes (Server-Rendered)
Pages for Reference domain such as Sube Yonetimi.
"""

from flask import Blueprint, render_template, session, redirect, url_for
from app.common.database import get_db_session
from app.common.decorators import login_required, permission_required
from app.modules.reference import queries
from app.modules.auth import queries as auth_queries

web_reference_bp = Blueprint("web_reference", __name__)

@web_reference_bp.route("/subeler", methods=["GET"])
@login_required
@permission_required("Şube Yönetimi Ekranı Görüntüleme")
def subeler():
    """
    Sube Yonetimi page.
    Shows the list of branches in a server-rendered table.
    """
    db_session = get_db_session()
    
    # Get current user
    user = auth_queries.get_kullanici_by_id(db_session, session['user_id'])
    
    if not user:
        db_session.close()
        return redirect(url_for('web_auth.login'))
        
    # Get all branches to display in the table
    all_suber = queries.get_suber(db_session, limit=1000)
    
    # Also get authorized branches for the topbar dropdown if needed
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
        
    all_suber_list = [
        {
            "Sube_ID": s.Sube_ID,
            "Sube_Adi": s.Sube_Adi,
            "Aciklama": s.Aciklama,
            "Aktif_Pasif": s.Aktif_Pasif
        } for s in all_suber
    ]
    
    auth_suber_list = [
        {
            "Sube_ID": s.Sube_ID,
            "Sube_Adi": s.Sube_Adi,
            "Aciklama": s.Aciklama,
            "Aktif_Pasif": s.Aktif_Pasif
        } for s in auth_suber
    ]
    
    db_session.close()
    
    return render_template(
        "subeler.html",
        user=user,
        subeler=auth_suber_list,      # For topbar dropdown (inherited from base)
        all_suber=all_suber_list      # For the table list
    )


@web_reference_bp.route("/degerler", methods=["GET"])
@login_required
@permission_required("Değer Yönetimi Ekranı Görüntüleme")
def degerler():
    """
    Deger Yonetimi page.
    Shows the list of values in a server-rendered table.
    """
    db_session = get_db_session()

    # Get current user
    user = auth_queries.get_kullanici_by_id(db_session, session['user_id'])

    if not user:
        db_session.close()
        return redirect(url_for('web_auth.login'))

    # Get all branches for topbar dropdown
    all_suber = queries.get_suber(db_session, limit=1000)
    is_admin = (user.Kullanici_Adi and user.Kullanici_Adi.lower() == 'admin')
    if not is_admin:
        roles = auth_queries.get_user_roles(db_session, user.Kullanici_ID)
        is_admin = 'admin' in [r.lower() for r in roles]

    auth_suber = all_suber if is_admin else [
        s for s in all_suber
        if s.Sube_ID in auth_queries.get_user_branches(db_session, user.Kullanici_ID)
    ]
    subeler_list = [{"Sube_ID": s.Sube_ID, "Sube_Adi": s.Sube_Adi} for s in auth_suber]

    # Get all Deger records
    all_degerler = queries.get_degerler(db_session, limit=1000)
    degerler_list = [
        {
            "Deger_ID": d.Deger_ID,
            "Deger_Adi": d.Deger_Adi,
            "Gecerli_Baslangic_Tarih": d.Gecerli_Baslangic_Tarih.isoformat() if d.Gecerli_Baslangic_Tarih else "",
            "Gecerli_Bitis_Tarih": d.Gecerli_Bitis_Tarih.isoformat() if d.Gecerli_Bitis_Tarih else "",
            "Deger": float(d.Deger) if d.Deger is not None else 0,
            "Deger_Aciklama": d.Deger_Aciklama or "",
        }
        for d in all_degerler
    ]

    db_session.close()

    return render_template(
        "degerler.html",
        user=user,
        subeler=subeler_list,
        degerler=degerler_list,
    )


@web_reference_bp.route("/kullanicilar", methods=["GET"])
@login_required
@permission_required("Kullanıcı Yönetimi Ekranı Görüntüleme")
def kullanicilar():
    """
    Kullanici Yonetimi page.
    Shows the list of users in a server-rendered table.
    """
    db_session = get_db_session()

    # Get current user
    user = auth_queries.get_kullanici_by_id(db_session, session['user_id'])

    if not user:
        db_session.close()
        return redirect(url_for('web_auth.login'))

    # Get all branches for topbar dropdown
    all_suber = queries.get_suber(db_session, limit=1000)
    is_admin = (user.Kullanici_Adi and user.Kullanici_Adi.lower() == 'admin')
    if not is_admin:
        roles = auth_queries.get_user_roles(db_session, user.Kullanici_ID)
        is_admin = 'admin' in [r.lower() for r in roles]

    auth_suber = all_suber if is_admin else [
        s for s in all_suber
        if s.Sube_ID in auth_queries.get_user_branches(db_session, user.Kullanici_ID)
    ]
    subeler_list = [{"Sube_ID": s.Sube_ID, "Sube_Adi": s.Sube_Adi} for s in auth_suber]

    # Get all Kullanici records
    all_kullanicilar = queries.get_kullanicilar(db_session, limit=1000, aktif_only=False)
    kullanicilar_list = [
        {
            "Kullanici_ID": k.Kullanici_ID,
            "Adi_Soyadi": k.Adi_Soyadi,
            "Kullanici_Adi": k.Kullanici_Adi,
            "Email": k.Email,
            "Aktif_Pasif": k.Aktif_Pasif,
        }
        for k in all_kullanicilar
    ]

    db_session.close()

    return render_template(
        "kullanicilar.html",
        user=user,
        subeler=subeler_list,
        kullanicilar=kullanicilar_list,
    )


@web_reference_bp.route("/roller", methods=["GET"])
@login_required
@permission_required("Rol Yönetimi Ekranı Görüntüleme")
def roller():
    """
    Rol Yonetimi page.
    Shows the list of roles in a server-rendered table.
    """
    db_session = get_db_session()

    # Get current user
    user = auth_queries.get_kullanici_by_id(db_session, session['user_id'])

    if not user:
        db_session.close()
        return redirect(url_for('web_auth.login'))

    # Get all branches for topbar dropdown
    all_suber = queries.get_suber(db_session, limit=1000)
    is_admin = (user.Kullanici_Adi and user.Kullanici_Adi.lower() == 'admin')
    if not is_admin:
        roles = auth_queries.get_user_roles(db_session, user.Kullanici_ID)
        is_admin = 'admin' in [r.lower() for r in roles]

    auth_suber = all_suber if is_admin else [
        s for s in all_suber
        if s.Sube_ID in auth_queries.get_user_branches(db_session, user.Kullanici_ID)
    ]
    subeler_list = [{"Sube_ID": s.Sube_ID, "Sube_Adi": s.Sube_Adi} for s in auth_suber]

    # Get all Rol records
    all_roller = queries.get_roller(db_session, limit=1000, aktif_only=False)
    roller_list = [
        {
            "Rol_ID": r.Rol_ID,
            "Rol_Adi": r.Rol_Adi,
            "Aciklama": r.Aciklama,
            "Aktif_Pasif": r.Aktif_Pasif,
        }
        for r in all_roller
    ]

    db_session.close()

    return render_template(
        "roller.html",
        user=user,
        subeler=subeler_list,
        roller=roller_list,
    )


@web_reference_bp.route("/yetkiler", methods=["GET"])
@login_required
@permission_required("Yetki Yönetimi Ekranı Görüntüleme")
def yetkiler():
    """
    Yetki Yonetimi page.
    Shows the list of permissions in a server-rendered table.
    """
    db_session = get_db_session()

    # Get current user
    user = auth_queries.get_kullanici_by_id(db_session, session['user_id'])

    if not user:
        db_session.close()
        return redirect(url_for('web_auth.login'))

    # Get all branches for topbar dropdown
    all_suber = queries.get_suber(db_session, limit=1000)
    is_admin = (user.Kullanici_Adi and user.Kullanici_Adi.lower() == 'admin')
    if not is_admin:
        roles = auth_queries.get_user_roles(db_session, user.Kullanici_ID)
        is_admin = 'admin' in [r.lower() for r in roles]

    auth_suber = all_suber if is_admin else [
        s for s in all_suber
        if s.Sube_ID in auth_queries.get_user_branches(db_session, user.Kullanici_ID)
    ]
    subeler_list = [{"Sube_ID": s.Sube_ID, "Sube_Adi": s.Sube_Adi} for s in auth_suber]

    # Get all Yetki records
    all_yetkiler = queries.get_yetkiler(db_session, limit=1000, aktif_only=False)
    yetkiler_list = [
        {
            "Yetki_ID": y.Yetki_ID,
            "Yetki_Adi": y.Yetki_Adi,
            "Aciklama": y.Aciklama,
            "Tip": y.Tip,
            "Aktif_Pasif": y.Aktif_Pasif,
        }
        for y in all_yetkiler
    ]

    db_session.close()

    return render_template(
        "yetkiler.html",
        user=user,
        subeler=subeler_list,
        yetkiler=yetkiler_list,
    )


@web_reference_bp.route("/kullanici-rol-atamalari", methods=["GET"])
@login_required
@permission_required("Kullanıcı Rol Atama Ekranı Görüntüleme")
def kullanici_rol_atamalari():
    """
    Kullanici Rol Atamalari page.
    Shows the list of user-role assignments.
    """
    db_session = get_db_session()

    # Get current user
    user = auth_queries.get_kullanici_by_id(db_session, session['user_id'])

    if not user:
        db_session.close()
        return redirect(url_for('web_auth.login'))

    # Get all branches for topbar dropdown
    all_suber = queries.get_suber(db_session, limit=1000)
    is_admin = (user.Kullanici_Adi and user.Kullanici_Adi.lower() == 'admin')
    if not is_admin:
        roles = auth_queries.get_user_roles(db_session, user.Kullanici_ID)
        is_admin = 'admin' in [r.lower() for r in roles]

    auth_suber = all_suber if is_admin else [
        s for s in all_suber
        if s.Sube_ID in auth_queries.get_user_branches(db_session, user.Kullanici_ID)
    ]
    subeler_list = [{"Sube_ID": s.Sube_ID, "Sube_Adi": s.Sube_Adi} for s in auth_suber]

    # Get data needed for dropdowns and display
    atamalar = queries.get_kullanici_rolleri(db_session, limit=1000)
    kullanicilar = db_session.query(queries.Kullanici).filter(queries.Kullanici.Aktif_Pasif == True).all()
    roller = queries.get_roller(db_session, limit=1000, aktif_only=True)

    atamalar_list = []
    for a in atamalar:
        atamalar_list.append({
            "Kullanici_ID": a.Kullanici_ID,
            "Rol_ID": a.Rol_ID,
            "Sube_ID": a.Sube_ID,
            "Aktif_Pasif": a.Aktif_Pasif,
            "Kullanici_Adi": a.kullanici.Adi_Soyadi if a.kullanici else None,
            "Kullanici_Login": a.kullanici.Kullanici_Adi if a.kullanici else None,
            "Rol_Adi": a.rol.Rol_Adi if a.rol else None,
            "Sube_Adi": a.sube.Sube_Adi if a.sube else None
        })

    kullanicilar_list = [{"Kullanici_ID": k.Kullanici_ID, "Adi_Soyadi": k.Adi_Soyadi, "Kullanici_Adi": k.Kullanici_Adi} for k in kullanicilar]
    roller_list = [{"Rol_ID": r.Rol_ID, "Rol_Adi": r.Rol_Adi} for r in roller]

    db_session.close()

    return render_template(
        "kullanici_rol_atamalari.html",
        user=user,
        subeler=subeler_list,
        atamalar=atamalar_list,
        kullanicilar=kullanicilar_list,
        roller=roller_list
    )


@web_reference_bp.route("/rol-yetki-atamalari", methods=["GET"])
@login_required
@permission_required("Rol Yetki Atama Ekranı Görüntüleme")
def rol_yetki_atamalari():
    """
    Rol Yetki Atamalari page.
    Shows the list of role-permission assignments.
    """
    db_session = get_db_session()

    # Get current user
    user = auth_queries.get_kullanici_by_id(db_session, session['user_id'])

    if not user:
        db_session.close()
        return redirect(url_for('web_auth.login'))

    # Get all branches for topbar dropdown
    all_suber = queries.get_suber(db_session, limit=1000)
    is_admin = (user.Kullanici_Adi and user.Kullanici_Adi.lower() == 'admin')
    if not is_admin:
        roles = auth_queries.get_user_roles(db_session, user.Kullanici_ID)
        is_admin = 'admin' in [r.lower() for r in roles]

    auth_suber = all_suber if is_admin else [
        s for s in all_suber
        if s.Sube_ID in auth_queries.get_user_branches(db_session, user.Kullanici_ID)
    ]
    subeler_list = [{"Sube_ID": s.Sube_ID, "Sube_Adi": s.Sube_Adi} for s in auth_suber]

    # Get data needed for dropdowns and display
    atamalar = queries.get_rol_yetkileri(db_session, limit=1000)
    roller = queries.get_roller(db_session, limit=1000, aktif_only=True)
    yetkiler = queries.get_yetkiler(db_session, limit=1000, aktif_only=True)

    atamalar_list = []
    for a in atamalar:
        atamalar_list.append({
            "Rol_ID": a.Rol_ID,
            "Yetki_ID": a.Yetki_ID,
            "Aktif_Pasif": a.Aktif_Pasif,
            "Rol_Adi": a.rol.Rol_Adi if a.rol else None,
            "Yetki_Adi": a.yetki.Yetki_Adi if a.yetki else None,
            "Tip": a.yetki.Tip if a.yetki else None
        })

    roller_list = [{"Rol_ID": r.Rol_ID, "Rol_Adi": r.Rol_Adi} for r in roller]
    yetkiler_list = [{"Yetki_ID": y.Yetki_ID, "Yetki_Adi": y.Yetki_Adi, "Tip": y.Tip} for y in yetkiler]

    db_session.close()

    return render_template(
        "rol_yetki_atamalari.html",
        user=user,
        subeler=subeler_list,
        atamalar=atamalar_list,
        roller=roller_list,
        yetkiler=yetkiler_list
    )


@web_reference_bp.route("/efatura-referans-yonetimi", methods=["GET"])
@login_required
@permission_required("e-Fatura Referans Yönetimi Ekranı Görüntüleme")
def efatura_referans_yonetimi():
    """
    e-Fatura Referans Yönetimi page.
    """
    db_session = get_db_session()
    user = auth_queries.get_kullanici_by_id(db_session, session['user_id'])
    
    if not user:
        db_session.close()
        return redirect(url_for('web_auth.login'))
        
    all_suber = queries.get_suber(db_session, limit=1000)
    is_admin = (user.Kullanici_Adi and user.Kullanici_Adi.lower() == 'admin')
    if not is_admin:
        roles = auth_queries.get_user_roles(db_session, user.Kullanici_ID)
        is_admin = 'admin' in [r.lower() for r in roles]

    auth_suber = all_suber if is_admin else [
        s for s in all_suber if s.Sube_ID in auth_queries.get_user_branches(db_session, user.Kullanici_ID)
    ]
    
    # Needs categorization list for referans creation
    can_view_gizli = is_admin or auth_queries.has_permission(db_session, user.Kullanici_ID, "Gizli Kategori Veri Erişimi")
    kategoriler = queries.get_kategoriler(db_session, limit=1000, can_view_gizli=can_view_gizli)
    kategoriler_list = [{"Kategori_ID": k.Kategori_ID, "Kategori_Adi": k.Kategori_Adi} for k in kategoriler]
    
    referanslar = queries.get_efatura_referanslar(db_session, limit=5000)
    referanslar_list = [
        {
            "Alici_Unvani": r.Alici_Unvani,
            "Referans_Kodu": r.Referans_Kodu,
            "Kategori_ID": r.Kategori_ID,
            "Kategori_Adi": r.kategori.Kategori_Adi if r.kategori else "Belirsiz",
            "Aciklama": r.Aciklama,
            "Aktif_Pasif": r.Aktif_Pasif
        } for r in referanslar
    ]
    
    db_session.close()
    
    return render_template(
        "efatura_referans_yonetimi.html",
        user=user,
        subeler=auth_suber,
        kategoriler=kategoriler_list,
        referanslar=referanslar_list
    )


@web_reference_bp.route("/odeme-referans-yonetimi", methods=["GET"])
@login_required
@permission_required("Ödeme Referans Yönetimi Ekran Görüntüleme")
def odeme_referans_yonetimi():
    """
    Ödeme Referans Yönetimi page.
    """
    db_session = get_db_session()
    user = auth_queries.get_kullanici_by_id(db_session, session['user_id'])
    
    if not user:
        db_session.close()
        return redirect(url_for('web_auth.login'))
        
    all_suber = queries.get_suber(db_session, limit=1000)
    is_admin = (user.Kullanici_Adi and user.Kullanici_Adi.lower() == 'admin')
    if not is_admin:
        roles = auth_queries.get_user_roles(db_session, user.Kullanici_ID)
        is_admin = 'admin' in [r.lower() for r in roles]

    auth_suber = all_suber if is_admin else [
        s for s in all_suber if s.Sube_ID in auth_queries.get_user_branches(db_session, user.Kullanici_ID)
    ]
    
    # Categories needed for adding/editing references
    can_view_gizli = is_admin or auth_queries.has_permission(db_session, user.Kullanici_ID, "Gizli Kategori Veri Erişimi")
    kategoriler = queries.get_kategoriler(db_session, limit=1000, can_view_gizli=can_view_gizli)
    kategoriler_list = [{"Kategori_ID": k.Kategori_ID, "Kategori_Adi": k.Kategori_Adi} for k in kategoriler]
    
    referanslar = queries.get_odeme_referanslar(db_session, limit=5000)
    referanslar_list = [
        {
            "Referans_ID": r.Referans_ID,
            "Referans_Metin": r.Referans_Metin,
            "Kategori_ID": r.Kategori_ID,
            "Kategori_Adi": r.kategori.Kategori_Adi if r.kategori else "Belirsiz",
            "Aktif_Pasif": r.Aktif_Pasif
        } for r in referanslar
    ]
    
    db_session.close()
    
    return render_template(
        "odeme_referans_yonetimi.html",
        user=user,
        subeler=auth_suber,
        kategoriler=kategoriler_list,
        referanslar=referanslar_list
    )
@web_reference_bp.route("/cari-borc-yonetimi", methods=["GET"])
@login_required
@permission_required("Cari Borç Yönetimi Ekranı Görüntüleme")
def cari_borc_yonetimi():
    """
    Cari Borç Yönetimi page.
    """
    db_session = get_db_session()
    user = auth_queries.get_kullanici_by_id(db_session, session['user_id'])
    
    if not user:
        db_session.close()
        return redirect(url_for('web_auth.login'))
        
    all_suber = queries.get_suber(db_session, limit=1000)
    is_admin = (user.Kullanici_Adi and user.Kullanici_Adi.lower() == 'admin')
    if not is_admin:
        roles = auth_queries.get_user_roles(db_session, user.Kullanici_ID)
        is_admin = 'admin' in [r.lower() for r in roles]

    auth_suber = all_suber if is_admin else [
        s for s in all_suber if s.Sube_ID in auth_queries.get_user_branches(db_session, user.Kullanici_ID)
    ]
    
    # Categories needed for adding/editing cariler
    can_view_gizli = is_admin or auth_queries.has_permission(db_session, user.Kullanici_ID, "Gizli Kategori Veri Erişimi")
    kategoriler = queries.get_kategoriler(db_session, limit=1000, can_view_gizli=can_view_gizli)
    kategoriler_list = [{"Kategori_ID": k.Kategori_ID, "Kategori_Adi": k.Kategori_Adi} for k in kategoriler]
    
    # Odeme Referanslar needed for dropdown
    odeme_referanslar = queries.get_odeme_referanslar(db_session, limit=1000)
    odeme_referanslar_list = [
        {
            "Referans_ID": r.Referans_ID, 
            "Referans_Metin": r.Referans_Metin,
            "Kategori_Adi": r.kategori.Kategori_Adi if r.kategori else "Belirsiz"
        } 
        for r in odeme_referanslar
    ]
    
    cariler = queries.get_cariler(db_session, limit=5000)
    cariler_list = [
        {
            "Cari_ID": c.Cari_ID,
            "Alici_Unvani": c.Alici_Unvani,
            "e_Fatura_Kategori_ID": c.e_Fatura_Kategori_ID,
            "Referans_ID": c.Referans_ID,
            "Referans_Detay": (
                f"#{c.referans.Referans_ID} ({c.referans.Referans_Metin} - {c.referans.kategori.Kategori_Adi})"
                if c.referans else "-"
            ),
            "Cari": c.Cari,
            "Aciklama": c.Aciklama,
            "Aktif_Pasif": c.Aktif_Pasif
        } for c in cariler
    ]
    
    db_session.close()
    
    return render_template(
        "cari_yonetimi.html",
        user=user,
        subeler=auth_suber,
        kategoriler=kategoriler_list,
        odeme_referanslar=odeme_referanslar_list,
        cariler=cariler_list
    )


@web_reference_bp.route("/ust-kategori-yonetimi", methods=["GET"])
@login_required
@permission_required("Üst Kategori Yönetimi Ekranı Görüntüleme")
def ust_kategori_yonetimi():
    """
    Üst Kategori Yönetimi page.
    """
    db_session = get_db_session()
    user = auth_queries.get_kullanici_by_id(db_session, session['user_id'])
    
    if not user:
        db_session.close()
        return redirect(url_for('web_auth.login'))
        
    all_suber = queries.get_suber(db_session, limit=1000)
    is_admin = (user.Kullanici_Adi and user.Kullanici_Adi.lower() == 'admin')
    if not is_admin:
        roles = auth_queries.get_user_roles(db_session, user.Kullanici_ID)
        is_admin = 'admin' in [r.lower() for r in roles]

    auth_suber = all_suber if is_admin else [
        s for s in all_suber if s.Sube_ID in auth_queries.get_user_branches(db_session, user.Kullanici_ID)
    ]
    
    ust_kategoriler = queries.get_ust_kategoriler(db_session, limit=1000)
    ust_kategoriler_list = [
        {
            "UstKategori_ID": uk.UstKategori_ID,
            "UstKategori_Adi": uk.UstKategori_Adi,
            "Aktif_Pasif": uk.Aktif_Pasif
        } for uk in ust_kategoriler
    ]
    
    db_session.close()
    
    return render_template(
        "ust_kategori_yonetimi.html",
        user=user,
        subeler=auth_suber,
        ust_kategoriler=ust_kategoriler_list
    )


@web_reference_bp.route("/kategori-yonetimi", methods=["GET"])
@login_required
@permission_required("Kategori Yönetimi Ekranı Görüntüleme")
def kategori_yonetimi():
    """
    Kategori Yönetimi page.
    """
    db_session = get_db_session()
    user = auth_queries.get_kullanici_by_id(db_session, session['user_id'])
    
    if not user:
        db_session.close()
        return redirect(url_for('web_auth.login'))
        
    all_suber = queries.get_suber(db_session, limit=1000)
    is_admin = (user.Kullanici_Adi and user.Kullanici_Adi.lower() == 'admin')
    if not is_admin:
        roles = auth_queries.get_user_roles(db_session, user.Kullanici_ID)
        is_admin = 'admin' in [r.lower() for r in roles]

    auth_suber = all_suber if is_admin else [
        s for s in all_suber if s.Sube_ID in auth_queries.get_user_branches(db_session, user.Kullanici_ID)
    ]
    
    # Categories with joined UstKategori for the table
    can_view_gizli = is_admin or auth_queries.has_permission(db_session, user.Kullanici_ID, "Gizli Kategori Veri Erişimi")
    kategoriler = queries.get_kategoriler(db_session, limit=1000, aktif_only=False, can_view_gizli=can_view_gizli)
    kategoriler_list = [
        {
            "Kategori_ID": k.Kategori_ID,
            "Kategori_Adi": k.Kategori_Adi,
            "Ust_Kategori_ID": k.Ust_Kategori_ID,
            "UstKategori_Adi": k.ust_kategori.UstKategori_Adi if k.ust_kategori else "-",
            "Tip": k.Tip,
            "Aktif_Pasif": k.Aktif_Pasif,
            "Gizli": k.Gizli
        } for k in kategoriler
    ]
    
    # Upper categories for the dropdowns
    ust_kategoriler = queries.get_ust_kategoriler(db_session, limit=1000)
    ust_kategoriler_list = [
        {
            "UstKategori_ID": uk.UstKategori_ID,
            "UstKategori_Adi": uk.UstKategori_Adi
        } for uk in ust_kategoriler
    ]
    
    db_session.close()
    
    return render_template(
        "kategori_yonetimi.html",
        user=user,
        subeler=auth_suber,
        kategoriler=kategoriler_list,
        ust_kategoriler=ust_kategoriler_list
    )
