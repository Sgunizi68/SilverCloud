from app import create_app
from app.models.models import Yetki, Rol, RolYetki, Kullanici
from app.common.database import db

app = create_app()
with app.app_context():
    print("Checking permissions...")
    perm_name = 'Ödeme Referans Yönetimi Ekranı Görüntüleme'
    y = db.session.query(Yetki).filter_by(Yetki_Adi=perm_name).first()
    if not y:
        print(f"Permission '{perm_name}' not found. Adding...")
        y = Yetki(Yetki_Adi=perm_name, Aktif_Pasif=True)
        db.session.add(y)
        db.session.commit()
        print("Permission added.")
    else:
        print(f"Permission '{perm_name}' already exists.")

    admin_role = db.session.query(Rol).filter(Rol.Rol_Adi.ilike('admin')).first()
    if admin_role:
        print(f"Found admin role: {admin_role.Rol_Adi}")
        ry = db.session.query(RolYetki).filter_by(Rol_ID=admin_role.Rol_ID, Yetki_ID=y.Yetki_ID).first()
        if not ry:
            print("Assigning permission to Admin role...")
            ry = RolYetki(Rol_ID=admin_role.Rol_ID, Yetki_ID=y.Yetki_ID, Aktif_Pasif=True)
            db.session.add(ry)
            db.session.commit()
            print("Permission assigned.")
        else:
            print("Permission already assigned to Admin role.")
    else:
        print("Admin role not found.")
    
    # Check if 'Sgunizi' user has admin role
    user = db.session.query(Kullanici).filter(Kullanici.Kullanici_Adi.ilike('Sgunizi')).first()
    if user:
        print(f"User Sgunizi found. ID: {user.Kullanici_ID}")
        from app.models.models import KullaniciRol
        kr = db.session.query(KullaniciRol).filter_by(Kullanici_ID=user.Kullanici_ID, Rol_ID=admin_role.Rol_ID if admin_role else -1).first()
        if kr:
            print("User Sgunizi has Admin role.")
        else:
            print("User Sgunizi does NOT have Admin role. Assigning...")
            if admin_role:
                # Need a Sube_ID for KullaniciRol
                from app.models.models import Sube
                first_sube = db.session.query(Sube).first()
                if first_sube:
                    kr = KullaniciRol(Kullanici_ID=user.Kullanici_ID, Rol_ID=admin_role.Rol_ID, Sube_ID=first_sube.Sube_ID, Aktif_Pasif=True)
                    db.session.add(kr)
                    db.session.commit()
                    print(f"Assigned Admin role to Sgunizi for sube {first_sube.Sube_Adi}")
    else:
        print("User Sgunizi not found.")
