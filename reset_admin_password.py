import sys
sys.path.insert(0, r'c:\projects\SilverCloud')

from app.main import create_main_app
from app.common.database import get_db_session

app = create_main_app()

with app.app_context():
    from app.models import Kullanici
    from app.modules.auth.security import get_password_hash
    from sqlalchemy import select

    db = get_db_session()
    
    # 1. Get Admin user
    stmt = select(Kullanici).where(Kullanici.Kullanici_Adi == 'Admin')
    admin_user = db.scalars(stmt).first()
    
    if admin_user:
        print(f"Current Admin hash: {admin_user.Password}")
        # Generate new hash for 'Adm123!'
        new_hash = get_password_hash('Adm123!')
        print(f"New Admin hash for 'Adm123!': {new_hash}")
        
        # Update user
        admin_user.Password = new_hash
        db.commit()
        print("Admin password successfully reset to 'Adm123!'")
    else:
        print("Admin user not found!")

    db.close()
