from app.main import create_main_app
from app.common.database import get_db_session
from app.models import EFatura

def debug():
    app = create_main_app()
    with app.app_context():
        db = get_db_session()
        res = db.query(EFatura).filter(EFatura.Fatura_Numarasi.like('SH12025000509175%')).all()
        for r in res:
            print(f"ID:{r.Fatura_ID}, No:{r.Fatura_Numarasi}, Tutar:{r.Tutar}, Kat:{r.Kategori_ID}, Sube:{r.Sube_ID}, Donem:{r.Donem}")
        db.close()

if __name__ == "__main__":
    debug()
