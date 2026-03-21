from app.main import create_main_app
from app.common.database import get_db_session
from app.modules.invoicing import queries
from app.models import EFatura

def test():
    app = create_main_app()
    with app.app_context():
        db = get_db_session()
        print("Testing CREATE...")
        try:
            # Try to create -3
            new_f = queries.create_efatura(
                db, sube_id=1, kategori_id=15, 
                fatura_no="SH12025000509175-3", 
                fatura_tutari=100.0,
                donem=2507
            )
            print(f"CREATED ID: {new_f.Fatura_ID}")
            
            print("Testing DELETE...")
            success = queries.delete_efatura(db, new_f.Fatura_ID)
            print(f"DELETED: {success}")
            
        except Exception as e:
            print(f"ERROR: {e}")
            import traceback
            traceback.print_exc()
        db.close()

if __name__ == "__main__":
    test()
