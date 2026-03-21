from app.main import create_main_app
from app.common.database import get_db_session
from app.models import EFatura

def find():
    app = create_main_app()
    with app.app_context():
        db = get_db_session()
        f = db.query(EFatura).first()
        if f:
            print(f"NO:{f.Fatura_Numarasi}")
            print(f"TUTAR:{f.Tutar}")
            print(f"SUBE:{f.Sube_ID}")
        else:
            print("NONE")
        db.close()

if __name__ == "__main__":
    find()
