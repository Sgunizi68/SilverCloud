from app import create_app
from app.models.models import Yetki, RolYetki
from app.common.database import db

app = create_app()
with app.app_context():
    print("Listing permissions like 'Ödeme Referans'...")
    results = db.session.query(Yetki).filter(Yetki.Yetki_Adi.like('%Ödeme Referans%')).all()
    for y in results:
        print(f"ID: {y.Yetki_ID}, Name: '{y.Yetki_Adi}'")

    # The user says ID 38 is the correct one.
    # Name from screenshot: "Ödeme Referans Yönetimi Ekran Görüntüleme"
    # Name I created: "Ödeme Referans Yönetimi Ekranı Görüntüleme"
    
    correct_id = 38
    wrong_name = "Ödeme Referans Yönetimi Ekranı Görüntüleme"
    
    wrong_perms = db.session.query(Yetki).filter(Yetki.Yetki_Adi == wrong_name).all()
    
    for wp in wrong_perms:
        if wp.Yetki_ID == correct_id:
            print(f"Warning: ID 38 has the wrong name! Updating name of ID 38...")
            wp.Yetki_Adi = "Ödeme Referans Yönetimi Ekran Görüntüleme"
            db.session.commit()
            print("Updated ID 38 name.")
        else:
            print(f"Deleting wrong permission ID: {wp.Yetki_ID} ('{wp.Yetki_Adi}')...")
            # Before deleting, migrate any RolYetki to ID 38
            ry_list = db.session.query(RolYetki).filter_by(Yetki_ID=wp.Yetki_ID).all()
            for ry in ry_list:
                # Check if it already exists for ID 38
                exists = db.session.query(RolYetki).filter_by(Rol_ID=ry.Rol_ID, Yetki_ID=correct_id).first()
                if not exists:
                    print(f"Migrating RolYetki for role {ry.Rol_ID} to ID {correct_id}")
                    ry.Yetki_ID = correct_id
                else:
                    print(f"RolYetki for role {ry.Rol_ID} already exists for ID {correct_id}. Deleting redundant one...")
                    db.session.delete(ry)
            
            db.session.delete(wp)
            db.session.commit()
            print(f"Deleted ID {wp.Yetki_ID}.")
    
    # Final check on ID 38
    y38 = db.session.get(Yetki, correct_id)
    if y38:
        print(f"Final check: ID {y38.Yetki_ID}, Name: '{y38.Yetki_Adi}'")
    else:
        print(f"ERROR: ID {correct_id} not found!")
